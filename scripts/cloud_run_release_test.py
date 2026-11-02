"""Exercise release ordering with real Git history and a fake read-only gcloud."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).with_name("cloud_run_release.py").resolve()
REPOSITORY = "region-docker.pkg.dev/example/project/backend"
OLD_IMAGE = REPOSITORY + "@sha256:" + "1" * 64
NEW_IMAGE = REPOSITORY + "@sha256:" + "2" * 64
REVISION = "example-backend-r1"


class CloudRunReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix="release-order-")
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)
        self.git("init", "--quiet", "--initial-branch=main")
        self.first = self.commit("First release")
        self.second = self.commit("Second release")
        self.docs = self.commit("Documentation after the second release")
        self.git("update-ref", "refs/remotes/origin/main", self.docs)
        self.service = {
            "spec": {"traffic": [{"latestRevision": True, "percent": 100}]},
            "status": {
                "traffic": [{"revisionName": REVISION, "percent": 100}],
                "url": "https://example-backend.run.app",
            },
        }
        self.revision = {
            "metadata": {"labels": {"source_commit": self.first}},
            "spec": {"containers": [{"image": OLD_IMAGE}]},
            "status": {"imageDigest": OLD_IMAGE},
        }
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        fake_gcloud = self.bin_dir / "gcloud"
        fake_gcloud.write_text(f"#!{sys.executable}\n" + """
import json
import os
from pathlib import Path
import sys

root = Path(os.environ['FAKE_CLOUD_ROOT'])
args = sys.argv[1:]
with (root / 'cloud-calls.jsonl').open('a') as calls:
    calls.write(json.dumps(args) + '\\n')
expected = {
    'services': 'spec.traffic,status.traffic,status.url',
    'revisions': (
        'metadata.labels.source_commit,spec.containers[0].image,status.imageDigest'
    ),
}
if (len(args) != 7 or args[0] != 'run'
        or args[1] not in expected or args[2] != 'describe'):
    raise SystemExit('Only the expected read-only commands are available in this test.')
if args[-1] != '--format=json(' + expected[args[1]] + ')':
    raise SystemExit('A release check tried to read an unapproved projection.')
if os.environ.get('FAKE_CLOUD_FAIL'):
    print('private-cli-diagnostic-must-not-be-displayed', file=sys.stderr)
    raise SystemExit(1)
