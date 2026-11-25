"""Coverage for draft status and the completeness check."""

import importlib

from django.apps import apps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from .completeness import CONVERT_HINT, check_story
from .models import (
    BackgroundMusic,
    BlankLink,
    Language,
    Paragraph,
    Story,
    Word,
    WordForm,
)

status_migration = importlib.import_module("core.migrations.0012_story_status")


class CompletenessFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.english = Language.objects.get(code="en")
        cls.maori = Language.objects.get(code="mi")

    def make_story(self, learning=None, **fields):
        return Story.objects.create(
            title="Rona and the Moon",
            language=self.english,
            learning_language=learning or self.maori,
            **fields,
        )

    def make_word(self, key, image="word_images/moon.jpg", **forms):
        """Create a word with forms given as code=(text, audio)."""
        word = Word(key=key, image=image)
        word.save(skip_compression=True)
        for code, (text, audio) in forms.items():
            WordForm.objects.create(
                word=word,
                language=Language.objects.get(code=code),
                text=text,
                audio=audio,
            )
        return word

    def page(self, story, text, links=None, order=0, audio="paragraph_audio/1.mp3"):
        paragraph = Paragraph.objects.create(
            story=story, order=order, text=text, audio=audio
        )
        for placeholder, word in (links or {}).items():
            BlankLink.objects.create(
                paragraph=paragraph, placeholder=placeholder, word=word
            )
        return paragraph


class CheckStoryTests(CompletenessFixture):
    def test_a_complete_story_is_ready(self):
        story = self.make_story()
        moon = self.make_word(
            "moon",
            mi=("marama", "word_audio/marama.mp3"),
            en=("moon", "word_audio/moon.mp3"),
        )
        self.page(story, "The __BLANK_moon__ rose.", {"__BLANK_moon__": moon})

        report = check_story(story)

        self.assertEqual(report.problems, [])
        self.assertEqual(report.warnings, ["The story has no picture."])
        self.assertEqual(report.summary, "1 warning")

    def test_problems_that_break_play(self):
        story = self.make_story()
        moon = self.make_word("moon", en=("moon", None))
        self.page(
            story,
            "The __BLANK_moon__ and __BLANK_sky__.",
            {"__BLANK_moon__": moon, "__BLANK_sky__": None},
        )

        problems = check_story(story).problems

        self.assertEqual(
            problems,
            [
                "Page 1: __BLANK_sky__ is not linked to a word.",
                "Word moon has no Māori form (learning language).",
            ],
        )

    def test_a_missing_story_language_form_is_a_problem_only_when_languages_differ(
        self,
    ):
        moon = self.make_word("moon", mi=("marama", "word_audio/marama.mp3"))
        differ = self.make_story()
        self.page(differ, "The __BLANK_moon__.", {"__BLANK_moon__": moon})
        same = Story.objects.create(
            title="Te Marama", language=self.maori, learning_language=self.maori
        )
        self.page(same, "Te __BLANK_moon__.", {"__BLANK_moon__": moon})

        self.assertEqual(
            check_story(differ).problems,
            ["Word moon has no English form (story language)."],
        )
        self.assertEqual(check_story(same).problems, [])

    def test_missing_media_and_long_pages_are_warnings(self):
        story = self.make_story()
        moon = self.make_word(
            "moon", image=None, mi=("marama", None), en=("moon", None)
        )
        self.page(
            story,
            "The __BLANK_moon__. " + "word " * 60,
            {"__BLANK_moon__": moon},
            audio=None,
        )

        report = check_story(story)

        self.assertEqual(report.problems, [])
        self.assertEqual(
            report.warnings,
            [
                "Page 1 has no narration.",
                "Page 1 is longer than 240 characters.",
                "Word moon has no Māori audio.",
                "Word moon has no English audio.",
                "Word moon has no picture.",
                "The story has no picture.",
            ],
        )

    def test_audio_that_is_not_mp3_is_a_warning(self):
        music = BackgroundMusic.objects.create(
            title="Humoresque", audio_file="bgm/h.m4a"
        )
        story = self.make_story(background_music=music)
        moon = self.make_word(
            "moon",
            mi=("marama", "word_audio/marama.ogg"),
            en=("moon", "word_audio/moon.mp3"),
        )
        self.page(
            story,
            "The __BLANK_moon__.",
            {"__BLANK_moon__": moon},
            audio="paragraph_audio/Rona_moon_01.ogg",
        )

        warnings = check_story(story).warnings

        self.assertIn(
            f"Page 1 narration is OGG, not MP3; {CONVERT_HINT}.",
            warnings,
        )
        self.assertIn(
            f"Word moon Māori audio is OGG, not MP3; {CONVERT_HINT}.",
            warnings,
        )
        self.assertIn(
            f"The background music is M4A, not MP3; {CONVERT_HINT}.",
            warnings,
        )
        self.assertFalse(any("English audio" in warning for warning in warnings))

    def test_a_story_without_pages_or_languages(self):
        story = Story.objects.create(title="Empty")

        self.assertEqual(
            check_story(story).problems,
            [
                "Choose the story language and the learning language.",
                "The story has no pages.",
            ],
        )

    def test_a_story_without_blanks_is_a_warning(self):
        story = self.make_story()
        self.page(story, "No blanks here.")

        self.assertIn("The story has no blanks.", check_story(story).warnings)


