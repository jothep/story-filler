"""Coverage for linking paragraph placeholders to words in the bank."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from .blanks import (
    build_word_index,
    link_placeholders,
    placeholder_key,
    placeholders_in,
)
from .models import BlankLink, Paragraph, Story, Word


class PlaceholderKeyTests(TestCase):
    def test_keys_are_lowercase_ascii_with_underscores(self):
        self.assertEqual(placeholder_key("Moon"), "moon")
        self.assertEqual(placeholder_key("kōrero paki"), "korero_paki")
        self.assertEqual(placeholder_key("  Kāinga! "), "kainga")

    def test_placeholders_are_distinct_and_ordered(self):
        text = "__BLANK_moon__ and __BLANK_tale__, then __BLANK_moon__ again"
        self.assertEqual(placeholders_in(text), ["__BLANK_moon__", "__BLANK_tale__"])


class LinkPlaceholdersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.story = Story.objects.create(title="Rona and the Moon")
        cls.moon = Word.objects.create(maori_word="marama", english_translation="moon")
        cls.tale = Word.objects.create(
            maori_word="kōrero paki", english_translation="tale"
        )

    def paragraph(self, text):
        return Paragraph.objects.create(story=self.story, order=1, text=text)

    def links(self, paragraph):
        return dict(
            paragraph.blank_links.values_list("placeholder", "word__maori_word")
        )

    def test_links_by_english_or_maori_and_reports_the_rest(self):
        paragraph = self.paragraph(
            "The __BLANK_moon__ told a __BLANK_korero_paki__ about the "
            "__BLANK_sky__ and the __BLANK_moon__."
        )

        unlinked = link_placeholders(paragraph)

        self.assertEqual(unlinked, ["__BLANK_sky__"])
        self.assertEqual(
            self.links(paragraph),
            {"__BLANK_moon__": "marama", "__BLANK_korero_paki__": "kōrero paki"},
        )

    def test_existing_links_are_kept(self):
        paragraph = self.paragraph("The __BLANK_moon__ rose.")
        BlankLink.objects.create(
            paragraph=paragraph, placeholder="__BLANK_moon__", word=self.tale
        )

        self.assertEqual(link_placeholders(paragraph), [])
        self.assertEqual(self.links(paragraph), {"__BLANK_moon__": "kōrero paki"})

    def test_ambiguous_keys_are_not_linked(self):
        Word.objects.create(maori_word="rama", english_translation="light")
        Word.objects.create(maori_word="māramatanga", english_translation="light")
        paragraph = self.paragraph("A __BLANK_light__ shone.")

        self.assertEqual(
            link_placeholders(paragraph, build_word_index()), ["__BLANK_light__"]
        )
        self.assertEqual(self.links(paragraph), {})


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class StoryAdminLinkingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="story-editor", email="editor@example.invalid", password=None
        )
        Word.objects.create(maori_word="marama", english_translation="moon")

    def post_story(self, user):
        self.client.force_login(user)
        return self.client.post(
            reverse("admin:core_story_add"),
            {
                "title": "Rona and the Moon",
                "story_picture": "",
                "background_music": "",
                "paragraphs-TOTAL_FORMS": "1",
                "paragraphs-INITIAL_FORMS": "0",
                "paragraphs-MIN_NUM_FORMS": "0",
                "paragraphs-MAX_NUM_FORMS": "1000",
                "paragraphs-0-id": "",
                "paragraphs-0-story": "",
                "paragraphs-0-order": "1",
                "paragraphs-0-text": "The __BLANK_moon__ lit the __BLANK_sky__.",
                "_save": "Save",
            },
        )

    def test_saving_a_story_links_placeholders_and_warns_about_the_rest(self):
        response = self.post_story(self.admin_user)

        self.assertEqual(response.status_code, 302)
        link = BlankLink.objects.get()
        self.assertEqual(link.placeholder, "__BLANK_moon__")
        self.assertEqual(link.word.maori_word, "marama")
        warnings = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("__BLANK_sky__" in message for message in warnings))

    def test_editors_without_blank_link_permission_get_no_links(self):
        editor = get_user_model().objects.create_user(
            username="paragraph-editor", is_staff=True
        )
        editor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="core",
                codename__in=[
                    "add_story",
                    "change_story",
                    "view_story",
                    "add_paragraph",
                    "change_paragraph",
                    "view_paragraph",
                ],
            )
        )

        response = self.post_story(editor)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Story.objects.filter(title="Rona and the Moon").exists())
        self.assertFalse(BlankLink.objects.exists())
