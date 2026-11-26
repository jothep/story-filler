"""Coverage for the upload_narration and upload_word_files commands."""

import io
import shutil
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .models import Language, Paragraph, Story, Word, WordForm


class UploadCommandTests(TestCase):
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
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)

    @classmethod
    def setUpTestData(cls):
        english = Language.objects.get(code="en")
        maori = Language.objects.get(code="mi")
        cls.story = Story.objects.create(
            title="Rona and the Moon", language=english, learning_language=maori
        )
        for order in range(3):
            Paragraph.objects.create(
                story=cls.story,
                order=order,
                text=f"Page {order}.",
                audio=f"paragraph_audio/Rona_moon_0{order + 1}.ogg",
            )
        cls.moon = Word.objects.create(key="moon")
        WordForm.objects.create(word=cls.moon, language=maori, text="marama")

    def write(self, *names):
        for name in names:
            (self.folder / name).write_bytes(b"ID3 fake mp3 data")

    def call(self, *args):
        out = io.StringIO()
        call_command(*args, stdout=out)
        return out.getvalue()

    def audio_names(self):
        return list(self.story.paragraphs.values_list("audio", flat=True))

    def test_a_dry_run_shows_the_matches_and_saves_nothing(self):
        self.write("Rona_moon_01.mp3", "Rona_moon_02.mp3", ".DS_Store")
        before = self.audio_names()

        out = self.call(
            "upload_narration", "Rona and the Moon", self.folder, "--dry-run"
        )

        self.assertIn("Story: Rona and the Moon (id", out)
        self.assertIn("Storage: FileSystemStorage", out)
        self.assertIn("PLAN Rona_moon_01.mp3: would be page 1", out)
        self.assertIn("PLAN Rona_moon_02.mp3: would be page 2", out)
        self.assertIn("2 would be saved, 0 skipped.", out)
        self.assertNotIn("DS_Store", out)
        self.assertEqual(self.audio_names(), before)

    def test_narration_is_saved_and_the_replaced_files_are_named(self):
        self.write("Rona_moon_01.mp3", "Rona_moon_03.mp3")

        out = self.call("upload_narration", str(self.story.pk), self.folder)

        self.assertIn(
            "SAVED Rona_moon_01.mp3: page 1 "
            "(replaced paragraph_audio/Rona_moon_01.ogg)",
            out,
        )
        names = self.audio_names()
        self.assertTrue(
            names[0].startswith("paragraph_audio/rona-and-the-moon-page-01")
        )
        self.assertEqual(names[1], "paragraph_audio/Rona_moon_02.ogg")
        self.assertTrue(
            names[2].startswith("paragraph_audio/rona-and-the-moon-page-03")
        )

    def test_skipped_files_make_the_command_fail_after_saving_the_rest(self):
        self.write("Rona_moon_01.mp3", "take2.mp3")

        with self.assertRaises(CommandError) as raised:
            self.call("upload_narration", "rona and the moon", self.folder)

        self.assertIn("1 files were not saved", str(raised.exception))
        self.assertTrue(self.audio_names()[0].startswith("paragraph_audio/rona-and"))

    def test_unknown_stories_and_paths_are_refused(self):
        with self.assertRaises(CommandError):
            self.call("upload_narration", "No such story", self.folder)
        with self.assertRaises(CommandError):
            self.call("upload_narration", "Rona and the Moon", self.folder / "missing")

    def test_word_files_are_saved_by_key_and_language(self):
        self.write("moon.mi.mp3")

        out = self.call("upload_word_files", self.folder / "moon.mi.mp3")

        self.assertIn("SAVED moon.mi.mp3: Māori audio of moon", out)
        form = self.moon.forms.get()
        self.assertTrue(form.audio.name.startswith("word_audio/moon.mi"))