class PublicStatusTests(CompletenessFixture):
    def test_drafts_are_hidden_from_players(self):
        draft = self.make_story()
        published = self.make_story(status=Story.PUBLISHED)

        stories = self.client.get(reverse("story-list")).json()
        draft_detail = self.client.get(reverse("story-detail", args=[draft.pk]))
        published_detail = self.client.get(reverse("story-detail", args=[published.pk]))

        self.assertEqual([story["id"] for story in stories], [published.pk])
        self.assertEqual(draft_detail.status_code, 404)
        self.assertEqual(published_detail.status_code, 200)

    def test_new_stories_start_as_drafts_and_existing_ones_are_published(self):
        existing = Story.objects.create(title="Live")
        Story.objects.filter(pk=existing.pk).update(status=Story.DRAFT)

        status_migration.publish_existing_stories(apps, None)

        existing.refresh_from_db()
        self.assertEqual(existing.status, Story.PUBLISHED)
        self.assertEqual(Story.objects.create(title="New").status, Story.DRAFT)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class PublishingInAdminTests(CompletenessFixture):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_user = get_user_model().objects.create_superuser(
            username="story-editor", email="editor@example.invalid", password=None
        )

    def publish(self, text):
        """Add a story with one page and ask for it to be published."""
        self.client.force_login(self.admin_user)
        return self.client.post(
            reverse("admin:core_story_add"),
            {
                "title": "Rona and the Moon",
                "status": Story.PUBLISHED,
                "language": self.english.pk,
                "learning_language": self.maori.pk,
                "story_picture": "",
                "background_music": "",
                "story_text": "",
                "paragraphs-TOTAL_FORMS": "1",
                "paragraphs-INITIAL_FORMS": "0",
                "paragraphs-MIN_NUM_FORMS": "0",
                "paragraphs-MAX_NUM_FORMS": "1000",
                "paragraphs-0-id": "",
                "paragraphs-0-story": "",
                "paragraphs-0-order": "0",
                "paragraphs-0-text": text,
                "_save": "Save",
            },
        )

    def test_a_story_with_problems_is_kept_as_a_draft(self):
        response = self.publish("The {{sky}} was dark.")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Story.objects.get().status, Story.DRAFT)
        errors = [
            str(message)
            for message in get_messages(response.wsgi_request)
            if message.level == messages.ERROR
        ]
        self.assertTrue(any("__BLANK_sky__ is not linked" in error for error in errors))

    def test_a_playable_story_is_published_despite_warnings(self):
        self.make_word("moon", mi=("marama", None), en=("moon", None))

        response = self.publish("The {{moon}} rose.")

        self.assertEqual(response.status_code, 302)
        story = Story.objects.get()
        self.assertEqual(story.status, Story.PUBLISHED)
        changelist = self.client.get(reverse("admin:core_story_changelist"))
        self.assertContains(changelist, "warnings")
        change = self.client.get(reverse("admin:core_story_change", args=[story.pk]))
        self.assertContains(change, "Word moon has no Māori audio.")
