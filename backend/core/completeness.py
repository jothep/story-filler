"""Check what a story is missing before it is published.

Problems break play, so a story with any stays a draft. Warnings point at
things that are often added later, such as audio, and do not block
publishing.
"""

from dataclasses import dataclass, field

from .blanks import placeholders_in
from .pages import PAGE_LENGTH, page_length


@dataclass
class Report:
    problems: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def summary(self):
        if not self.problems and not self.warnings:
            return "Ready"
        parts = []
        if self.problems:
            parts.append(plural(len(self.problems), "problem"))
        if self.warnings:
            parts.append(plural(len(self.warnings), "warning"))
        return ", ".join(parts)


def not_mp3(file):
    """Return the upper-case extension of a stored audio file that is not MP3."""
    if not file or file.name.lower().endswith(".mp3"):
        return None
    return file.name.rsplit(".", 1)[-1].upper() if "." in file.name else "?"


CONVERT_HINT = "convert it with scripts/convert_audio.py"


def plural(count, noun):
    return f"{count} {noun}{'' if count == 1 else 's'}"


def language_name(language):
    return language.name if language else "?"


def check_word(word, story, report):
    """Add the problems and warnings for one linked word."""
    forms = {form.language_id: form for form in word.forms.all()}
    needed = [(story.learning_language, True)]
    if story.language_id != story.learning_language_id:
        needed.append((story.language, False))
    for language, learning in needed:
        form = forms.get(language.pk)
        name = language_name(language)
        if form is None:
            role = "learning" if learning else "story"
            report.problems.append(
                f"Word {word.key} has no {name} form ({role} language)."
            )
        elif not form.audio:
            report.warnings.append(f"Word {word.key} has no {name} audio.")
        elif not_mp3(form.audio):
            report.warnings.append(
                f"Word {word.key} {name} audio is {not_mp3(form.audio)}, "
                f"not MP3; {CONVERT_HINT}."
            )
    if not word.image:
        report.warnings.append(f"Word {word.key} has no picture.")


def check_page(number, paragraph, words, report):
    """Check one page, collecting its linked words; return its blank count."""
    links = {link.placeholder: link for link in paragraph.blank_links.all()}
    placeholders = placeholders_in(paragraph.text)
    for placeholder in placeholders:
        link = links.get(placeholder)
        if link is None or link.word is None:
            report.problems.append(
                f"Page {number}: {placeholder} is not linked to a word."
            )
        else:
            words[link.word.pk] = link.word
    if not paragraph.audio:
        report.warnings.append(f"Page {number} has no narration.")
    elif not_mp3(paragraph.audio):
        report.warnings.append(
            f"Page {number} narration is {not_mp3(paragraph.audio)}, not MP3; "
            f"{CONVERT_HINT}."
        )
    if page_length(paragraph.text) > PAGE_LENGTH:
        report.warnings.append(
            f"Page {number} is longer than {PAGE_LENGTH} characters."
        )
    return len(placeholders)


def check_story(story):
    """Return a Report on what the saved story is missing."""
    report = Report()
    if not story.language_id or not story.learning_language_id:
        report.problems.append("Choose the story language and the learning language.")
    paragraphs = list(
        story.paragraphs.order_by("order", "pk").prefetch_related(
            "blank_links__word__forms"
        )
    )
    if not paragraphs:
        report.problems.append("The story has no pages.")
    words = {}
    blanks = 0
    for number, paragraph in enumerate(paragraphs, 1):
        blanks += check_page(number, paragraph, words, report)
    if paragraphs and not blanks:
        report.warnings.append("The story has no blanks.")
    if story.language_id and story.learning_language_id:
        for word in words.values():
            check_word(word, story, report)
    if not story.story_picture_id:
        report.warnings.append("The story has no picture.")
    music = story.background_music
    if music and not_mp3(music.audio_file):
        report.warnings.append(
            f"The background music is {not_mp3(music.audio_file)}, not MP3; "
            f"{CONVERT_HINT}."
        )
    return report
