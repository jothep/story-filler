"""Verify documentation-only detection with real Git changes and invalid inputs."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from check_docs_only import DocsOnlyError, check_docs_only

SCRIPT = Path(__file__).with_name("check_docs_only.py").resolve()


class DocsOnlyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="docs-only-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.event = self.root / "event.json"
        self.output = self.root / "output"
        self.git("init", "--quiet", "--initial-branch=main")
        for name in ("README.md", "docs/guide.md", "backend/app.py"):
            self.write_file(name, "original\n")
        self.base = self.commit()
        self.write_event(self.base)

    def git(self, *arguments):
        return (
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Docs Check Test",
                    "-c",
                    "user.email=docs@example.test",
                    "-c",
                    "commit.gpgsign=false",
                    *arguments,
                ],
                cwd=self.repo,
                capture_output=True,
                check=True,
            )
            .stdout.decode()
            .strip()
        )

    def write_file(self, name, text="changed\n"):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "-m", "Synthetic change")
        return self.git("rev-parse", "HEAD")

    def write_event(self, head, base=None):
        self.event.write_text(
            json.dumps(
                {
                    "pull_request": {
                        "base": {"sha": base or self.base},
                        "head": {"sha": head},
                    }
                }
            ),
            encoding="utf-8",
        )

    def run_cli(
        self, event_name="pull_request", event_path=None, output_path=None, unset=()
    ):
        environment = os.environ | {
            "GITHUB_EVENT_NAME": event_name,
            "GITHUB_EVENT_PATH": str(event_path or self.event),
            "GITHUB_OUTPUT": str(output_path or self.output),
        }
        for name in unset:
            environment.pop(name, None)
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=self.repo,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def assert_result(self, expected):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.output.read_text(), f"docs_only={str(expected).lower()}\n"
        )
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertNotIn("README.md", result.stdout)
        self.output.unlink()

    def test_root_and_nested_docs_markdown_changes_pass(self):
        self.write_file("README.md")
        self.write_file("CHANGELOG.md")
        self.write_file("docs/guide.md")
        self.write_file("docs/nested/guide.md")
        self.write_event(self.commit())
        self.assert_result(True)

    def test_code_other_directory_markdown_and_non_markdown_docs_do_not_pass(self):
        for name in (
            "backend/app.py",
            "backend/README.md",
            "docs/image.svg",
            ".github/workflows/check.yml",
            "docs/sub/example.py",
            "OTHER.MD",
        ):
            with self.subTest(name=name):
                self.git("reset", "--hard", self.base)
                self.write_file("README.md")
                self.write_file(name)
                self.write_event(self.commit())
                self.assert_result(False)

    def test_empty_diff_is_not_documentation_only(self):
        self.write_event(self.commit())
        self.assert_result(False)

    def test_deleted_document_is_allowed_but_deleted_code_is_not(self):
        (self.repo / "docs/guide.md").unlink()
        self.write_event(self.commit())
        self.assert_result(True)
        self.git("reset", "--hard", self.base)
        (self.repo / "backend/app.py").unlink()
        self.write_event(self.commit())
        self.assert_result(False)

    def test_code_renamed_into_docs_still_includes_its_old_path(self):
        self.git("mv", "backend/app.py", "docs/app.md")
        self.write_event(self.commit())
        self.assert_result(False)

    def test_document_rename_remains_documentation_only(self):
        self.git("mv", "docs/guide.md", "docs/renamed.md")
        self.write_event(self.commit())
        self.assert_result(True)

    def test_merge_base_diff_ignores_changes_only_on_base_branch(self):
        self.git("switch", "--quiet", "--create", "feature")
        self.write_file("docs/guide.md")
        head = self.commit()
        self.git("switch", "--quiet", "main")
        self.write_file("backend/app.py")
        advanced_base = self.commit()
        self.write_event(head, base=advanced_base)
        self.assert_result(True)

    def test_nul_delimiters_preserve_newlines_in_filenames_without_logging_them(self):
        name = "docs/private\n::error::forged.md"
        self.write_file(name)
        self.write_event(self.commit())
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), "docs_only=true\n")
        self.assertNotIn("private", result.stdout + result.stderr)
        self.assertNotIn("forged", result.stdout + result.stderr)

    def test_non_pull_request_events_read_neither_event_file_nor_git(self):
        with patch("check_docs_only.pull_request_commits") as metadata:
            with patch("check_docs_only.subprocess.run") as git:
                for event in (
                    "push",
                    "schedule",
                    "workflow_dispatch",
                    "pull_request_target",
                    None,
                ):
                    self.assertEqual(
                        check_docs_only(event, "/missing/event"), (False, 0)
                    )
                metadata.assert_not_called()
                git.assert_not_called()
        result = self.run_cli("push", event_path=self.root / "missing")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), "docs_only=false\n")

    def test_malformed_or_missing_metadata_fails_without_git_or_output(self):
        invalid = [
            None,
            [],
            {},
            {"pull_request": None},
            {"pull_request": {}},
            {"pull_request": {"base": {"sha": self.base}}},
        ]
        for sha in (
            None,
            1,
            [],
            "HEAD",
            "--help",
            "a" * 39,
            "z" * 40,
            self.base + "\n",
            "$(touch marker)",
        ):
            invalid.append(
                {"pull_request": {"base": {"sha": self.base}, "head": {"sha": sha}}}
            )
            invalid.append(
                {"pull_request": {"base": {"sha": sha}, "head": {"sha": self.base}}}
            )
        with patch("check_docs_only.subprocess.run") as git:
            for value in invalid:
                with self.subTest(value=value):
                    self.event.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(DocsOnlyError):
                        check_docs_only("pull_request", self.event)
            git.assert_not_called()
        self.event.unlink()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_json_and_duplicate_metadata_fail(self):
        for content in (
            "{",
            '{"pull_request":null,"pull_request":{}}',
            '{"value":NaN}',
        ):
            self.event.write_text(content, encoding="utf-8")
            result = self.run_cli()
            self.assertEqual(result.returncode, 1)
            self.assertFalse(self.output.exists())
        self.event.write_bytes(b"\xff")
        self.assertEqual(self.run_cli().returncode, 1)

    def test_required_event_or_output_environment_values_cannot_be_omitted(self):
        for name in ("GITHUB_EVENT_PATH", "GITHUB_OUTPUT"):
            with self.subTest(name=name):
                result = self.run_cli(unset=(name,))
                self.assertEqual(result.returncode, 1)
                self.assertFalse(self.output.exists())
                self.assertNotIn("Traceback", result.stderr)

    def test_unavailable_commit_or_git_failure_cannot_claim_docs_only(self):
        self.write_event("1" * 40)
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())
        self.assertNotIn("fatal:", result.stderr)
        self.assertNotIn("1" * 40, result.stderr)

    def test_incomplete_or_invalid_nul_output_fails(self):
        for output in (
            b"README.md",
            b"README.md\0docs/guide.md",
            b"README.md\0\0",
            b"docs/../app.md\0",
        ):
            with self.subTest(output=output):
                response = subprocess.CompletedProcess([], 0, stdout=output, stderr=b"")
                with patch("check_docs_only.subprocess.run", return_value=response):
                    with self.assertRaises(DocsOnlyError):
                        check_docs_only("pull_request", self.event)

    def test_git_timeout_and_missing_executable_fail(self):
        for error in (
            OSError("private diagnostic"),
            subprocess.TimeoutExpired("git", 30),
        ):
            with patch("check_docs_only.subprocess.run", side_effect=error):
                with self.assertRaises(DocsOnlyError):
                    check_docs_only("pull_request", self.event)

    def test_output_is_appended_and_output_write_failure_is_safe(self):
        self.output.write_text("previous=value\n", encoding="utf-8")
        result = self.run_cli("push")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), "previous=value\ndocs_only=false\n")
        result = self.run_cli("push", output_path=self.root / "missing" / "private")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("private", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
