"""Save many dropped files at once, matched to words and pages by file name.

Word files are named by key, and audio also by language code:
``moon.jpg`` is the picture of ``moon``, ``moon.mi.mp3`` its Māori audio.
Narration files are named by page number: ``page-01.mp3``, ``page-2.mp3``,
``3.mp3`` or a name ending in the number after ``-``, ``_`` or a space, such
as ``Rona_moon_04.mp3``, for the story's first to fourth pages. Nothing is guessed:
a file that does not match exactly is listed with the reason.

Uploading is planned first, so a dry run reports exactly what saving would
do. The admin pages and the ``upload_narration`` and ``upload_word_files``
commands share this module.
"""

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path, PurePath
from typing import Callable

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import storages
from django.utils.text import slugify

from .models import (
    Language,
    Word,
    compress_image,
    validate_audio_file_size,
    validate_image_file_size,
)

IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp"})
OTHER_AUDIO = frozenset({"aac", "aif", "aiff", "flac", "m4a", "oga", "ogg", "opus"})
OTHER_AUDIO |= {"wav", "webm", "wma"}
PAGE_SEPARATORS = "-_ "
CONVERT = "convert it to MP3 with scripts/convert_audio.py first"


@dataclass
class UploadReport:
    saved: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


@dataclass
class Item:
    """One file and what saving it does."""

    name: str
    target: str
    save: Callable[[], str]


def split_name(upload):
    """Return the file's base name, its dot-separated parts and extension."""
    name = PurePath(upload.name).name
    parts = name.split(".")
    return name, parts, parts[-1].lower() if len(parts) > 1 else ""


def size_problem(validator, upload):
    """Return the size validator's message for ``upload``, or None."""
    try:
        validator(upload)
    except ValidationError as error:
        return " ".join(error.messages)
    return None


def match_word_file(upload, words, languages):
    """Return (kind, word, language) for a word file, or raise ValueError."""
    name, parts, extension = split_name(upload)
    if extension in OTHER_AUDIO:
        raise ValueError(f"{name}: audio must be MP3; {CONVERT}.")
    if extension in IMAGE_EXTENSIONS and len(parts) == 2:
        word = words.get(parts[0].lower())
        if word is None:
            raise ValueError(f"{name}: no word has the key {parts[0]}.")
        return "image", word, None
    if extension == "mp3" and len(parts) == 3:
        word = words.get(parts[0].lower())
        language = languages.get(parts[1].lower())
        if word is None:
            raise ValueError(f"{name}: no word has the key {parts[0]}.")
        if language is None:
            raise ValueError(f"{name}: no language has the code {parts[1]}.")
        return "audio", word, language
    raise ValueError(
        f"{name}: name it <key>.jpg for a picture or <key>.<language>.mp3 for audio."
    )


def plan_word_files(uploads):
    """Return the word files to save and the reasons others are skipped."""
    items = []
    skipped = []
    words = {word.key: word for word in Word.objects.exclude(key=None)}
    languages = {language.code.lower(): language for language in Language.objects.all()}
    seen = set()
    for upload in uploads:
        name = split_name(upload)[0]
        try:
            kind, word, language = match_word_file(upload, words, languages)
        except ValueError as error:
            skipped.append(str(error))
            continue
        slot = (kind, word.pk, language.pk if language else None)
        if slot in seen:
            skipped.append(f"{name}: another file in this upload has the same target.")
            continue
        seen.add(slot)
        item, problem = word_item(upload, name, kind, word, language)
        if problem:
            skipped.append(f"{name}: {problem}")
        else:
            items.append(item)
    return items, skipped


def word_item(upload, name, kind, word, language):
    """Return (item, None) for a matched word file, or (None, problem)."""
    if kind == "image":
        problem = size_problem(validate_image_file_size, upload)
        item = Item(
            name, f"picture of {word.key}", partial(save_word_image, upload, word)
        )
        return (None, problem) if problem else (item, None)
    form = word.forms.filter(language=language).first()
    if form is None:
        return None, f"{word.key} has no {language.name} form yet; add its text first."
    problem = size_problem(validate_audio_file_size, upload)
    target = f"{language.name} audio of {word.key}"
    item = Item(name, target, partial(save_form_audio, upload, form))
    return (None, problem) if problem else (item, None)


