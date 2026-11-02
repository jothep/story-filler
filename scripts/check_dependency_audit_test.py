"""Exercise audit omissions seen with temporary pip resolver environments."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_dependency_audit import AuditCoverageError, check_coverage

SCRIPT = Path(__file__).with_name("check_dependency_audit.py")
HASH = "--hash=sha256:" + "a" * 64
SECOND_HASH = "--hash=sha256:" + "b" * 64
PACKAGES = {"django": "5.2.14", "packaging": "26.2"}
TOOLS = {"pip": "26.3", "setuptools": "82.0.1", "wheel": "0.46.3"}


class DependencyAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.lock = Path(self.directory.name) / "requirements.txt"
        self.report = Path(self.directory.name) / "audit.json"
        self.write_lock(PACKAGES)
        self.write_report(PACKAGES)

    def write_lock(self, packages):
        self.lock.write_text(
            "# Generated hash lock\n--only-binary :all:\n\n"
            + "".join(
                f"{name}=={version} \\\n    {HASH} \\\n    {SECOND_HASH}\n"
                "    # via -r requirements.in\n"
                for name, version in packages.items()
            ),
            encoding="utf-8",
        )

    def write_report(self, packages):
        self.write_dependencies(
            [
                {"name": name, "version": version, "vulns": []}
                for name, version in packages.items()
            ]
        )

    def write_dependencies(self, dependencies):
        self.report.write_text(
            json.dumps({"dependencies": dependencies, "fixes": []}), encoding="utf-8"
        )

    def test_full_hashed_lock_is_covered(self):
        self.assertEqual(check_coverage(self.lock, self.report), 2)

    def test_preinstalled_packaging_omission_fails(self):
        self.write_report({"django": "5.2.14"})
        with self.assertRaisesRegex(
            AuditCoverageError, "Missing from audit: packaging"
        ):
            check_coverage(self.lock, self.report)

    def test_bootstrap_tool_omissions_fail(self):
        all_packages = PACKAGES | TOOLS
        self.write_lock(all_packages)
        for omitted in TOOLS:
            with self.subTest(omitted=omitted):
                self.write_report(
                    {
                        name: version
                        for name, version in all_packages.items()
                        if name != omitted
                    }
                )
                with self.assertRaisesRegex(
                    AuditCoverageError, f"Missing from audit: {omitted}"
                ):
                    check_coverage(self.lock, self.report)

    def test_bootstrap_tools_are_required_and_accepted_when_reported(self):
        self.write_lock(PACKAGES | TOOLS)
        self.write_report(PACKAGES | TOOLS)
        self.assertEqual(check_coverage(self.lock, self.report), 5)

    def test_extra_resolver_packages_fail(self):
        self.write_report(PACKAGES | {"pip": "26.3"})
        with self.assertRaisesRegex(AuditCoverageError, "Not in lock: pip"):
            check_coverage(self.lock, self.report)

    def test_same_package_at_a_different_version_fails(self):
        self.write_report(PACKAGES | {"packaging": "26.1"})
        with self.assertRaisesRegex(
            AuditCoverageError, "Version mismatch for packaging"
        ):
            check_coverage(self.lock, self.report)

    def test_normalized_names_match_without_hiding_duplicates(self):
        self.write_lock({"Django_Cors.Headers": "4.9.0"})
        self.write_report({"django-cors-headers": "4.9.0"})
        self.assertEqual(check_coverage(self.lock, self.report), 1)
        self.write_report(
            {"django-cors-headers": "4.9.0", "Django_Cors.Headers": "4.9.0"}
        )
        with self.assertRaisesRegex(AuditCoverageError, "Duplicate audited dependency"):
            check_coverage(self.lock, self.report)

    def test_duplicate_lock_names_fail_even_at_the_same_version(self):
        self.write_lock(
            {"Django_Cors.Headers": "4.9.0", "django-cors-headers": "4.9.0"}
        )
        with self.assertRaisesRegex(AuditCoverageError, "Duplicate locked dependency"):
            check_coverage(self.lock, self.report)

    def test_skipped_dependencies_cannot_count_as_coverage(self):
        for reason in ["Dependency could not be audited", "", None]:
            with self.subTest(reason=reason):
                self.write_dependencies(
                    [
                        {
                            "name": "django",
                            "version": "5.2.14",
                            "vulns": [],
                            "skip_reason": reason,
                        }
                    ]
                )
                with self.assertRaisesRegex(
                    AuditCoverageError, "Audit skipped dependency: django"
                ):
                    check_coverage(self.lock, self.report)

    def test_dependency_without_audit_results_fails(self):
        self.write_dependencies([{"name": "django", "version": "5.2.14"}])
        with self.assertRaisesRegex(
            AuditCoverageError, "Missing vulnerability results"
        ):
            check_coverage(self.lock, self.report)

    def test_findings_are_separate_from_coverage(self):
        self.write_lock({"packaging": "26.1"})
        self.write_dependencies(
            [
                {
                    "name": "packaging",
                    "version": "26.1",
                    "vulns": [{"id": "PYSEC-example"}],
                }
            ]
        )
        self.assertEqual(check_coverage(self.lock, self.report), 1)

    def test_unsupported_lock_syntax_is_never_silently_ignored(self):
        entries = [
            "packaging>=26.2",
            "packaging==26.*",
            "packaging[extra]==26.2",
            'packaging==26.2; python_version >= "3.13"',
            "packaging @ https://example.invalid/package.whl",
            "-r other.txt",
            "--requirement=other.txt",
            "-c constraints.txt",
            "--index-url https://example.invalid/simple",
            "--only-binary packaging",
            "--hash=sha256:" + "a" * 64,
        ]
        for entry in entries:
            with self.subTest(entry=entry):
                self.lock.write_text(f"{entry} {HASH}\n", encoding="utf-8")
                with self.assertRaisesRegex(
                    AuditCoverageError, "Unsupported lock entry"
                ):
                    check_coverage(self.lock, self.report)

    def test_missing_or_invalid_hash_fails(self):
        for suffix in ["", "--hash=sha256:abc", "--hash=md5:" + "a" * 32]:
            with self.subTest(suffix=suffix):
                self.lock.write_text(f"packaging==26.2 {suffix}\n", encoding="utf-8")
                with self.assertRaisesRegex(
                    AuditCoverageError, "Unsupported lock entry"
                ):
                    check_coverage(self.lock, self.report)

    def test_unfinished_continuation_fails(self):
        self.lock.write_text(f"packaging==26.2 {HASH} \\\n", encoding="utf-8")
        with self.assertRaisesRegex(AuditCoverageError, "Unfinished lock continuation"):
            check_coverage(self.lock, self.report)

    def test_empty_lock_fails(self):
        self.lock.write_text(
            "# no dependencies\n--only-binary :all:\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(
            AuditCoverageError, "Lock contains no dependencies"
        ):
            check_coverage(self.lock, self.report)

    def test_equals_option_and_inline_comments_are_supported(self):
        self.lock.write_text(
            f"--only-binary=:all:\npackaging==26.2 {HASH} # pinned\n", encoding="utf-8"
        )
        self.write_report({"packaging": "26.2"})
        self.assertEqual(check_coverage(self.lock, self.report), 1)

    def test_invalid_report_shapes_fail(self):
        for content in [[], {}, {"dependencies": {}}, {"dependencies": [None]}]:
            with self.subTest(content=content):
                self.report.write_text(json.dumps(content), encoding="utf-8")
                with self.assertRaises(AuditCoverageError):
                    check_coverage(self.lock, self.report)

    def test_duplicate_json_keys_fail(self):
        self.report.write_text(
            '{"dependencies": [], "dependencies": []}', encoding="utf-8"
        )
        with self.assertRaisesRegex(AuditCoverageError, "Duplicate JSON key"):
            check_coverage(self.lock, self.report)

    def run_cli(self):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.lock), str(self.report)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def test_cli_reports_coverage_count(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("all 2 locked dependencies", result.stdout)

    def test_cli_fails_clearly_for_missing_or_invalid_input(self):
        for content in ["{", '{"dependencies": []}']:
            with self.subTest(content=content):
                self.report.write_text(content, encoding="utf-8")
                result = self.run_cli()
                self.assertEqual(result.returncode, 1)
                self.assertIn("Audit coverage check failed:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
        self.report.unlink()
        self.assertEqual(self.run_cli().returncode, 1)


if __name__ == "__main__":
    unittest.main()
