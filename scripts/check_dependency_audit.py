"""Check that a pip-audit JSON report covers every dependency in a hash lock.

This checks coverage, not vulnerability severity. Keep pip-audit's exit status
as a separate required check. Only the repository's pip-tools lock syntax is
accepted; unsupported requirements must fail rather than disappear from review.
"""

import argparse
import json
from pathlib import Path
import re
import sys

PACKAGE_NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
PINNED_VERSION = r"[0-9][A-Za-z0-9.!+]*"
HASH = r"--hash=sha256:[A-Fa-f0-9]{64}"
LOCK_ENTRY = re.compile(
    rf"(?P<name>{PACKAGE_NAME})==(?P<version>{PINNED_VERSION})" rf"(?:\s+{HASH})+"
)


class AuditCoverageError(ValueError):
    """The inputs cannot establish complete audit coverage."""


def normalize_name(name):
    """Match Python package names across case, hyphens, underscores and dots."""
    return re.sub(r"[-_.]+", "-", name).lower()


def logical_lines(text):
    """Join pip-tools hash continuations while preserving useful line numbers."""
    parts = []
    start = 0
    for number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"\s+#.*$", "", line).rstrip()
        if not parts:
            start = number
        if line.endswith("\\"):
            parts.append(line[:-1].strip())
            continue
        parts.append(line)
        yield start, " ".join(parts)
        parts = []
    if parts:
        raise AuditCoverageError(f"Unfinished lock continuation on line {start}")


def read_lock(path):
    """Read exact pins with SHA-256 hashes; reject all unhandled lock syntax."""
    packages = {}
    for number, line in logical_lines(Path(path).read_text(encoding="utf-8")):
        if line in ("--only-binary :all:", "--only-binary=:all:"):
            continue
        match = LOCK_ENTRY.fullmatch(line)
        if match is None:
            raise AuditCoverageError(
                f"Unsupported lock entry on line {number}: expected name==version "
                "with SHA-256 hashes. Markers, includes and other options are "
                "not supported."
            )
        name = normalize_name(match["name"])
        if name in packages:
            raise AuditCoverageError(f"Duplicate locked dependency: {name}")
        packages[name] = match["version"]
    if not packages:
        raise AuditCoverageError("Lock contains no dependencies")
    return packages


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AuditCoverageError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_report(path):
    report = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=unique_json_object,
    )
    if not isinstance(report, dict) or not isinstance(report.get("dependencies"), list):
        raise AuditCoverageError("Audit report must contain a dependencies array")

    packages = {}
    for position, dependency in enumerate(report["dependencies"], 1):
        if not isinstance(dependency, dict):
            raise AuditCoverageError(f"Invalid audit dependency at position {position}")
        name = dependency.get("name")
        if not isinstance(name, str) or re.fullmatch(PACKAGE_NAME, name) is None:
            raise AuditCoverageError(
                f"Invalid audit package name at position {position}"
            )
        name = normalize_name(name)
        if name in packages:
            raise AuditCoverageError(f"Duplicate audited dependency: {name}")
        if "skip_reason" in dependency:
            raise AuditCoverageError(f"Audit skipped dependency: {name}")
        version = dependency.get("version")
        if not isinstance(version, str) or not version:
            raise AuditCoverageError(f"Missing audit version for {name}")
        if not isinstance(dependency.get("vulns"), list):
            raise AuditCoverageError(f"Missing vulnerability results for {name}")
        packages[name] = version
    return packages


def check_coverage(lock_path, report_path):
    locked = read_lock(lock_path)
    audited = read_report(report_path)
    problems = []
    missing = sorted(locked.keys() - audited.keys())
    extra = sorted(audited.keys() - locked.keys())
    if missing:
        problems.append("Missing from audit: " + ", ".join(missing))
    if extra:
        problems.append("Not in lock: " + ", ".join(extra))
    for name in sorted(locked.keys() & audited.keys()):
        if locked[name] != audited[name]:
            problems.append(
                f"Version mismatch for {name}: locked {locked[name]}, "
                f"audited {audited[name]}"
            )
    if problems:
        raise AuditCoverageError("; ".join(problems))
    return len(locked)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lock", type=Path, help="pip-tools requirements hash lock")
    parser.add_argument("report", type=Path, help="pip-audit --format=json report")
    arguments = parser.parse_args(argv)
    try:
        count = check_coverage(arguments.lock, arguments.report)
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(f"Audit coverage check failed: {error}", file=sys.stderr)
        return 1
    print(f"Audit coverage matches all {count} locked dependencies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