def save_word_image(upload, word):
    """Save a scaled JPEG as the word's picture; return the replaced name."""
    previous = word.image.name or ""
    content, _ = compress_image(upload, max_width=800, max_height=800, quality=80)
    word.image.save(f"{word.key}.jpg", content, save=False)
    word.save(skip_compression=True)
    return previous


def save_form_audio(upload, form):
    """Save the form's audio; return the replaced name."""
    previous = form.audio.name or ""
    form.audio.save(f"{form.word.key}.{form.language.code}.mp3", upload, save=True)
    return previous


def page_number(upload):
    """Return the 1-based page number at the end of a narration file name.

    The number may stand alone or follow ``page``, ``-``, ``_`` or a space,
    so ``take2.mp3`` is not read as page 2. Returns None otherwise.
    """
    _, parts, extension = split_name(upload)
    if extension != "mp3" or len(parts) != 2:
        return None
    stem = parts[0]
    digits = len(stem) - len(stem.rstrip("0123456789"))
    if not 1 <= digits <= 4:
        return None
    prefix = stem[: len(stem) - digits]
    if prefix and prefix[-1] not in PAGE_SEPARATORS:
        if not prefix.lower().endswith("page"):
            return None
    return int(stem[-digits:]) or None


def plan_narration(story, uploads):
    """Return the narration files to save and the reasons others are skipped."""
    items = []
    skipped = []
    paragraphs = list(story.paragraphs.order_by("order", "pk"))
    slug = slugify(story.title) or "story"
    seen = set()
    for upload in uploads:
        name, _, extension = split_name(upload)
        if extension in OTHER_AUDIO:
            skipped.append(f"{name}: narration must be MP3; {CONVERT}.")
            continue
        number = page_number(upload)
        if number is None:
            skipped.append(
                f"{name}: end the name with its page number, such as page-01.mp3 "
                "or Rona_moon_01.mp3."
            )
            continue
        if not 1 <= number <= len(paragraphs):
            skipped.append(f"{name}: the story has {len(paragraphs)} pages.")
            continue
        if number in seen:
            skipped.append(f"{name}: another file in this upload is for page {number}.")
            continue
        seen.add(number)
        problem = size_problem(validate_audio_file_size, upload)
        if problem:
            skipped.append(f"{name}: {problem}")
            continue
        save = partial(
            save_page_audio,
            upload,
            paragraphs[number - 1],
            f"{slug}-page-{number:02d}.mp3",
        )
        items.append(Item(name, f"page {number}", save))
    return items, skipped


def save_page_audio(upload, paragraph, stored_name):
    """Save a page's narration; return the replaced name."""
    previous = paragraph.audio.name or ""
    paragraph.audio.save(stored_name, upload, save=True)
    return previous


def run(items, skipped, dry_run=False):
    """Save the planned items, or only report them for a dry run."""
    report = UploadReport(skipped=list(skipped))
    for item in items:
        if dry_run:
            report.saved.append(f"{item.name}: would be {item.target}")
            continue
        try:
            previous = item.save()
        except ValidationError as error:
            report.skipped.append(f"{item.name}: {' '.join(error.messages)}")
            continue
        replaced = f" (replaced {previous})" if previous else ""
        report.saved.append(f"{item.name}: {item.target}{replaced}")
    return report


def save_word_files(uploads):
    """Save pictures and audio to the words their names match."""
    return run(*plan_word_files(uploads))


def save_narration(story, uploads):
    """Save narration files to the story's pages by their page numbers."""
    return run(*plan_narration(story, uploads))


@contextmanager
def opened_files(paths):
    """Open the files named by ``paths``, looking inside folders.

    Hidden files such as ``.DS_Store`` in folders are ignored.
    """
    found = []
    for path in map(Path, paths):
        if path.is_dir():
            found += sorted(
                item
                for item in path.iterdir()
                if item.is_file() and not item.name.startswith(".")
            )
        elif path.is_file():
            found.append(path)
        else:
            raise FileNotFoundError(f"No such file or folder: {path}")
    with ExitStack() as stack:
        yield [
            File(stack.enter_context(path.open("rb")), name=path.name)
            for path in dict.fromkeys(found)
        ]


def storage_description():
    """Name the storage that saved files go to."""
    storage = storages["default"]
    backend = type(storage).__name__
    bucket = getattr(storage, "bucket_name", None)
    location = getattr(storage, "location", "")
    return f"{backend} ({'bucket ' + bucket if bucket else location})"
