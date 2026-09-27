#!/usr/bin/env python3
"""Read-only check of the public story API; no credentials or third-party packages."""

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class CheckFailed(Exception):
    """An HTTP response or API contract did not pass the smoke check."""


def base_url(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise argparse.ArgumentTypeError(
            "Use a public HTTP(S) base URL without credentials, query, or fragment."
        )
    return value.rstrip("/")


def fetch_json(url, path, timeout, attempts, retry_delay):
    """Retry transient HTTP/network errors, with a timeout and bounded response size."""
    for attempt in range(1, attempts + 1):
        try:
            request = Request(
                url + path,
                headers={"Accept": "application/json", "User-Agent": "story-api-smoke-check/1"},
            )
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise CheckFailed(f"{path}: expected HTTP 200, got {response.status}")
                content_type = response.headers.get_content_type()
                if content_type != "application/json" and not content_type.endswith("+json"):
                    raise CheckFailed(f"{path}: expected a JSON response")
                payload = response.read(2 * 1024 * 1024 + 1)
                if len(payload) > 2 * 1024 * 1024:
                    raise CheckFailed(f"{path}: response exceeds the 2 MiB smoke-check limit")
                try:
                    return json.loads(payload)
                except (ValueError, UnicodeDecodeError) as exc:
                    raise CheckFailed(f"{path}: invalid JSON") from exc
        except HTTPError as exc:
            reason = f"HTTP {exc.code}"
            transient = exc.code in (408, 429, 500, 502, 503, 504)
            exc.close()
            if not transient:
                raise CheckFailed(f"{path}: {reason}") from exc
        except (URLError, TimeoutError, OSError):
            reason = "network error or request timeout"

        if attempt == attempts:
            raise CheckFailed(f"{path}: {reason} after {attempts} attempt(s)")
        print(f"RETRY {path}: {reason}; attempt {attempt + 1}/{attempts}", flush=True)
        time.sleep(retry_delay)


def positive_id(value):
    return type(value) is int and value > 0


def nonempty_text(value):
    return isinstance(value, str) and bool(value.strip())


def check_api(url, timeout=20, attempts=3, retry_delay=3):
    def get(path):
        return fetch_json(url, path, timeout, attempts, retry_delay)

    stories = get("/api/stories/")
    if not isinstance(stories, list) or not stories:
        raise CheckFailed("/api/stories/: expected a non-empty story list")
    if not all(
        isinstance(story, dict)
        and positive_id(story.get("id"))
        and nonempty_text(story.get("title"))
        for story in stories
    ):
        raise CheckFailed("/api/stories/: invalid story id/title structure")
    print(f"PASS /api/stories/: {len(stories)} story(s)", flush=True)

    story_id = stories[0]["id"]
    detail_path = f"/api/stories/{story_id}/"
    detail = get(detail_path)
    if not isinstance(detail, dict) or detail.get("id") != story_id:
        raise CheckFailed(f"{detail_path}: invalid story detail or mismatched id")
    paragraphs = detail.get("paragraphs")
    words = detail.get("words_in_bank")
    if not isinstance(paragraphs, list) or not paragraphs or not all(
        isinstance(paragraph, dict)
        and positive_id(paragraph.get("id"))
        and nonempty_text(paragraph.get("text"))
        and isinstance(paragraph.get("blank_links"), list)
        for paragraph in paragraphs
    ):
        raise CheckFailed(f"{detail_path}: expected non-empty paragraphs with id/text/blank_links")
    if not isinstance(words, list) or not words or not all(
        isinstance(word, dict)
        and positive_id(word.get("id"))
        and nonempty_text(word.get("maori_word"))
        and nonempty_text(word.get("english_translation"))
        for word in words
    ):
        raise CheckFailed(f"{detail_path}: expected a non-empty word bank with id/translations")
    print(f"PASS {detail_path}: {len(paragraphs)} paragraph(s), {len(words)} word(s)", flush=True)

    if not isinstance(get("/api/config/"), dict):
        raise CheckFailed("/api/config/: expected a JSON object")
    print("PASS /api/config/: JSON object", flush=True)
    print("Smoke check passed: public API reads only; media, writes, and full gameplay are not tested.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, type=base_url)
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout in seconds (1-60)")
    parser.add_argument("--attempts", type=int, default=3, help="Attempts per endpoint (1-5)")
    parser.add_argument("--retry-delay", type=int, default=3, help="Seconds between attempts (0-10)")
    args = parser.parse_args(argv)
    if not (1 <= args.timeout <= 60 and 1 <= args.attempts <= 5 and 0 <= args.retry_delay <= 10):
        parser.error("Require timeout 1-60, attempts 1-5, and retry-delay 0-10.")
    try:
        check_api(args.base_url, args.timeout, args.attempts, args.retry_delay)
    except CheckFailed as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
