"""Coverage for linking paragraph placeholders to words in the bank."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .blanks import (
    build_word_index,
    expand_inline_blanks,
    link_placeholders,
    placeholder_key,
    remove_stale_links,
    placeholders_in,
)
from .models import BlankLink, Language, Paragraph, Story, Word, WordForm


def make_word(key, **forms):
    """Create a word entry with a form per language code, such as mi="marama"."""
    word = Word.objects.create(key=key)
    for code, text in forms.items():
        WordForm.objects.create(
            word=word, language=Language.objects.get(code=code), text=text
        )
    return word


class PlaceholderKeyTests(TestCase):
    def test_keys_are_lowercase_ascii_with_underscores(self):
        self.assertEqual(placeholder_key("Moon"), "moon")
        self.assertEqual(placeholder_key("kōrero paki"), "korero_paki")
        self.assertEqual(placeholder_key("  Kāinga! "), "kainga")

    def test_placeholders_are_distinct_and_ordered(self):
        text = "__BLANK_moon__ and __BLANK_tale__, then __BLANK_moon__ again"
        self.assertEqual(placeholders_in(text), ["__BLANK_moon__", "__BLANK_tale__"])


class InlineBlankTests(SimpleTestCase):
    def test_inline_blanks_become_placeholders(self):
        self.assertEqual(
            expand_inline_blanks("The {{moon}} told a {{ Kōrero Paki }}."),
            "The __BLANK_moon__ told a __BLANK_korero_paki__.",
        )
        self.assertEqual(
            expand_inline_blanks("Kept: __BLANK_sky__."), "Kept: __BLANK_sky__."
        )

    def test_braces_that_are_not_blanks_are_refused(self):
        for text in ("Empty {{}}.", "Open {{moon.", "Close moon}}.", "{{!}}"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                expand_inline_blanks(text)


class RemoveStaleLinksTests(TestCase):
    def test_only_links_that_are_not_parsed_blanks_are_removed(self):
        story = Story.objects.create(title="Rona and the Moon")
        moon = make_word("moon", mi="marama")
        paragraph = Paragraph.objects.create(
            story=story, order=0, text="The __BLANK_moon__ and __BLANK_moon__x__."
        )
        for placeholder in ("__BLANK_moon__", "__BLANK_moon__x__", "__BLANK_sky__"):
            BlankLink.objects.create(
                paragraph=paragraph, placeholder=placeholder, word=moon
            )

        removed = remove_stale_links(paragraph)

        self.assertEqual(sorted(removed), ["__BLANK_sky__"])
        self.assertEqual(
            sorted(paragraph.blank_links.values_list("placeholder", flat=True)),
            ["__BLANK_moon__", "__BLANK_moon__x__"],
        )

    def test_the_saved_text_decides_not_a_stale_copy(self):
        story = Story.objects.create(title="Rona and the Moon")
        moon = make_word("moon", mi="marama")
        paragraph = Paragraph.objects.create(story=story, order=0, text="No blank.")
        BlankLink.objects.create(
            paragraph=paragraph, placeholder="__BLANK_moon__", word=moon
        )
        Paragraph.objects.filter(pk=paragraph.pk).update(text="The __BLANK_moon__.")

        self.assertEqual(remove_stale_links(paragraph), [])
        self.assertTrue(paragraph.blank_links.exists())


class LinkPlaceholdersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.story = Story.objects.create(title="Rona and the Moon")
        cls.moon = make_word("moon", mi="marama", en="moon")
        cls.tale = make_word("tale", mi="kōrero paki", en="tale")

    def paragraph(self, text):
        return Paragraph.objects.create(story=self.story, order=1, text=text)

    def links(self, paragraph):
        return dict(paragraph.blank_links.values_list("placeholder", "word__key"))

    def test_links_by_key_or_form_text_and_reports_the_rest(self):
        paragraph = self.paragraph(
            "The __BLANK_moon__ told a __BLANK_korero_paki__ about the "
            "__BLANK_sky__ and the __BLANK_moon__."
        )

        unlinked = link_placeholders(paragraph)

        self.assertEqual(unlinked, ["__BLANK_sky__"])
        self.assertEqual(
            self.links(paragraph),
            {"__BLANK_moon__": "moon", "__BLANK_korero_paki__": "tale"},
        )

    def test_existing_links_are_kept(self):
        paragraph = self.paragraph("The __BLANK_moon__ rose.")
        BlankLink.objects.create(
            paragraph=paragraph, placeholder="__BLANK_moon__", word=self.tale
        )

        self.assertEqual(link_placeholders(paragraph), [])
        self.assertEqual(self.links(paragraph), {"__BLANK_moon__": "tale"})

    def test_a_key_wins_over_form_text(self):
        make_word("glow", en="moon")
        paragraph = self.paragraph("The __BLANK_moon__ rose.")

        self.assertEqual(link_placeholders(paragraph), [])
        self.assertEqual(self.links(paragraph), {"__BLANK_moon__": "moon"})

    def test_ambiguous_keys_are_not_linked(self):
        make_word("lamp", en="light", mi="rama")
        make_word("glow", en="light", mi="māramatanga")
        paragraph = self.paragraph("A __BLANK_light__ shone.")

        self.assertEqual(
            link_placeholders(paragraph, build_word_index()), ["__BLANK_light__"]
        )
        self.assertEqual(self.links(paragraph), {})

    def test_links_without_a_word_long_placeholders_and_deleted_words_are_reported(
        self,
    ):
        long_key = "x" * 50
        # Keys fit a placeholder, but a match on form text can be too long.
        make_word("roa", mi="roa", en=long_key)
        sky = make_word("sky", mi="rangi")
        paragraph = self.paragraph(f"__BLANK_moon__ __BLANK_{long_key}__ __BLANK_sky__")
        BlankLink.objects.create(
            paragraph=paragraph, placeholder="__BLANK_moon__", word=None
        )
        index = build_word_index()
        sky.delete()

        self.assertEqual(
            link_placeholders(paragraph, index),
            ["__BLANK_moon__", f"__BLANK_{long_key}__", "__BLANK_sky__"],
        )
        self.assertEqual(self.links(paragraph), {"__BLANK_moon__": None})


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
        make_word("moon", mi="marama", en="moon")

    def post_story(self, user, text="The __BLANK_moon__ lit the __BLANK_sky__."):
        self.client.force_login(user)
        return self.client.post(
            reverse("admin:core_story_add"),
            {
                "title": "Rona and the Moon",
                "language": Language.objects.get(code="en").pk,
                "learning_language": Language.objects.get(code="mi").pk,
                "story_picture": "",
                "background_music": "",
                "paragraphs-TOTAL_FORMS": "1",
                "paragraphs-INITIAL_FORMS": "0",
                "paragraphs-MIN_NUM_FORMS": "0",
                "paragraphs-MAX_NUM_FORMS": "1000",
                "paragraphs-0-id": "",
                "paragraphs-0-story": "",
                "paragraphs-0-order": "1",
                "paragraphs-0-text": text,
                "_save": "Save",
            },
        )

    def edit_paragraph(self, user, story, text):
        """Save the story's only paragraph with new text."""
        paragraph = story.paragraphs.get()
        self.client.force_login(user)
        return self.client.post(
            reverse("admin:core_story_change", args=[story.pk]),
            {
                "title": story.title,
                "language": story.language_id,
                "learning_language": story.learning_language_id,
                "story_picture": "",
                "background_music": "",
                "paragraphs-TOTAL_FORMS": "1",
                "paragraphs-INITIAL_FORMS": "1",
                "paragraphs-MIN_NUM_FORMS": "0",
                "paragraphs-MAX_NUM_FORMS": "1000",
                "paragraphs-0-id": paragraph.pk,
                "paragraphs-0-story": story.pk,
                "paragraphs-0-order": paragraph.order,
                "paragraphs-0-text": text,
                "_save": "Save",
            },
        )

    def test_inline_blanks_are_stored_as_placeholders_and_linked(self):
        response = self.post_story(self.admin_user, text="The {{ Moon }} rose.")

        self.assertEqual(response.status_code, 302)
        story = Story.objects.get()
        self.assertEqual(story.paragraphs.get().text, "The __BLANK_moon__ rose.")
        self.assertEqual(BlankLink.objects.get().word.key, "moon")

    def test_unclosed_inline_blanks_are_refused(self):
        response = self.post_story(self.admin_user, text="The {{moon rose.")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Write each blank as {{key}}")
        self.assertFalse(Story.objects.exists())

    def test_links_for_removed_blanks_are_deleted(self):
        self.post_story(self.admin_user, text="The {{moon}} rose.")
        story = Story.objects.get()

        response = self.edit_paragraph(self.admin_user, story, "The sun rose.")

        self.assertEqual(response.status_code, 302)
        self.assertFalse(BlankLink.objects.exists())
        infos = [
            str(message)
            for message in get_messages(response.wsgi_request)
            if message.level == messages.INFO
        ]
        self.assertTrue(any("__BLANK_moon__" in message for message in infos))

    def test_editors_who_may_not_delete_links_keep_them(self):
        self.post_story(self.admin_user, text="The {{moon}} rose.")
        story = Story.objects.get()
        editor = get_user_model().objects.create_user(
            username="page-editor", is_staff=True
        )
        editor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="core",
                codename__in=[
                    "change_story",
                    "view_story",
                    "add_paragraph",
                    "change_paragraph",
                    "view_paragraph",
                    "add_blanklink",
                ],
            )
        )

        response = self.edit_paragraph(editor, story, "The sun rose.")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(BlankLink.objects.get().placeholder, "__BLANK_moon__")

    def test_saving_a_story_links_placeholders_and_warns_about_the_rest(self):
        response = self.post_story(self.admin_user)

        self.assertEqual(response.status_code, 302)
        link = BlankLink.objects.get()
        self.assertEqual(link.placeholder, "__BLANK_moon__")
        self.assertEqual(link.word.key, "moon")
        warnings = [
            str(message)
            for message in get_messages(response.wsgi_request)
            if message.level == messages.WARNING
        ]
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
