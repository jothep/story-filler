"""Exercise fail-closed CodeQL result and analysis-integrity checks."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_codeql_results import CodeQLGateError, check_report

SCRIPT = Path(__file__).with_name("check_codeql_results.py")


def clean_report():
    return {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "CodeQL"}},
                "invocations": [{"executionSuccessful": True}],
                "results": [],
            }
        ],
    }


class CodeQLGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.report_path = self.directory / "python.sarif"
        self.write_report(clean_report())

    def write_report(self, report):
        self.report_path.write_text(json.dumps(report), encoding="utf-8")

    def assert_rejected(self, report):
        self.write_report(report)
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")

    def run_cli(self, language="python"):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--directory",
                str(self.directory),
                "--language",
                language,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def test_zero_results_passes_for_each_supported_language(self):
        self.assertEqual(check_report(self.directory, "python"), 1)
        self.report_path.rename(self.directory / "javascript.sarif")
        self.assertEqual(check_report(self.directory, "javascript"), 1)

    def test_every_result_blocks_even_if_suppressed_unchanged_or_level_none(self):
        variants = [
            {},
            {"level": "none"},
            {"level": "note"},
            {"baselineState": "unchanged"},
            {"baselineState": "absent"},
            {"suppressions": [{"kind": "inSource", "status": "accepted"}]},
            {"suppressions": [{"kind": "external"}]},
        ]
        for metadata in variants:
            with self.subTest(metadata=metadata):
                report = clean_report()
                report["runs"][0]["results"] = [
                    {"ruleId": "py/log-injection", **metadata}
                ]
                self.write_report(report)
                with self.assertRaisesRegex(CodeQLGateError, "Found 1 result"):
                    check_report(self.directory, "python")

    def test_missing_or_invalid_rule_metadata_never_hides_a_result(self):
        for result in ({}, {"ruleIndex": 0}, {"ruleId": None}, {"ruleId": ["id"]}):
            with self.subTest(result=result):
                report = clean_report()
                report["runs"][0]["results"] = [result]
                self.write_report(report)
                with self.assertRaisesRegex(CodeQLGateError, "Found 1 result"):
                    check_report(self.directory, "python")

    def test_all_runs_are_checked_and_all_findings_are_counted(self):
        report = clean_report()
        report["runs"].append(deepcopy(report["runs"][0]))
        report["runs"][1]["results"] = [
            {"ruleId": "py/log-injection"},
            {"ruleId": "py/log-injection"},
            {"ruleId": "py/reflective-xss"},
        ]
        self.write_report(report)
        with self.assertRaisesRegex(
            CodeQLGateError,
            "Found 3 result.*py/log-injection: 2, py/reflective-xss: 1",
        ):
            check_report(self.directory, "python")

    def test_missing_or_non_directory_input_fails(self):
        for path in (self.directory / "missing", self.report_path):
            with self.subTest(path=path):
                with self.assertRaises(CodeQLGateError):
                    check_report(path, "python")

    def test_missing_wrong_language_extra_and_nested_reports_fail(self):
        self.report_path.unlink()
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")
        wrong_report = self.directory / "javascript.sarif"
        wrong_report.write_text(json.dumps(clean_report()), encoding="utf-8")
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")
        self.write_report(clean_report())
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")
        nested = self.directory / "nested"
        nested.mkdir()
        wrong_report.rename(nested / "python.sarif")
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")

    def test_report_must_be_a_regular_file_not_a_directory_or_symlink(self):
        self.report_path.unlink()
        self.report_path.mkdir()
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")
        self.report_path.rmdir()
        target = self.directory / "outside.json"
        target.write_text(json.dumps(clean_report()), encoding="utf-8")
        self.report_path.symlink_to(target)
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")

    def test_invalid_json_duplicate_keys_and_nonstandard_constants_fail(self):
        for content in (
            "{",
            '{"version":"2.1.0","runs":[],"runs":[]}',
            '{"version":"2.1.0","runs":[],"value":NaN}',
            '{"version":"2.1.0","runs":[],"value":Infinity}',
            '{"value":' + "1" * 5000 + "}",
        ):
            with self.subTest(content=content):
                self.report_path.write_text(content, encoding="utf-8")
                with self.assertRaises(CodeQLGateError):
                    check_report(self.directory, "python")
        self.report_path.write_bytes(b"\xff\xfe")
        with self.assertRaises(CodeQLGateError):
            check_report(self.directory, "python")

    def test_wrong_version_missing_empty_or_malformed_runs_fail(self):
        for report in (
            [],
            {},
            {"version": "2.0.0", "runs": clean_report()["runs"]},
            {"version": "2.1.0"},
            {"version": "2.1.0", "runs": []},
            {"version": "2.1.0", "runs": None},
            {"version": "2.1.0", "runs": {}},
            {"version": "2.1.0", "runs": [None]},
        ):
            with self.subTest(report=report):
                self.assert_rejected(report)

    def test_every_run_requires_codeql_tool_and_results_array(self):
        variants = (
            {},
            {"tool": None, "results": []},
            {"tool": {"driver": None}, "results": []},
            {"tool": {"driver": {"name": "Other"}}, "results": []},
            {"tool": {"driver": {"name": "CodeQL"}}},
            {"tool": {"driver": {"name": "CodeQL"}}, "results": None},
            {"tool": {"driver": {"name": "CodeQL"}}, "results": {}},
            {"tool": {"driver": {"name": "CodeQL"}}, "results": [None]},
        )
        for run in variants:
            with self.subTest(run=run):
                report = clean_report()
                report["runs"].append(run)
                self.assert_rejected(report)

    def test_absent_invocation_metadata_is_valid_but_not_required_for_results(self):
        report = clean_report()
        del report["runs"][0]["invocations"]
        self.write_report(report)
        self.assertEqual(check_report(self.directory, "python"), 1)
        report["runs"][0]["results"] = [{}]
        self.assert_rejected(report)

    def test_unsuccessful_missing_or_malformed_invocations_fail(self):
        for invocation in (
            None,
            {},
            {"executionSuccessful": False},
            {"executionSuccessful": None},
            {"executionSuccessful": 1},
            {"executionSuccessful": "true"},
            {"executionSuccessful": True, "exitCode": 1},
            {"executionSuccessful": True, "exitCode": "0"},
            {"executionSuccessful": True, "exitCode": False},
            {"executionSuccessful": True, "processStartFailureMessage": "private"},
            {"executionSuccessful": True, "exitSignalNumber": 9},
        ):
            with self.subTest(invocation=invocation):
                report = clean_report()
                report["runs"][0]["invocations"].append(invocation)
                self.assert_rejected(report)
        for invocations in (None, {}):
            report = clean_report()
            report["runs"][0]["invocations"] = invocations
            self.assert_rejected(report)

    def test_error_and_malformed_analysis_notifications_fail(self):
        for key in ("toolExecutionNotifications", "toolConfigurationNotifications"):
            for notifications in (
                None,
                {},
                [None],
                [{"level": "error", "message": {"text": "private"}}],
                [{"level": "invalid"}],
                [{"level": None}],
            ):
                with self.subTest(key=key, notifications=notifications):
                    report = clean_report()
                    report["runs"][0]["invocations"][0][key] = notifications
                    self.assert_rejected(report)

    def test_non_error_analysis_notifications_do_not_count_as_findings(self):
        report = clean_report()
        report["runs"][0]["invocations"][0]["exitCode"] = 0
        report["runs"][0]["invocations"][0]["toolExecutionNotifications"] = [
            {"level": level, "message": {"text": "synthetic diagnostic"}}
            for level in ("none", "note", "warning")
        ]
        self.write_report(report)
        self.assertEqual(check_report(self.directory, "python"), 1)

    def test_cli_reports_safe_counts_without_source_or_control_characters(self):
        report = clean_report()
        report["runs"][0]["results"] = [
            {"ruleId": "py/log-injection", "message": {"text": "private snippet"}},
            {"ruleId": "unsafe\n::error::forged", "message": {"text": "private"}},
        ]
        self.write_report(report)
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Found 2 result(s)", result.stderr)
        self.assertIn("py/log-injection: 1", result.stderr)
        self.assertIn("<unknown-rule>: 1", result.stderr)
        self.assertEqual(len(result.stderr.splitlines()), 1)
        self.assertNotIn("private", result.stderr)
        self.assertNotIn("forged", result.stderr)
        self.assertNotIn("::error::", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_cli_success_and_malformed_input_have_clear_status_without_traceback(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CodeQL python: 0 results across 1 run(s).", result.stdout)
        for content in ("{", '{"secret\n::error::private": 1}'):
            self.report_path.write_text(content, encoding="utf-8")
            result = self.run_cli()
            self.assertEqual(result.returncode, 1)
            self.assertIn("CodeQL gate failed:", result.stderr)
            self.assertNotIn("private", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        self.report_path.unlink()
        self.assertEqual(self.run_cli().returncode, 1)


if __name__ == "__main__":
    unittest.main()
