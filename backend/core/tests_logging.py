"""Regression coverage for request fields written to plain-text API logs."""

import logging
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.http import Http404
from django.test import SimpleTestCase
from django.urls import Resolver404, resolve, reverse
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from .logging_utils import escape_log_value
from .views import AppConfigAPIView, StoryDetailAPIView, StoryListAPIView


class LogValueTests(SimpleTestCase):
    def test_printable_values_remain_readable(self):
        for value in ("127.0.0.1", "2001:db8::1", "unknown", 42, "Te reo Māori"):
            with self.subTest(value=value):
                self.assertEqual(escape_log_value(value), str(value))

    def test_controls_cannot_create_another_line_or_terminal_instruction(self):
        controls = [chr(code) for code in (*range(32), *range(127, 160))]
        controls += ["\u2028", "\u2029", "\u202e", "\u2066"]
        for control in controls:
            with self.subTest(control=repr(control)):
                output = StringIO()
                handler = logging.StreamHandler(output)
                record = logging.LogRecord(
                    "test", logging.INFO, __file__, 0, "ip=%s", (), None
                )
                record.args = (escape_log_value("127.0.0.1" + control + "FORGED"),)
                handler.handle(record)

                rendered = output.getvalue()
                self.assertEqual(len(rendered.splitlines()), 1)
                self.assertTrue(rendered.endswith("\n"))
                self.assertTrue(rendered[:-1].isprintable())
                self.assertIn("127.0.0.1", rendered)
                self.assertIn("FORGED", rendered)

    def test_escape_sequences_retain_the_difference_from_literal_backslashes(self):
        self.assertEqual(escape_log_value("\r\n\t\x1b\u2028"), r"\r\n\t\x1b\u2028")
        self.assertEqual(escape_log_value(r"\r\n"), r"\\r\\n")


class PublicAPILoggingTests(SimpleTestCase):
    malicious_value = "42\r\n[INFO] FORGED\t\x1b[31m\u2028"
    escaped_value = r"42\r\n[INFO] FORGED\t\x1b[31m\u2028"

    def setUp(self):
        self.factory = APIRequestFactory()
        self.story = SimpleNamespace(title="Te reo Māori\nA new line")
        self.story_data = {"id": 42, "title": self.story.title}

    def assert_single_line_records(self, logs):
        self.assertEqual(len("\n".join(logs.output).splitlines()), len(logs.records))
        for record in logs.records:
            self.assertTrue(record.getMessage().isprintable())

    def test_all_request_logs_escape_malformed_remote_addresses(self):
        request = self.factory.get("/", REMOTE_ADDR=self.malicious_value)
        with (
            patch(
                "rest_framework.generics.ListAPIView.list",
                return_value=Response([]),
            ),
            patch.object(StoryDetailAPIView, "get_object", return_value=self.story),
            patch.object(
                StoryDetailAPIView,
                "get_serializer",
                return_value=SimpleNamespace(data=self.story_data),
            ),
            patch("core.views.AppConfig.objects.select_related") as config_query,
        ):
            config_query.return_value.first.return_value = None
            for view, kwargs in (
                (StoryListAPIView, {}),
                (StoryDetailAPIView, {"pk": 42}),
                (AppConfigAPIView, {}),
            ):
                with self.subTest(view=view.__name__):
                    with self.assertLogs("core.views", level="INFO") as logs:
                        response = view.as_view()(request, **kwargs)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(self.escaped_value, logs.records[0].getMessage())
                    self.assert_single_line_records(logs)

    def test_detail_success_escapes_alternate_caller_id_without_changing_response(self):
        request = self.factory.get("/", REMOTE_ADDR="2001:db8::1")
        with (
            patch.object(StoryDetailAPIView, "get_object", return_value=self.story),
            patch.object(
                StoryDetailAPIView,
                "get_serializer",
                return_value=SimpleNamespace(data=self.story_data),
            ),
            self.assertLogs("core.views", level="INFO") as logs,
        ):
            response = StoryDetailAPIView.as_view()(request, pk=self.malicious_value)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.story_data)
        self.assertEqual(len(logs.records), 2)
        for record in logs.records:
            self.assertIn("id=" + self.escaped_value, record.getMessage())
        self.assertIn("ip=2001:db8::1", logs.records[0].getMessage())
        self.assertIn("title='Te reo Māori\\nA new line'", logs.records[1].getMessage())
        self.assert_single_line_records(logs)

    def test_missing_story_log_escapes_alternate_caller_id_and_keeps_404(self):
        with (
            patch.object(StoryDetailAPIView, "get_object", side_effect=Http404),
            self.assertLogs("core.views", level="WARNING") as logs,
        ):
            response = StoryDetailAPIView.as_view()(
                self.factory.get("/"), pk=self.malicious_value
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            logs.records[0].getMessage(), "Story not found: id=" + self.escaped_value
        )
        self.assert_single_line_records(logs)

    def test_error_log_escapes_id_and_retains_traceback_and_safe_api_error(self):
        error = RuntimeError("synthetic internal diagnostic")
        with (
            patch.object(StoryDetailAPIView, "get_object", side_effect=error),
            self.assertLogs("core.views", level="ERROR") as logs,
        ):
            response = StoryDetailAPIView.as_view()(
                self.factory.get("/"), pk=self.malicious_value
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {
                "error": "Failed to retrieve story",
                "detail": "An unexpected error occurred. Please try again later.",
            },
        )
        record = logs.records[0]
        self.assertEqual(
            record.getMessage(), "Error retrieving story " + self.escaped_value
        )
        self.assertTrue(record.getMessage().isprintable())
        self.assertIs(record.exc_info[1], error)
        self.assertIsNotNone(record.exc_info[2])
        self.assertIn("Traceback (most recent call last):", logs.output[0])

    def test_normal_ids_and_addresses_keep_original_log_messages(self):
        with (
            patch.object(StoryDetailAPIView, "get_object", return_value=self.story),
            patch.object(
                StoryDetailAPIView,
                "get_serializer",
                return_value=SimpleNamespace(data=self.story_data),
            ),
            self.assertLogs("core.views", level="INFO") as logs,
        ):
            response = StoryDetailAPIView.as_view()(
                self.factory.get("/", REMOTE_ADDR="127.0.0.1"), pk=42
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            logs.records[0].getMessage(), "Story detail requested: id=42, ip=127.0.0.1"
        )
        self.assertIn("id=42, title=", logs.records[1].getMessage())

    def test_public_story_route_converts_ids_to_int_and_rejects_malformed_ids(self):
        detail_url = reverse("story-detail", args=[42])
        self.assertEqual(resolve(detail_url).kwargs, {"pk": 42})
        for value in ("42\r\nFORGED", "42%0d%0aFORGED", "42\x1b[31m", "invalid"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(Resolver404):
                    resolve(detail_url.replace("42", value))
