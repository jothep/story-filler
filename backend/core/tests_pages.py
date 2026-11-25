"""Coverage for turning a whole pasted story into pages."""

import shutil
import tempfile
import time
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .blanks import expand_inline_blanks
from .models import BlankLink, Language, Paragraph, Story, Word, WordForm
from .pages import apply_pages, page_length, sentences_in, split_pages, story_text

LIVE_PAGES = [
    "Long ago, in Aotearoa, there lived a woman named Rona. She was quick with "
    "her words, and her anger was well-known in the __BLANK_village__. Her "
    "husband often sighed, “Rona, your tongue is sharper than a "
    "__BLANK_shark__'s tooth.”",
    "One night, he asked, “I am thirsty. Fetch me __BLANK_water__, please.” "
    "Rona grumbled but took her calabash and stomped into the dark.",
    "The __BLANK_wind__ carried her insult upward—right into the ears of the "
    "Moon-God. The Moon-God descended in a beam of silver __BLANK_light__.",
]


class SplitPagesTests(SimpleTestCase):
    def test_blank_lines_separate_pages_and_whitespace_is_tidied(self):
        text = "First  page\nstill first.\r\n\r\n\r\nSecond page.\n \n"

        self.assertEqual(split_pages(text), ["First page still first.", "Second page."])

    def test_long_pages_are_split_at_sentence_ends(self):
        sentence = "The moon rose over the quiet hills tonight."
        text = " ".join([sentence] * 8)

        pages = split_pages(text, limit=100)

        self.assertEqual(pages, [f"{sentence} {sentence}"] * 4)
        self.assertTrue(all(page_length(page) <= 100 for page in pages))

    def test_a_sentence_longer_than_the_limit_stays_whole(self):
        sentence = "word " * 30 + "end."

        self.assertEqual(split_pages(sentence, limit=50), [" ".join(sentence.split())])

    def test_sentences_end_at_punctuation_followed_by_space(self):
        self.assertEqual(
            sentences_in("A b. C d! He said “Go.” Then left… 3.14 is pi"),
            ["A b.", "C d!", "He said “Go.”", "Then left…", "3.14 is pi"],
        )

    def test_other_scripts_and_abbreviations(self):
        self.assertEqual(
            sentences_in("我喜欢月亮。它很亮！真的吗？好"),
            ["我喜欢月亮。", "它很亮！", "真的吗？", "好"],
        )
        self.assertEqual(sentences_in("هل ترى؟ نعم."), ["هل ترى؟", "نعم."])
        self.assertEqual(
            sentences_in("Mr. Smith met Dr. Rona, e.g. at night. Then left."),
            ["Mr. Smith met Dr. Rona, e.g. at night.", "Then left."],
        )

    def test_wide_characters_count_twice(self):
        self.assertEqual(page_length("月亮 moon"), 9)

    def test_long_runs_of_punctuation_or_newlines_stay_fast(self):
        started = time.perf_counter()
        sentences_in("!" * 200_000 + "a")
        split_pages("\n" * 200_000 + "a" + " b." * 1000)
        self.assertLess(time.perf_counter() - started, 2)

    def test_blanks_count_as_a_fixed_width(self):
        self.assertEqual(page_length("a __BLANK_village__ b"), 14)

    def test_the_live_pages_survive_a_round_trip(self):
        text = "\n\n".join(LIVE_PAGES).replace("__BLANK_", "{{").replace("__", "}}")
        self.assertEqual(split_pages(expand_inline_blanks(text)), LIVE_PAGES)


class ApplyPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.story = Story.objects.create(title="Rona and the Moon")

    def page(self, order, text, audio=None):
        return Paragraph.objects.create(
            story=self.story, order=order, text=text, audio=audio
        )

    def test_pages_keep_audio_by_position_and_report_what_to_check(self):
        first = self.page(0, "One.", audio="paragraph_audio/1.ogg")
        second = self.page(1, "Two.", audio="paragraph_audio/2.ogg")
        self.page(2, "Three.", audio="paragraph_audio/3.ogg")

        changed, removed = apply_pages(self.story, ["One.", "Two, changed."])

        self.assertEqual((changed, removed), ([2], [3]))
        self.assertEqual(
            list(self.story.paragraphs.values_list("order", "text", "audio")),
            [
                (0, "One.", "paragraph_audio/1.ogg"),
                (1, "Two, changed.", "paragraph_audio/2.ogg"),
            ],
        )
        self.assertEqual(
            [first.pk, second.pk],
            list(self.story.paragraphs.values_list("pk", flat=True)),
        )

    def test_new_pages_are_added_without_audio(self):
        self.page(0, "One.")

        self.assertEqual(apply_pages(self.story, ["One.", "Two."]), ([], []))
        self.assertEqual(
            list(self.story.paragraphs.values_list("order", "text", "audio")),
            [(0, "One.", ""), (1, "Two.", "")],
        )

    def test_story_text_writes_blanks_inline(self):
        self.page(1, "A __BLANK_moon__.")
        self.page(0, "First.")

        self.assertEqual(story_text(self.story), "First.\n\nA {{moon}}.")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class WholeStoryAdminTests(TestCase):
    def setUp(self):
        # Saving validates the stored narration's size, so the file must exist.
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        Path(media, "paragraph_audio").mkdir()
        Path(media, "paragraph_audio", "1.ogg").write_bytes(b"OggS")
        settings = override_settings(MEDIA_ROOT=media)
        settings.enable()
        self.addCleanup(settings.disable)

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="story-editor", email="editor@example.invalid", password=None
        )
        english = Language.objects.get(code="en")
        maori = Language.objects.get(code="mi")
        cls.story = Story.objects.create(
            title="Rona and the Moon", language=english, learning_language=maori
        )
        Paragraph.objects.create(
            story=cls.story, order=0, text="Old page.", audio="paragraph_audio/1.ogg"
        )
        moon = Word.objects.create(key="moon")
        WordForm.objects.create(word=moon, language=maori, text="marama")

    def save(self, user, text, version="", page_text=None):
        """Save the story with ``text`` in the whole-story box.

        ``page_text`` also changes the first page in its page form.
        """
        self.client.force_login(user)
        data = {
            "story_text_version": version,
            "title": self.story.title,
            "language": self.story.language_id,
            "learning_language": self.story.learning_language_id,
            "status": "draft",
            "story_picture": "",
            "background_music": "",
            "story_text": text,
            "paragraphs-MIN_NUM_FORMS": "0",
            "paragraphs-MAX_NUM_FORMS": "1000",
            "_save": "Save",
        }
        paragraphs = list(self.story.paragraphs.order_by("order"))
        data["paragraphs-TOTAL_FORMS"] = str(len(paragraphs))
        data["paragraphs-INITIAL_FORMS"] = str(len(paragraphs))
        for index, paragraph in enumerate(paragraphs):
            data[f"paragraphs-{index}-id"] = paragraph.pk
            data[f"paragraphs-{index}-story"] = self.story.pk
            data[f"paragraphs-{index}-order"] = paragraph.order
            data[f"paragraphs-{index}-text"] = (
                page_text if page_text is not None and index == 0 else paragraph.text
            )
        return self.client.post(
            reverse("admin:core_story_change", args=[self.story.pk]), data
        )

    def messages(self, response, level):
        return [
            str(message)
            for message in get_messages(response.wsgi_request)
            if message.level == level
        ]

    def pages(self):
        return list(self.story.paragraphs.values_list("text", "audio"))

    def test_the_whole_story_replaces_the_pages_and_links_blanks(self):
        response = self.save(
            self.admin_user, "The {{moon}} rose.\r\n\r\nRona was angry."
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.pages(),
            [
                ("The __BLANK_moon__ rose.", "paragraph_audio/1.ogg"),
                ("Rona was angry.", ""),
            ],
        )
        self.assertEqual(BlankLink.objects.get().word.key, "moon")
        self.assertIn(
            "The story now has 2 pages.", self.messages(response, messages.INFO)
        )
        self.assertTrue(
            any("pages 1" in note for note in self.messages(response, messages.WARNING))
        )

    def test_an_unchanged_or_empty_box_changes_nothing(self):
        for text in ("Old page.\r\n", ""):
            with self.subTest(text=text):
                response = self.save(self.admin_user, text)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(self.pages(), [("Old page.", "paragraph_audio/1.ogg")])

    def test_editors_who_may_not_replace_pages_are_told(self):
        editor = get_user_model().objects.create_user(
            username="title-editor", is_staff=True
        )
        editor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="core",
                codename__in=["change_story", "view_story", "view_paragraph"],
            )
        )

        response = self.save(editor, "Something new.")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.pages(), [("Old page.", "paragraph_audio/1.ogg")])
        self.assertTrue(
            any(
                "was not applied" in note
                for note in self.messages(response, messages.WARNING)
            )
        )

    def test_the_box_shows_the_current_pages_with_inline_blanks(self):
        Paragraph.objects.create(story=self.story, order=1, text="A __BLANK_moon__.")
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("admin:core_story_change", args=[self.story.pk])
        )

        self.assertContains(response, "Old page.\n\nA {{moon}}.")

    def test_a_save_from_an_older_tab_is_refused(self):
        self.client.force_login(self.admin_user)
        page = self.client.get(reverse("admin:core_story_change", args=[self.story.pk]))
        version = page.context["adminform"].form["story_text_version"].value()
        Paragraph.objects.filter(story=self.story).update(text="Changed elsewhere.")

        response = self.save(self.admin_user, "My older text.", version=version)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The pages changed after this page was opened")
        self.assertEqual(
            self.pages(), [("Changed elsewhere.", "paragraph_audio/1.ogg")]
        )

    def test_the_box_is_not_applied_with_page_form_edits(self):
        response = self.save(
            self.admin_user, "A whole new story.", page_text="Edited in its form."
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.pages(), [("Edited in its form.", "paragraph_audio/1.ogg")]
        )
        self.assertTrue(
            any(
                "was not applied because pages were also edited" in note
                for note in self.messages(response, messages.WARNING)
            )
        )

    def test_stored_line_breaks_do_not_count_as_a_change(self):
        Paragraph.objects.filter(story=self.story).update(text="Old\r\npage.")

        response = self.save(self.admin_user, "Old\r\npage.\r\n")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.pages(), [("Old\r\npage.", "paragraph_audio/1.ogg")])
