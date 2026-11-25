"""Save many dropped files at once, matched to words and pages by file name.

Word files are named by key, and audio also by language code:
``moon.jpg`` is the picture of ``moon``, ``moon.mi.mp3`` its Māori audio.
Narration files are named by page number: ``page-01.mp3``, ``page-2.mp3`` or
``3.mp3`` for the story's first, second and third pages. Nothing is guessed:
a file that does not match exactly is listed with the reason.
"""

import re
from dataclasses import dataclass, field
from pathlib import PurePath

from django.core.exceptions import ValidationError
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
PAGE_NAME = re.compile(r"(?:page[-_ ]?)?0*(\d{1,4})", re.IGNORECASE)
CONVERT = "convert it to MP3 with scripts/convert_audio.py first"


@dataclass
class UploadReport:
    saved: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def split_name(upload):
    """Return the file's base name, its dot-separated parts and extension."""
    name = PurePath(upload.name).name
    parts = name.split(".")
    return name, parts, parts[-1].lower() if len(parts) > 1 else ""


def checked(validator, upload, name, report):
    """Run a size validator; record and return False when it fails."""
    try:
        validator(upload)
    except ValidationError as error:
        report.skipped.append(f"{name}: {' '.join(error.messages)}")
        return False
    return True


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


def save_word_files(uploads):
    """Save pictures and audio to the words their names match."""
    report = UploadReport()
    words = {word.key: word for word in Word.objects.exclude(key=None)}
    languages = {language.code.lower(): language for language in Language.objects.all()}
    seen = set()
    for upload in uploads:
        name = split_name(upload)[0]
        try:
            kind, word, language = match_word_file(upload, words, languages)
        except ValueError as error:
            report.skipped.append(str(error))
            continue
        slot = (kind, word.pk, language.pk if language else None)
        if slot in seen:
            report.skipped.append(
                f"{name}: another file in this upload has the same target."
            )
            continue
        seen.add(slot)
        if kind == "image":
            save_word_image(upload, word, name, report)
        else:
            save_form_audio(upload, word, language, name, report)
    return report


def save_word_image(upload, word, name, report):
    if not checked(validate_image_file_size, upload, name, report):
        return
    try:
        content, _ = compress_image(upload, max_width=800, max_height=800, quality=80)
    except ValidationError as error:
        report.skipped.append(f"{name}: {' '.join(error.messages)}")
        return
    replaced = bool(word.image)
    word.image.save(f"{word.key}.jpg", content, save=False)
    word.save(skip_compression=True)
    report.saved.append(
        f"{name}: picture of {word.key}" + (" (replaced)" if replaced else "")
    )


def save_form_audio(upload, word, language, name, report):
    form = word.forms.filter(language=language).first()
    if form is None:
        report.skipped.append(
            f"{name}: {word.key} has no {language.name} form yet; add its text first."
        )
        return
    if not checked(validate_audio_file_size, upload, name, report):
        return
    replaced = bool(form.audio)
    form.audio.save(f"{word.key}.{language.code}.mp3", upload, save=True)
    report.saved.append(
        f"{name}: {language.name} audio of {word.key}"
        + (" (replaced)" if replaced else "")
    )


def page_number(upload):
    """Return the 1-based page number in a narration file name, or None."""
    _, parts, extension = split_name(upload)
    if extension != "mp3" or len(parts) != 2:
        return None
    match = PAGE_NAME.fullmatch(parts[0])
    return int(match.group(1)) if match else None


def save_narration(story, uploads):
    """Save narration files to the story's pages by their page numbers."""
    report = UploadReport()
    paragraphs = list(story.paragraphs.order_by("order", "pk"))
    seen = set()
    for upload in uploads:
        name, _, extension = split_name(upload)
        if extension in OTHER_AUDIO:
            report.skipped.append(f"{name}: narration must be MP3; {CONVERT}.")
            continue
        number = page_number(upload)
        if number is None:
            report.skipped.append(
                f"{name}: name it page-01.mp3, page-02.mp3 and so on."
            )
            continue
        if not 1 <= number <= len(paragraphs):
            report.skipped.append(f"{name}: the story has {len(paragraphs)} pages.")
            continue
        if number in seen:
            report.skipped.append(
                f"{name}: another file in this upload is for page {number}."
            )
            continue
        seen.add(number)
        if not checked(validate_audio_file_size, upload, name, report):
            continue
        paragraph = paragraphs[number - 1]
        replaced = bool(paragraph.audio)
        slug = slugify(story.title) or "story"
        paragraph.audio.save(f"{slug}-page-{number:02d}.mp3", upload, save=True)
        report.saved.append(
            f"{name}: page {number}" + (" (replaced)" if replaced else "")
        )
    return report