print((root / (args[1] + '.json')).read_text())
""")
        fake_gcloud.chmod(0o755)

    def git(self, *arguments):
        result = subprocess.run(
            [
                "git",
                "-c",
                "user.name=Release Test",
                "-c",
                "user.email=release@example.test",
                "-c",
                "commit.gpgsign=false",
                *arguments,
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def commit(self, message):
        self.git("commit", "--quiet", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def check_release(
        self,
        candidate=None,
        image=NEW_IMAGE,
        operation="plan",
        extra_args=(),
        cloud_fails=False,
    ):
        (self.root / "services.json").write_text(json.dumps(self.service))
        (self.root / "revisions.json").write_text(json.dumps(self.revision))
        environment = dict(os.environ)
        environment.update(
            {
                "PATH": str(self.bin_dir) + os.pathsep + os.environ.get("PATH", ""),
                "FAKE_CLOUD_ROOT": str(self.root),
            }
        )
        environment.pop("FAKE_CLOUD_FAIL", None)
        if cloud_fails:
            environment["FAKE_CLOUD_FAIL"] = "1"
        return subprocess.run(
            [
                sys.executable,
                str(HELPER),
                operation,
                "--service",
                "example-backend",
                "--project",
                "example",
                "--region",
                "region",
                "--repository",
                REPOSITORY,
                "--candidate",
                candidate or self.second,
                "--image",
                image,
                *extra_args,
            ],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def assert_rejected(self, result, reason):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn(reason, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_newer_release_survives_later_documentation_commit(self):
        result = self.check_release()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "deploy=true\ndecision=deploy\n")

    def test_slow_old_build_cannot_replace_newer_serving_commit(self):
        self.revision["metadata"]["labels"]["source_commit"] = self.second
        result = self.check_release(candidate=self.first)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "deploy=false\ndecision=superseded\n")

    def test_same_commit_and_digest_are_idempotent(self):
        result = self.check_release(candidate=self.first, image=OLD_IMAGE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "deploy=false\ndecision=unchanged\n")

    def test_same_commit_with_different_digest_is_not_silently_replaced(self):
        self.assert_rejected(
            self.check_release(candidate=self.first), "different digest"
        )

    def test_legacy_full_commit_tag_can_identify_the_current_release(self):
        self.revision.pop("metadata")
        self.revision["spec"]["containers"][0]["image"] = REPOSITORY + ":" + self.first
        self.assertEqual(self.check_release().returncode, 0)

    def test_bare_status_digest_is_normalized_after_repository_validation(self):
        self.revision["status"]["imageDigest"] = "sha256:" + "1" * 64
        for reference in (OLD_IMAGE, REPOSITORY + ":" + self.first):
            with self.subTest(reference=reference):
                self.revision["spec"]["containers"][0]["image"] = reference
                result = self.check_release(
                    candidate=self.first,
                    image=OLD_IMAGE,
                    operation="verify",
                    extra_args=("--expected-revision", REVISION),
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_resolved_digest_cannot_name_another_repository(self):
        self.revision["status"]["imageDigest"] = (
            "other.example/backend@sha256:" + "1" * 64
        )
        self.assert_rejected(self.check_release(), "expected repository")

    def test_bare_digest_does_not_make_an_untrusted_image_reference_valid(self):
        self.revision["status"]["imageDigest"] = "sha256:" + "1" * 64
        self.revision["spec"]["containers"][0]["image"] = (
            "other.example/backend:" + self.first
        )
        self.assert_rejected(self.check_release(), "image reference")

    def test_status_digest_must_match_the_digest_image_reference(self):
        self.revision["status"]["imageDigest"] = "sha256:" + "2" * 64
        self.assert_rejected(self.check_release(), "does not match its resolved digest")

    def test_unknown_commit_is_rejected(self):
        self.revision["metadata"]["labels"]["source_commit"] = "f" * 40
        self.assert_rejected(self.check_release(), "absent")

    def test_non_main_candidate_is_rejected(self):
        self.git("checkout", "--quiet", "-b", "side", self.first)
        side = self.commit("Unmerged release")
        self.assert_rejected(self.check_release(candidate=side), "main history")

    def test_divergent_commits_remain_rejected_even_after_both_are_merged(self):
        self.git("checkout", "--quiet", "-b", "side", self.first)
        side = self.commit("Side release")
        self.git("checkout", "--quiet", "main")
        self.git("merge", "--quiet", "--no-ff", "side", "-m", "Merge the histories")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.revision["metadata"]["labels"]["source_commit"] = side
        self.assert_rejected(self.check_release(), "diverge")

    def test_empty_and_split_traffic_are_rejected(self):
        for traffic in (
            [],
            [
                {"revisionName": REVISION, "percent": 90},
                {"revisionName": "example-backend-r2", "percent": 10},
            ],
        ):
            with self.subTest(traffic=traffic):
                self.service["status"]["traffic"] = traffic
                self.assert_rejected(
                    self.check_release(), "one identified serving revision"
                )

    def test_pinned_or_missing_traffic_policy_is_rejected(self):
        for traffic in ([], [{"revisionName": REVISION, "percent": 100}]):
            with self.subTest(traffic=traffic):
                self.service["spec"]["traffic"] = traffic
                self.assert_rejected(
                    self.check_release(), "latest-revision traffic policy"
                )

    def test_malformed_traffic_does_not_escape_the_error_handler(self):
        self.service["status"]["traffic"] = [None]
        self.assert_rejected(self.check_release(), "one identified serving revision")

    def test_unidentified_image_and_untrusted_repository_are_rejected(self):
        for reference in (
            REPOSITORY + ":latest",
            "other.example/backend:" + self.first,
            None,
        ):
            with self.subTest(reference=reference):
                self.revision["spec"]["containers"][0]["image"] = reference
                self.assert_rejected(self.check_release(), "image reference")

    def test_digest_image_requires_a_commit_label(self):
        self.revision.pop("metadata")
        self.assert_rejected(self.check_release(), "full source commit")

    def test_conflicting_commit_label_and_legacy_tag_are_rejected(self):
        self.revision["spec"]["containers"][0]["image"] = REPOSITORY + ":" + self.second
        self.assert_rejected(self.check_release(), "disagree")

    def test_mutable_candidate_image_is_rejected_before_cloud_access(self):
        self.assert_rejected(
            self.check_release(image=REPOSITORY + ":latest"), "immutable digest"
        )
        self.assertFalse((self.root / "cloud-calls.jsonl").exists())

    def test_cloud_failure_does_not_print_private_diagnostics(self):
        result = self.check_release(cloud_fails=True)
        self.assert_rejected(result, "Could not read")
        self.assertNotIn("private-cli-diagnostic", result.stderr)

    def test_verify_matches_actual_traffic_revision_commit_and_digest(self):
        self.revision["metadata"]["labels"]["source_commit"] = self.second
        self.revision["spec"]["containers"][0]["image"] = NEW_IMAGE
        self.revision["status"]["imageDigest"] = NEW_IMAGE
        result = self.check_release(
            operation="verify", extra_args=("--expected-revision", REVISION)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "service_url=https://example-backend.run.app\n")

    def test_verify_rejects_old_running_image_or_wrong_revision(self):
        result = self.check_release(
            operation="verify", extra_args=("--expected-revision", REVISION)
        )
        self.assert_rejected(result, "does not match")
        result = self.check_release(
            candidate=self.first,
            image=OLD_IMAGE,
            operation="verify",
            extra_args=("--expected-revision", "example-backend-unexpected"),
        )
        self.assert_rejected(result, "does not match")

    def test_verify_requires_the_revision_returned_by_deployment(self):
        self.assert_rejected(
            self.check_release(operation="verify"), "requires the revision"
        )


if __name__ == "__main__":
    unittest.main()
