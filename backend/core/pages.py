"""Turn a whole story, pasted as text, into pages.

Each page is a Paragraph, shown on its own screen in the game. A blank line
starts a new page; a page longer than ``PAGE_LENGTH`` is split at sentence
ends, packing as many sentences onto each page as fit. A single sentence
longer than the limit stays on one page.
"""

import unicodedata

from django.db import transaction

from .blanks import PLACEHOLDER
from .models import Story

# The longest live page is 216 characters by this measure; a blank counts as
# BLANK_LENGTH characters because the game shows it as a fixed-width box, and
# a wide character (such as Chinese) counts as two.
PAGE_LENGTH = 240
BLANK_LENGTH = 10
# Punctuation that ends a sentence when whitespace or the text's end follows.
SENTENCE_END = frozenset(".!?…؟")
# Full-width punctuation ends a sentence even without a following space, as
# in Chinese or Japanese text.
FULL_WIDTH_END = frozenset("。！？")
CLOSING = frozenset('"”’)]」』）】')
# A full stop after these words does not end the sentence.
ABBREVIATIONS = frozenset(
    {"mr", "mrs", "ms", "dr", "prof", "st", "mt", "vs", "etc", "e.g", "i.e"}
)


def page_length(text):
    """Return the length of ``text`` as it takes up space in the game."""
    text = PLACEHOLDER.sub("x" * BLANK_LENGTH, text)
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def blocks_in(text):
    """Return the text's blocks: runs of non-blank lines, joined by spaces."""
    blocks = []
    lines = []
    for line in (text or "").splitlines():
        if line.strip():
            lines.append(line)
        elif lines:
            blocks.append(" ".join(" ".join(lines).split()))
            lines = []
    if lines:
        blocks.append(" ".join(" ".join(lines).split()))
    return blocks


def sentences_in(text):
    """Split text after sentence-ending punctuation and any closing quotes.

    A sentence ends where ``.``, ``!``, ``?`` or ``…`` (and any closing quotes
    or brackets after them) are followed by whitespace or the end of the text.
    The scan is linear, so pasted text cannot make it slow.
    """
    sentences = []
    start = 0
    index = 0
    length = len(text)
    while index < length:
        full_width = text[index] in FULL_WIDTH_END
        if not full_width and text[index] not in SENTENCE_END:
            index += 1
            continue
        end = index + 1
        while end < length and (
            text[end] in SENTENCE_END
            or text[end] in FULL_WIDTH_END
            or text[end] in CLOSING
        ):
            end += 1
        ends = full_width or end == length or text[end].isspace()
        if ends and not abbreviation_before(text, start, index, end):
            sentence = text[start:end].strip()
            if sentence:
                sentences.append(sentence)
            start = end
        index = end
    rest = text[start:].strip()
    if rest:
        sentences.append(rest)
    return sentences


def abbreviation_before(text, start, index, end):
    """Whether a single full stop at ``index`` follows a known abbreviation."""
    if text[index] != "." or end != index + 1:
        return False
    word_start = text.rfind(" ", start, index) + 1
    return text[word_start:index].lower() in ABBREVIATIONS


def split_pages(text, limit=PAGE_LENGTH):
    """Return the pages of a whole story."""
    pages = []
    for block in blocks_in(text):
        current = ""
        for sentence in sentences_in(block):
            candidate = f"{current} {sentence}".strip()
            if current and page_length(candidate) > limit:
                pages.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            pages.append(current)
    return pages


def story_text(story):
    """Return a story's pages as one text, with blanks written as ``{{key}}``."""
    return "\n\n".join(
        PLACEHOLDER.sub(lambda match: "{{" + match.group(1) + "}}", paragraph.text)
        for paragraph in story.paragraphs.order_by("order", "pk")
    ).replace("\r\n", "\n")


def apply_pages(story, pages):
    """Make the story's paragraphs match ``pages``, keeping audio by position.

    Page *n* reuses the story's *n*-th paragraph, so its narration stays
    attached, and pages are numbered from 0 in that order; extra paragraphs
    are deleted and new pages are added without audio. The story row is
    locked, so two saves cannot interleave. Returns the 1-based numbers of
    pages whose text changed while they had audio, and of deleted paragraphs
    that had audio.
    """
    with transaction.atomic():
        Story.objects.select_for_update().filter(pk=story.pk).first()
        return replace_pages(story, pages)


def replace_pages(story, pages):
    paragraphs = list(story.paragraphs.order_by("order", "pk"))
    changed_with_audio = []
    for index, text in enumerate(pages):
        if index < len(paragraphs):
            paragraph = paragraphs[index]
            if paragraph.text != text and paragraph.audio:
                changed_with_audio.append(index + 1)
            if paragraph.text != text or paragraph.order != index:
                paragraph.text = text
                paragraph.order = index
                paragraph.save(update_fields=["text", "order"])
        else:
            story.paragraphs.create(order=index, text=text)
    removed_with_audio = []
    for number, paragraph in enumerate(paragraphs[len(pages) :], len(pages) + 1):
        if paragraph.audio:
            removed_with_audio.append(number)
        paragraph.delete()
    return changed_with_audio, removed_with_audio
