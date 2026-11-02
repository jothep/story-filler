"""Identify pull requests changing only root Markdown or docs/**/*.md files."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys


class DocsOnlyError(ValueError):
    """The pull request diff could not be checked reliably."""


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DocsOnlyError("Pull request metadata contains duplicate JSON keys")
        value[key] = item
    return value


def reject_constant(_value):
    raise DocsOnlyError("Pull request metadata contains invalid JSON")


def pull_request_commits(event_path):
    if not event_path:
        raise DocsOnlyError("Pull request event file is required")
    try:
        event = json.loads(
            Path(event_path).read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except DocsOnlyError:
        raise
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise DocsOnlyError("Pull request metadata could not be read") from error
    pull_request = event.get("pull_request") if isinstance(event, dict) else None
    if not isinstance(pull_request, dict):
        raise DocsOnlyError("Pull request metadata is missing")
    commits = []
    for side in ("base", "head"):
        reference = pull_request.get(side)
        sha = reference.get("sha") if isinstance(reference, dict) else None
        if not isinstance(sha, str) or re.fullmatch(r"[0-9a-fA-F]{40}", sha) is None:
            raise DocsOnlyError("Pull request commit IDs must be full SHA-1 values")
        commits.append(sha.lower())
    return commits


def check_docs_only(event_name, event_path):
    if event_name != "pull_request":
        return False, 0
    base, head = pull_request_commits(event_path)
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "-z",
                "--no-renames",
                f"{base}...{head}",
                "--",
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DocsOnlyError("Pull request diff could not be read") from error
    if result.returncode != 0:
        raise DocsOnlyError("Git could not compare the pull request commits")
    if not result.stdout:
        return False, 0
    if not result.stdout.endswith(b"\0"):
        raise DocsOnlyError("Git returned an incomplete path list")
    paths = result.stdout[:-1].split(b"\0")
    for path in paths:
        if any(part in (b"", b".", b"..") for part in path.split(b"/")):
            raise DocsOnlyError("Git returned an invalid path list")
    docs_only = all(
        path.endswith(b".md") and (b"/" not in path or path.startswith(b"docs/"))
        for path in paths
    )
    return docs_only, len(paths)


def main():
    try:
        docs_only, path_count = check_docs_only(
            os.environ.get("GITHUB_EVENT_NAME"), os.environ.get("GITHUB_EVENT_PATH")
        )
        output_path = os.environ.get("GITHUB_OUTPUT")
        if not output_path:
            raise DocsOnlyError("GitHub output file is required")
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"docs_only={str(docs_only).lower()}\n")
    except (DocsOnlyError, OSError, ValueError) as error:
        message = (
            str(error) if isinstance(error, DocsOnlyError) else "Output write failed"
        )
        print(f"Documentation-only check failed: {message}", file=sys.stderr)
        return 1
    print(f"docs_only={str(docs_only).lower()} ({path_count} changed paths checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
