"""Coverage for exporting the database as a content package."""

import io
import tempfile
import tomllib
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from .content import dump_toml, toml_string
from .models import (
    AppConfig,
    BackgroundMusic,
    BlankLink,
    Paragraph,
    Story,
    StoryPicture,
    Word,
)


class TomlTests(SimpleTestCase):
    def test_strings_read_back_unchanged(self):
        for value in [
            "",
            "Rona's “moon”",
            'quote " and backslash \\ and """ three',
            "tab\tnew line\nreturn\r",
            "control \x00 \x08 \x1f delete \x7f C1 \x80 \x85 \x9f",
            "kōrero paki, Träumerei, 夢幻曲, 🌕",
        ]:
            with self.subTest(value=value):
                self.assertEqual(tomllib.loads(f"v = {toml_string(value)}")["v"], value)

    def test_c1_controls_are_escaped(self):
        self.assertEqual(toml_string("a\x85b"), '"a\\u0085b"')

    def test_empty_collections_are_written(self):
        document = {"title": "Empty", "paragraphs": [], "pictures": {}}
        self.assertEqual(tomllib.loads(dump_toml(document)), document)

    def test_documents_read_back_unchanged(self):
        document = {
            "title": "Rona and the Moon",
            "count": 3,
            "words": {"moon": {"maori": "marama"}, "a b": {"english": "x"}},
            "paragraphs": [{"order": 2, "text": "{{moon}}"}, {"text": "Two"}],
        }
        self.assertEqual(tomllib.loads(dump_toml(document)), document)

    def test_unsupported_values_are_refused(self):
        for value in [True, 1.5, None]:
            with self.subTest(value=value), self.assertRaises(TypeError):
                dump_toml({"value": value})


class ExportContentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.picture = StoryPicture(title="Rona and the Moon", image_file="pic/r.jpg")
        cls.picture.save(skip_compression=True)
        cls.humoresque = BackgroundMusic.objects.create(
            title="Humoresque", audio_file="bgm/humoresque.m4a"
        )
        cls.traumerei = BackgroundMusic.objects.create(
            title="Träumerei_MID", audio_file="bgm/traumerei.mp3"
        )
        AppConfig.objects.create(menu_bgm=cls.traumerei)
        cls.moon = cls.word("marama", "moon", image="word_images/moon.jpg")
        cls.light = cls.word("rama", "light", maori_audio="word_audio_maori/rama.mp3")
        cls.glow = cls.word("māramatanga", "light")
        cls.story = Story.objects.create(
            title="Rona and the Moon",
            story_picture=cls.picture,
            background_music=cls.humoresque,
        )

    @staticmethod
    def word(maori, english, **media):
        word = Word(maori_word=maori, english_translation=english, **media)
        word.save(skip_compression=True)
        return word

    def paragraph(self, order, text, links, audio=None):
        paragraph = Paragraph.objects.create(
            story=self.story, order=order, text=text, audio=audio
        )
        for placeholder, word in links.items():
            BlankLink.objects.create(
                paragraph=paragraph, placeholder=placeholder, word=word
            )
        return paragraph

    def export(self, directory, **options):
        call_command(
            "export_content", output=directory, stdout=io.StringIO(), **options
        )
        return {
            path.relative_to(directory).as_posix(): tomllib.loads(
                path.read_text(encoding="utf-8")
            )
            for path in Path(directory).rglob("*.toml")
        }

    def test_exports_library_words_and_stories(self):
        self.paragraph(
            0,
            "The __BLANK_moon__ gave __BLANK_light__.",
            {"__BLANK_moon__": self.moon, "__BLANK_light__": self.light},
            audio="paragraph_audio/one.ogg",
        )
        self.paragraph(5, "A soft __BLANK_light__.", {"__BLANK_light__": self.glow})

        with tempfile.TemporaryDirectory() as directory:
            files = self.export(directory)

        self.assertEqual(
            sorted(files),
            ["library.toml", "stories/rona-and-the-moon/story.toml", "words.toml"],
        )
        self.assertEqual(
            files["library.toml"],
            {
                "menu_music": "traumerei_mid",
                "pictures": {
                    "rona-and-the-moon": {
                        "title": "Rona and the Moon",
                        "image": "pic/r.jpg",
                    }
                },
                "music": {
                    "humoresque": {
                        "title": "Humoresque",
                        "audio": "bgm/humoresque.m4a",
                    },
                    "traumerei_mid": {
                        "title": "Träumerei_MID",
                        "audio": "bgm/traumerei.mp3",
                    },
                },
            },
        )
        self.assertEqual(
            files["words.toml"]["words"],
            {
                "moon": {
                    "maori": "marama",
                    "english": "moon",
                    "image": "word_images/moon.jpg",
                },
                "light": {
                    "maori": "rama",
                    "english": "light",
                    "maori_audio": "word_audio_maori/rama.mp3",
                },
                "light_2": {"maori": "māramatanga", "english": "light"},
            },
        )
        self.assertEqual(
            files["stories/rona-and-the-moon/story.toml"],
            {
                "title": "Rona and the Moon",
                "picture": "rona-and-the-moon",
                "music": "humoresque",
                "paragraphs": [
                    {
                        "text": "The {{moon}} gave {{light}}.",
                        "audio": "paragraph_audio/one.ogg",
                    },
                    {"order": 5, "text": "A soft {{light|light_2}}."},
                ],
            },
        )

    def test_content_that_cannot_be_written_exactly_is_refused(self):
        self.paragraph(0, "No link for __BLANK_moon__.", {})
        self.paragraph(1, "No word for __BLANK_sky__.", {"__BLANK_sky__": None})
        self.paragraph(2, "Stale link.", {"__BLANK_tale__": self.moon})
        self.paragraph(3, "Braces {{ here }}.", {})

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(CommandError) as raised:
                self.export(directory)
            self.assertEqual(list(Path(directory).iterdir()), [])

        message = str(raised.exception)
        for expected in [
            "paragraph 0: __BLANK_moon__ has no Blank Link",
            "paragraph 1: __BLANK_sky__ is linked to no word",
            "paragraph 2: Blank Link __BLANK_tale__ is not in the text",
            "paragraph 3: the text contains {{ or }}",
        ]:
            self.assertIn(expected, message)

    def test_more_than_one_configuration_is_refused(self):
        AppConfig.objects.bulk_create([AppConfig(menu_bgm=self.humoresque)])

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(CommandError) as raised:
                self.export(directory)

        self.assertIn("2 application configurations exist", str(raised.exception))

    def test_control_characters_in_diagnostics_are_escaped(self):
        self.story.title = "Rona\x1b[31m"
        self.story.save()
        self.paragraph(0, "No link for __BLANK_moon__.", {})

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(CommandError) as raised:
                self.export(directory)

        self.assertNotIn("\x1b", str(raised.exception))
        self.assertIn('"Rona\\u001b[31m" paragraph 0', str(raised.exception))

    def test_a_failed_write_leaves_no_files(self):
        real = tempfile.NamedTemporaryFile
        calls = []

        def fail_on_second(*args, **kwargs):
            calls.append(args)
            if len(calls) == 2:
                raise OSError("disk full")
            return real(*args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch("core.content.tempfile.NamedTemporaryFile", fail_on_second),
                self.assertRaises(OSError),
            ):
                self.export(directory)
            self.assertEqual(
                [path for path in Path(directory).rglob("*") if path.is_file()], []
            )

    def test_existing_files_are_kept_unless_overwrite_is_given(self):
        with tempfile.TemporaryDirectory() as directory:
            self.export(directory)
            words = Path(directory, "words.toml")
            words.write_text("edited\n", encoding="utf-8")

            with self.assertRaises(CommandError):
                self.export(directory)
            self.assertEqual(words.read_text(encoding="utf-8"), "edited\n")

            self.export(directory, overwrite=True)
            self.assertIn("[words.moon]", words.read_text(encoding="utf-8"))


class ExportOutsideTransactionTests(TransactionTestCase):
    """Run the export as the command does, outside any open transaction."""

    def test_exports_from_a_consistent_read_only_snapshot(self):
        word = Word(maori_word="marama", english_translation="moon")
        word.save(skip_compression=True)

        with tempfile.TemporaryDirectory() as directory:
            call_command("export_content", output=directory, stdout=io.StringIO())
            words = tomllib.loads(Path(directory, "words.toml").read_text("utf-8"))

        self.assertEqual(
            words, {"words": {"moon": {"maori": "marama", "english": "moon"}}}
        )
