from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import quote

from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve

from . import views


@override_settings(ROOT_URLCONF="polls.urls")
class PlainTextPollTests(SimpleTestCase):
    def assert_plain_text(self, response, expected):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.content.decode(), expected)

    def test_numeric_routes_preserve_their_response_text(self):
        for path, expected in [
            ("/5/", "You're looking at question 5."),
            ("/5/results/", "You're looking at the results of question 5."),
            ("/5/vote/", "You're voting on question 5."),
        ]:
            with self.subTest(path=path):
                self.assertEqual(resolve(path).kwargs, {"question_id": 5})
                self.assert_plain_text(self.client.get(path), expected)

    def test_numeric_routes_reject_markup_and_other_non_numeric_ids(self):
        for value in ['<svg onload="alert(1)">', "1<script>alert(1)</script>", "x"]:
            for suffix in ["", "results/", "vote/"]:
                with self.subTest(value=value, suffix=suffix):
                    response = self.client.get(f"/{quote(value, safe='')}/{suffix}")
                    self.assertEqual(response.status_code, 404)

    def test_views_keep_markup_inert_even_when_called_without_the_converter(self):
        malicious_id = '<img src=x onerror="alert(1)">'
        request = RequestFactory().get("/")
        for view, expected in [
            (views.detail, f"You're looking at question {malicious_id}."),
            (
                views.results,
                f"You're looking at the results of question {malicious_id}.",
            ),
            (views.vote, f"You're voting on question {malicious_id}."),
        ]:
            with self.subTest(view=view.__name__):
                self.assert_plain_text(view(request, malicious_id), expected)

    def test_question_list_keeps_stored_markup_inert_without_losing_text(self):
        question_texts = ['<script>alert("stored")</script>', "Māori & English"]
        questions = [SimpleNamespace(question_text=text) for text in question_texts]
        with patch.object(views.Question.objects, "order_by", return_value=questions):
            response = self.client.get("/")
        self.assert_plain_text(response, ", ".join(question_texts))
