"""Coverage for uploading many word and narration files at once."""

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Language, Paragraph, Story, Word, WordForm
from .uploads import page_number


def picture(name):
    buffer = BytesIO()
    Image.new("RGB", (1200, 900), "navy").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def audio(name):
    return SimpleUploadedFile(name, b"ID3 fake mp3 data", content_type="audio/mpeg")


class UploadTestCase(TestCase):
    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        storage = override_settings(
            MEDIA_ROOT=media,
            STORAGES={
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            },
        )
        storage.enable()
        self.addCleanup(storage.disable)

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="media-editor", email="editor@example.invalid", password=None
        )
        cls.english = Language.objects.get(code="en")
        cls.maori = Language.objects.get(code="mi")
        Language.objects.create(code="zh-Hans", name="中文")

    def upload(self, url, files, user=None):
        self.client.force_login(user or self.admin_user)
        return self.client.post(url, {"files": files})


class WordUploadTests(UploadTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.moon = Word.objects.create(key="moon")
        WordForm.objects.create(word=cls.moon, language=cls.maori, text="marama")
        WordForm.objects.create(word=cls.moon, language=cls.english, text="moon")
        cls.sky = Word.objects.create(key="sky")
        WordForm.objects.create(word=cls.sky, language=cls.english, text="sky")
        cls.url = reverse("admin:core_word_upload")

    def test_files_are_matched_by_key_and_language_and_the_rest_explained(self):
        response = self.upload(
            self.url,
            [
                picture("moon.jpg"),
                audio("MOON.MI.MP3"),
                audio("moon.en.mp3"),
                audio("moon.mi.ogg"),
                audio("star.mi.mp3"),
                audio("moon.fr.mp3"),
                audio("sky.mi.mp3"),
                audio("notes.txt"),
            ],
        )

        self.assertEqual(response.status_code, 200)
        report = response.context["report"]
        self.assertEqual(
            report.saved,
            [
                "moon.jpg: picture of moon",
                "MOON.MI.MP3: Māori audio of moon",
                "moon.en.mp3: English audio of moon",
            ],
        )
        self.assertEqual(len(report.skipped), 5)
        for expected in (
            "moon.mi.ogg: audio must be MP3",
            "star.mi.mp3: no word has the key star",
            "moon.fr.mp3: no language has the code fr",
            "sky.mi.mp3: sky has no Māori form yet",
            "notes.txt: name it <key>.jpg",
        ):
            self.assertTrue(
                any(line.startswith(expected) for line in report.skipped), expected
            )
        self.moon.refresh_from_db()
        self.assertTrue(self.moon.image.name.startswith("word_images/moon"))
        with Image.open(self.moon.image.path) as stored:
            self.assertLessEqual(max(stored.size), 800)
        forms = {form.language.code: form.audio.name for form in self.moon.forms.all()}
        self.assertTrue(forms["mi"].startswith("word_audio/moon.mi"))
        self.assertTrue(forms["en"].startswith("word_audio/moon.en"))

    def test_two_files_for_one_target_keep_the_first(self):
        report = self.upload(
            self.url, [audio("moon.mi.mp3"), audio("Moon.mi.mp3")]
        ).context["report"]

        self.assertEqual(len(report.saved), 1)
        self.assertIn("same target", report.skipped[0])

    def test_the_word_list_links_to_the_upload_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:core_word_changelist"))

        self.assertContains(response, self.url)

    def test_editors_who_may_not_change_word_forms_are_refused(self):
        editor = get_user_model().objects.create_user(
            username="word-viewer", is_staff=True
        )
        editor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="core",
                codename__in=["change_word", "view_word"],
            )
        )

        response = self.upload(self.url, [audio("moon.mi.mp3")], user=editor)

        self.assertEqual(response.status_code, 403)


class PageNumberTests(SimpleTestCase):
    def test_names_ending_in_a_page_number(self):
        cases = {
            "page-01.mp3": 1,
            "page03.mp3": 3,
            "PAGE_4.mp3": 4,
            "12.mp3": 12,
            "Rona_moon_05.mp3": 5,
            "rona moon 6.mp3": 6,
            "take2.mp3": None,
            "page-0.mp3": None,
            "page-12345.mp3": None,
            "page-01.ogg": None,
            "moon.mi.mp3": None,
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(page_number(audio(name)), expected)


class NarrationUploadTests(UploadTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.story = Story.objects.create(
            title="Rona and the Moon", language=cls.english, learning_language=cls.maori
        )
        for order in (5, 6, 7):
            Paragraph.objects.create(
                story=cls.story, order=order, text=f"Page {order}."
            )
        cls.url = reverse("admin:core_story_narration", args=[cls.story.pk])

    def test_files_are_matched_to_pages_by_number(self):
        report = self.upload(
            self.url,
            [
                audio("page-01.mp3"),
                audio("2.mp3"),
                audio("page_02.mp3"),
                audio("page-09.mp3"),
                audio("page-3.ogg"),
                audio("intro.mp3"),
                audio("take3.mp3"),
                audio("Rona_moon_03.mp3"),
            ],
        ).context["report"]

        self.assertEqual(
            report.saved,
            ["page-01.mp3: page 1", "2.mp3: page 2", "Rona_moon_03.mp3: page 3"],
        )
        for expected in (
            "page_02.mp3: another file in this upload is for page 2",
            "page-09.mp3: the story has 3 pages",
            "page-3.ogg: narration must be MP3",
            "intro.mp3: end the name with its page number",
            "take3.mp3: end the name with its page number",
        ):
            self.assertTrue(
                any(line.startswith(expected) for line in report.skipped), expected
            )
        audio_names = list(self.story.paragraphs.values_list("audio", flat=True))
        self.assertTrue(
            audio_names[0].startswith("paragraph_audio/rona-and-the-moon-page-01")
        )
        self.assertTrue(
            audio_names[1].startswith("paragraph_audio/rona-and-the-moon-page-02")
        )
        self.assertTrue(
            audio_names[2].startswith("paragraph_audio/rona-and-the-moon-page-03")
        )

    def test_the_story_page_links_to_the_upload_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("admin:core_story_change", args=[self.story.pk])
        )

        self.assertContains(response, self.url)
        self.assertContains(response, "Upload narration")
