"""Offline tests for smoke-check response validation and bounded retries."""

import importlib.util
import io
import json
from contextlib import redirect_stdout
from email.message import Message
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError


SPEC = importlib.util.spec_from_file_location("smoke_check", Path(__file__).with_name("smoke-check.py"))
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)

STORIES = [{"id": 1, "title": "Story"}]
DETAIL = {
    "id": 1,
    "paragraphs": [{"id": 1, "text": "A story", "blank_links": []}],
    "words_in_bank": [{"id": 1, "maori_word": "kāinga", "english_translation": "home"}],
}


def response(data, content_type="application/json"):
    result = MagicMock()
    result.__enter__.return_value = result
    result.status = 200
    result.headers = Message()
    result.headers["Content-Type"] = content_type
    result.read.return_value = json.dumps(data).encode()
    return result


class SmokeCheckTests(unittest.TestCase):
    def test_success_checks_only_three_public_get_endpoints(self):
        with patch.object(smoke, "urlopen", side_effect=[
            response(STORIES), response(DETAIL), response({"menu_bgm": None})
        ]) as opened, redirect_stdout(io.StringIO()):
            smoke.check_api("https://example.test")
        self.assertEqual([call.args[0].full_url for call in opened.call_args_list], [
            "https://example.test/api/stories/",
            "https://example.test/api/stories/1/",
            "https://example.test/api/config/",
        ])
        self.assertTrue(all(call.args[0].get_method() == "GET" for call in opened.call_args_list))

    def test_empty_database_is_not_a_successful_demo(self):
        with patch.object(smoke, "urlopen", return_value=response([])):
            with self.assertRaisesRegex(smoke.CheckFailed, "non-empty story list"):
                smoke.check_api("https://example.test")

    def test_missing_word_bank_fails_even_with_http_200(self):
        with patch.object(smoke, "urlopen", side_effect=[
            response(STORIES), response({**DETAIL, "words_in_bank": []})
        ]), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(smoke.CheckFailed, "non-empty word bank"):
                smoke.check_api("https://example.test")

    def test_html_response_fails_without_printing_body(self):
        with patch.object(smoke, "urlopen", return_value=response("unexpected page", "text/html")):
            with self.assertRaisesRegex(smoke.CheckFailed, "expected a JSON response"):
                smoke.check_api("https://example.test")

    def test_transient_503_is_retried_and_bounded(self):
        errors = [HTTPError("https://example.test", 503, "unavailable", {}, None) for _ in range(3)]
        with patch.object(smoke, "urlopen", side_effect=errors) as opened, \
                patch.object(smoke.time, "sleep") as slept, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(smoke.CheckFailed, "after 3 attempt"):
                smoke.check_api("https://example.test")
        self.assertEqual(opened.call_count, 3)
        self.assertEqual(slept.call_count, 2)

    def test_404_is_not_retried(self):
        error = HTTPError("https://example.test", 404, "not found", {}, None)
        with patch.object(smoke, "urlopen", side_effect=error) as opened:
            with self.assertRaisesRegex(smoke.CheckFailed, "HTTP 404"):
                smoke.check_api("https://example.test")
        self.assertEqual(opened.call_count, 1)


if __name__ == "__main__":
    unittest.main()
