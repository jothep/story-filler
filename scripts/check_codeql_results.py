"""Require a valid CodeQL SARIF report with zero results for one CI language.

Run only after a successful official CodeQL analysis, against its fresh output
directory. This gate has no severity threshold, baseline or suppression allowance.
It checks the report, not source coverage or whether the analyzer was executed.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys


class CodeQLGateError(ValueError):
    """The report cannot establish a successful analysis with zero findings."""


def unique_json_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise CodeQLGateError("Report contains a duplicate JSON key")
        value[key] = item
    return value


def reject_json_constant(_value):
    raise CodeQLGateError("Report contains a nonstandard JSON constant")


def check_invocations(run):
    # Invocations are optional SARIF metadata. When supplied, their success flag
    # is mandatory; SARIF Appendix I also identifies error notifications as an
    # indication that the result set may be incomplete.
    invocations = run.get("invocations", [])
    if not isinstance(invocations, list):
        raise CodeQLGateError("Run invocations must be an array")
    for invocation in invocations:
        if not isinstance(invocation, dict):
            raise CodeQLGateError("Invocation must be an object")
        if invocation.get("executionSuccessful") is not True:
            raise CodeQLGateError("Invocation did not report successful execution")
        if "exitCode" in invocation and (
            type(invocation["exitCode"]) is not int or invocation["exitCode"] != 0
        ):
            raise CodeQLGateError("CodeQL invocation reports an invalid or failed exit")
        if any(
            key in invocation
            for key in (
                "processStartFailureMessage",
                "exitSignalNumber",
                "exitSignalName",
            )
        ):
            raise CodeQLGateError("Invocation reports a process failure")
        for key in ("toolExecutionNotifications", "toolConfigurationNotifications"):
            notifications = invocation.get(key, [])
            if not isinstance(notifications, list):
                raise CodeQLGateError("Invocation notifications must be an array")
            for notification in notifications:
                if not isinstance(notification, dict):
                    raise CodeQLGateError("Invocation notification must be an object")
                level = notification.get("level", "warning")
                if level not in ("none", "note", "warning"):
                    raise CodeQLGateError(
                        "Invocation contains an error or invalid level"
                    )


def check_report(directory, language):
    if language not in ("python", "javascript"):
        raise CodeQLGateError("Unsupported analysis language")
    directory = Path(directory)
    report_path = directory / f"{language}.sarif"
    # The official analyzer emits <language>.sarif for code scanning. Reject
    # missing, extra and nested reports rather than silently checking a subset.
    if (
        not directory.is_dir()
        or set(directory.rglob("*.sarif")) != {report_path}
        or not report_path.is_file()
        or report_path.is_symlink()
    ):
        raise CodeQLGateError(f"Expected exactly one regular {language}.sarif report")
    try:
        report = json.loads(
            report_path.read_text(encoding="utf-8"),
            object_pairs_hook=unique_json_object,
            parse_constant=reject_json_constant,
        )
    except CodeQLGateError:
        raise
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise CodeQLGateError("Report could not be read as valid JSON") from error
    if not isinstance(report, dict) or report.get("version") != "2.1.0":
        raise CodeQLGateError("Report must use SARIF version 2.1.0")
    runs = report.get("runs")
    if not isinstance(runs, list) or not runs:
        raise CodeQLGateError("Report must contain a nonempty runs array")
    findings = Counter()
    for run in runs:
        if not isinstance(run, dict):
            raise CodeQLGateError("Run must be an object")
        tool = run.get("tool")
        driver = tool.get("driver") if isinstance(tool, dict) else None
        if not isinstance(driver, dict) or driver.get("name") != "CodeQL":
            raise CodeQLGateError("Every run must identify the CodeQL driver")
        check_invocations(run)
        results = run.get("results")
        if not isinstance(results, list):
            raise CodeQLGateError("Every run must contain a results array")
        for result in results:
            if not isinstance(result, dict):
                raise CodeQLGateError("Result must be an object")
            rule_id = result.get("ruleId")
            if (
                not isinstance(rule_id, str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}", rule_id) is None
            ):
                rule_id = "<unknown-rule>"
            findings[rule_id] += 1
    if findings:
        summary = ", ".join(
            f"{rule}: {count}" for rule, count in sorted(findings.items())
        )
        raise CodeQLGateError(f"Found {sum(findings.values())} result(s): {summary}")
    return len(runs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--language", required=True, choices=("python", "javascript"))
    arguments = parser.parse_args(argv)
    try:
        run_count = check_report(arguments.directory, arguments.language)
    except (CodeQLGateError, OSError) as error:
        # All validation messages are fixed text or restricted rule identifiers.
        # Do not print file contents, result messages, paths or exception details.
        detail = (
            str(error) if isinstance(error, CodeQLGateError) else "Report access failed"
        )
        print(f"CodeQL gate failed: {detail}", file=sys.stderr)
        return 1
    print(f"CodeQL {arguments.language}: 0 results across {run_count} run(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
