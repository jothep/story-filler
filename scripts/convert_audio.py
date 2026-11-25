#!/usr/bin/env python3
"""Convert recordings to MP3 before uploading them to Story Filler.

Media are prepared on the author's machine; the service never converts them.
Run this on files or folders of recordings, then upload the MP3 files in the
admin. It needs ffmpeg installed locally (on macOS: ``brew install ffmpeg``).

Each audio file becomes an MP3 with the same name, so ``moon.mi.ogg`` becomes
``moon.mi.mp3``. Inputs are never changed, an existing MP3 is kept unless
``--overwrite`` is given, and metadata tags are not copied.

Examples:
  python3 scripts/convert_audio.py ~/Recordings/rona --speech --dry-run
  python3 scripts/convert_audio.py page-01.ogg page-02.ogg --speech --loudness
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

AUDIO_SUFFIXES = frozenset(
    {".aac", ".aif", ".aiff", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus"}
    | {".wav", ".webm", ".wma"}
)
LOUDNESS = "loudnorm=I=-16:TP=-1.5:LRA=11"
SILENCE = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.1"
TRIM = f"{SILENCE},areverse,{SILENCE},areverse"


class ConvertError(Exception):
    """An input cannot be converted as asked."""


def find_inputs(paths):
    """Return the audio files named by ``paths``, looking inside folders."""
    found = []
    for path in map(Path, paths):
        if path.is_dir():
            found += sorted(
                item
                for item in path.iterdir()
                if item.is_file() and item.suffix.lower() in AUDIO_SUFFIXES
            )
        elif path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES:
            found.append(path)
        else:
            raise ConvertError(f"Not an audio file or folder: {path}")
    return list(dict.fromkeys(found))


def output_path(source, output_dir=None):
    """Return where ``source`` is written as MP3, keeping its name."""
    return Path(output_dir or source.parent) / f"{source.stem}.mp3"


def ffmpeg_command(ffmpeg, source, target, options):
    """Return the ffmpeg arguments for one conversion."""
    filters = ([TRIM] if options.trim else []) + (
        [LOUDNESS] if options.loudness else []
    )
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
    command += ["-i", str(source.resolve()), "-vn", "-map_metadata", "-1"]
    if options.speech:
        command += ["-ac", "1"]
    if filters:
        command += ["-af", ",".join(filters)]
    command += ["-codec:a", "libmp3lame", "-q:a", "4", "-f", "mp3"]
    return command + [str(target.resolve())]


def convert(ffmpeg, source, target, options):
    """Convert one file through a temporary file; return False if ffmpeg fails."""
    partial = target.with_name(f".{target.name}.part")
    result = subprocess.run(
        ffmpeg_command(ffmpeg, source, partial, options),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        partial.unlink(missing_ok=True)
        print(f"FAILED {source}: {result.stderr.strip()[:300]}", file=sys.stderr)
        return False
    os.replace(partial, target)
    return True


def plan(sources, options):
    """Return (source, target) pairs to convert and the skipped files."""
    jobs = []
    skipped = []
    for source in sources:
        target = output_path(source, options.output)
        if target.resolve() == source.resolve():
            skipped.append(f"{source} (already MP3 in place)")
        elif target.exists() and not options.overwrite:
            skipped.append(f"{source} ({target.name} exists)")
        else:
            jobs.append((source, target))
    return jobs, skipped


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("paths", nargs="+", help="Audio files or folders")
    parser.add_argument(
        "--output", help="Folder for the MP3 files (default: beside each input)"
    )
    parser.add_argument(
        "--speech", action="store_true", help="Mix to mono, for narration and words"
    )
    parser.add_argument(
        "--loudness", action="store_true", help="Even out loudness (EBU R128)"
    )
    parser.add_argument(
        "--trim", action="store_true", help="Cut silence at the start and end"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Replace existing MP3 files"
    )
    parser.add_argument("--dry-run", action="store_true", help="List what would happen")
    return parser.parse_args(argv)


def main(argv=None):
    options = parse_args(argv)
    try:
        sources = find_inputs(options.paths)
    except ConvertError as error:
        print(error, file=sys.stderr)
        return 2
    jobs, skipped = plan(sources, options)
    for note in skipped:
        print(f"SKIP {note}")
    if options.dry_run:
        for source, target in jobs:
            print(f"WOULD CONVERT {source} -> {target}")
        return 0
    ffmpeg = shutil.which("ffmpeg")
    if jobs and not ffmpeg:
        print("ffmpeg is not installed. On macOS: brew install ffmpeg", file=sys.stderr)
        return 2
    if options.output:
        Path(options.output).mkdir(parents=True, exist_ok=True)
    failed = 0
    for source, target in jobs:
        if convert(ffmpeg, source, target, options):
            print(f"OK {source} -> {target}")
        else:
            failed += 1
    print(f"Converted {len(jobs) - failed}, skipped {len(skipped)}, failed {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
