"""Coverage for word entries with a form per language."""

import importlib

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import BlankLink, Language, Paragraph, Story, Word, WordForm

copy_migration = importlib.import_module("core.migrations.0011_copy_words_into_forms")


class CopyWordsIntoFormsTests(TestCase):
    """The data migration, run against legacy rows created in the test."""

    def forms(self, word):
        return {
            form.language.code: (form.text, form.audio.name or None)
            for form in word.forms.select_related("language")
        }

    def test_copies_legacy_columns_keys_and_story_languages(self):
        moon = Word.objects.create(
            maori_word="marama",
            english_translation="moon",
            maori_audio="word_audio_maori/marama.mp3",
        )
        light = Word.objects.create(maori_word="rama", english_translation="Light")
        glow = Word.objects.create(
            maori_word="māramatanga", english_translation="light"
        )
        house = Word.objects.create(maori_word="kāinga", english_translation="")
        story = Story.objects.create(title="Rona and the Moon")

        copy_migration.copy_words_into_forms(apps, None)
        copy_migration.copy_words_into_forms(apps, None)

        for word in (moon, light, glow, house):
            word.refresh_from_db()
        self.assertEqual(
            [moon.key, light.key, glow.key, house.key],
            ["moon", "light", "light_2", "kainga"],
        )
        self.assertEqual(
            self.forms(moon),
            {"en": ("moon", None), "mi": ("marama", "word_audio_maori/marama.mp3")},
        )
        self.assertEqual(self.forms(house), {"mi": ("kāinga", None)})
        self.assertEqual(WordForm.objects.count(), 7)
        story.refresh_from_db()
        self.assertEqual(story.language.code, "en")
        self.assertEqual(story.learning_language.code, "mi")


class WordApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.english = Language.objects.get(code="en")
        cls.maori = Language.objects.get(code="mi")
        cls.chinese = Language.objects.create(code="zh-Hans", name="中文")
        cls.moon = Word(key="moon", image="word_images/moon.jpg")
        cls.moon.save(skip_compression=True)
        WordForm.objects.create(
            word=cls.moon,
            language=cls.maori,
            text="marama",
            audio="word_audio/marama.mp3",
        )
        WordForm.objects.create(word=cls.moon, language=cls.english, text="moon")
        WordForm.objects.create(word=cls.moon, language=cls.chinese, text="月亮")

    def story_with(self, learning_language, *words):
        story = Story.objects.create(
            title="Moon", language=self.english, learning_language=learning_language
        )
        paragraph = Paragraph.objects.create(
            story=story,
            order=0,
            text=" ".join(f"__BLANK_{word.key}__" for word in words),
        )
        for word in words:
            BlankLink.objects.create(
                paragraph=paragraph, placeholder=f"__BLANK_{word.key}__", word=word
            )
        return story

    def detail(self, story):
        response = self.client.get(reverse("story-detail", args=[story.pk]))
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_learning_language_fills_text_and_story_language_the_translation(self):
        data = self.detail(self.story_with(self.maori, self.moon))

        self.assertEqual(data["language"], {"code": "en", "name": "English"})
        self.assertEqual(data["learning_language"], {"code": "mi", "name": "Māori"})
        word = data["words_in_bank"][0]
        self.assertEqual(
            {name: word[name] for name in ("key", "text", "translation")},
            {"key": "moon", "text": "marama", "translation": "moon"},
        )
        self.assertTrue(word["audio"].endswith("word_audio/marama.mp3"))
        self.assertEqual(word["maori_word"], "marama")
        self.assertEqual(word["english_translation"], "moon")
        self.assertEqual(word["maori_audio"], word["audio"])
        self.assertIsNone(word["english_audio"])
        self.assertEqual(data["paragraphs"][0]["blank_links"][0]["word"], word)

    def test_another_learning_language_uses_its_forms(self):
        word = self.detail(self.story_with(self.chinese, self.moon))["words_in_bank"][0]

        self.assertEqual((word["text"], word["translation"]), ("月亮", "moon"))
        self.assertEqual(word["maori_word"], "月亮")

    def test_a_story_in_its_own_language_has_no_translation(self):
        word = self.detail(self.story_with(self.english, self.moon))["words_in_bank"][0]

        self.assertEqual((word["text"], word["translation"]), ("moon", None))
        self.assertIsNone(word["translation_audio"])
        self.assertEqual(word["english_translation"], "moon")

    def test_a_missing_form_is_null(self):
        star = Word.objects.create(key="star")
        word = self.detail(self.story_with(self.maori, star))["words_in_bank"][0]

        self.assertEqual(
            (word["key"], word["text"], word["translation"]), ("star", None, None)
        )

    def test_queries_do_not_grow_with_words(self):
        few = self.story_with(self.maori, self.moon)
        more_words = [self.moon]
        for key in ("star", "sun", "sky"):
            word = Word.objects.create(key=key)
            WordForm.objects.create(word=word, language=self.maori, text=key)
            more_words.append(word)
        many = self.story_with(self.maori, *more_words)

        counts = []
        for story in (few, many):
            with CaptureQueriesContext(connection) as queries:
                self.detail(story)
            counts.append(len(queries))
        self.assertEqual(counts[0], counts[1])


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class WordAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="word-editor", email="editor@example.invalid", password=None
        )

    def test_a_word_is_added_with_its_language_forms(self):
        self.client.force_login(self.admin_user)
        english = Language.objects.get(code="en")
        maori = Language.objects.get(code="mi")

        response = self.client.post(
            reverse("admin:core_word_add"),
            {
                "key": "moon",
                "forms-TOTAL_FORMS": "2",
                "forms-INITIAL_FORMS": "0",
                "forms-MIN_NUM_FORMS": "0",
                "forms-MAX_NUM_FORMS": "1000",
                "forms-0-language": english.pk,
                "forms-0-text": "moon",
                "forms-1-language": maori.pk,
                "forms-1-text": "marama",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        word = Word.objects.get(key="moon")
        self.assertEqual(
            sorted(word.forms.values_list("language__code", "text")),
            [("en", "moon"), ("mi", "marama")],
        )
        self.assertIsNone(word.maori_word)
        changelist = self.client.get(reverse("admin:core_word_changelist"))
        self.assertContains(changelist, "mi: marama")

    def test_keys_outside_the_placeholder_alphabet_are_refused(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("admin:core_word_add"),
            {
                "key": "full-moon",
                "forms-TOTAL_FORMS": "0",
                "forms-INITIAL_FORMS": "0",
                "forms-MIN_NUM_FORMS": "0",
                "forms-MAX_NUM_FORMS": "1000",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Word.objects.exists())
