"""Offline tests for the local audio conversion helper (ffmpeg is mocked)."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import convert_audio


def options(**overrides):
    values = {
        "output": None,
        "speech": False,
        "loudness": False,
        "trim": False,
        "overwrite": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class ConvertAudioTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)
        for name in ("moon.mi.ogg", "page-01.WAV", "notes.txt", "-odd.ogg"):
            (self.folder / name).write_bytes(b"audio")

    def run_main(self, *args, ffmpeg_ok=True):
        def fake_run(command, **kwargs):
            if ffmpeg_ok:
                Path(command[-1]).write_bytes(b"mp3")
            return SimpleNamespace(returncode=0 if ffmpeg_ok else 1, stderr="bad input")

        out = io.StringIO()
        with (
            patch.object(convert_audio.shutil, "which", return_value="/usr/bin/ffmpeg"),
            patch.object(convert_audio.subprocess, "run", side_effect=fake_run) as run,
            redirect_stdout(out),
            redirect_stderr(io.StringIO()),
        ):
            code = convert_audio.main([*map(str, args)])
        return code, run, out.getvalue()

    def test_folders_give_their_audio_files_with_names_kept(self):
        sources = convert_audio.find_inputs([self.folder])

        self.assertEqual(
            [source.name for source in sources],
            ["-odd.ogg", "moon.mi.ogg", "page-01.WAV"],
        )
        self.assertEqual(
            convert_audio.output_path(self.folder / "moon.mi.ogg").name, "moon.mi.mp3"
        )

    def test_a_path_that_is_not_audio_is_refused(self):
        with redirect_stderr(io.StringIO()):
            code = convert_audio.main([str(self.folder / "notes.txt")])

        self.assertEqual(code, 2)

    def test_the_command_uses_absolute_paths_and_drops_metadata(self):
        source = self.folder / "-odd.ogg"
        target = self.folder / "-odd.mp3"

        command = convert_audio.ffmpeg_command(
            "ffmpeg", source, target, options(speech=True, loudness=True, trim=True)
        )

        self.assertEqual(command[command.index("-i") + 1], str(source.resolve()))
        self.assertEqual(command[-1], str(target.resolve()))
        self.assertIn("-map_metadata", command)
        self.assertEqual(command[command.index("-ac") + 1], "1")
        filters = command[command.index("-af") + 1]
        self.assertTrue(filters.startswith("silenceremove") and "loudnorm" in filters)

    def test_plain_conversion_has_no_filters_or_mono(self):
        command = convert_audio.ffmpeg_command(
            "ffmpeg", Path("a.ogg"), Path("a.mp3"), options()
        )

        self.assertNotIn("-af", command)
        self.assertNotIn("-ac", command)

    def test_files_are_converted_beside_their_inputs(self):
        code, run, out = self.run_main(self.folder, "--speech")

        self.assertEqual(code, 0)
        self.assertEqual(run.call_count, 3)
        self.assertTrue((self.folder / "moon.mi.mp3").exists())
        self.assertTrue((self.folder / "page-01.mp3").exists())
        self.assertEqual(list(self.folder.glob(".*.part")), [])
        self.assertIn("Converted 3, skipped 0, failed 0.", out)

    def test_existing_mp3_files_are_kept_unless_overwrite(self):
        (self.folder / "moon.mi.mp3").write_bytes(b"keep")

        code, run, _ = self.run_main(self.folder / "moon.mi.ogg")
        self.assertEqual((code, run.call_count), (0, 0))
        self.assertEqual((self.folder / "moon.mi.mp3").read_bytes(), b"keep")

        code, run, _ = self.run_main(self.folder / "moon.mi.ogg", "--overwrite")
        self.assertEqual((code, run.call_count), (0, 1))
        self.assertEqual((self.folder / "moon.mi.mp3").read_bytes(), b"mp3")

    def test_an_mp3_in_place_is_skipped(self):
        (self.folder / "done.mp3").write_bytes(b"mp3")

        code, run, out = self.run_main(self.folder / "done.mp3")

        self.assertEqual((code, run.call_count), (0, 0))
        self.assertIn("already MP3 in place", out)

    def test_dry_run_converts_nothing(self):
        code, run, out = self.run_main(self.folder, "--dry-run")

        self.assertEqual((code, run.call_count), (0, 0))
        self.assertEqual(out.count("WOULD CONVERT"), 3)

    def test_failures_leave_no_partial_file_and_fail_the_run(self):
        code, _, _ = self.run_main(self.folder / "moon.mi.ogg", ffmpeg_ok=False)

        self.assertEqual(code, 1)
        self.assertFalse((self.folder / "moon.mi.mp3").exists())
        self.assertEqual(list(self.folder.glob(".*.part")), [])

    def test_missing_ffmpeg_is_explained(self):
        err = io.StringIO()
        with (
            patch.object(convert_audio.shutil, "which", return_value=None),
            redirect_stdout(io.StringIO()),
            redirect_stderr(err),
        ):
            code = convert_audio.main([str(self.folder / "moon.mi.ogg")])

        self.assertEqual(code, 2)
        self.assertIn("brew install ffmpeg", err.getvalue())


if __name__ == "__main__":
    unittest.main()
