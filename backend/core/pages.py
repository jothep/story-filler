"""Turn a whole story, pasted as text, into pages.

Each page is a Paragraph, shown on its own screen in the game. A blank line
starts a new page; a page longer than ``PAGE_LENGTH`` is split at sentence
ends, packing as many sentences onto each page as fit. A single sentence
longer than the limit stays on one page.
"""

import re

from .blanks import PLACEHOLDER

# The longest live page is 216 characters by this measure; a blank counts as
# BLANK_LENGTH characters because the game shows it as a fixed-width box.
PAGE_LENGTH = 240
BLANK_LENGTH = 10
PAGE_BREAK = re.compile(r"\n\s*\n")
SENTENCE = re.compile(r"\S.*?(?:[.!?…]+[\"”’)\]]*(?=\s|$)|$)", re.S)


def page_length(text):
    """Return the length of ``text`` as it takes up space in the game."""
    return len(PLACEHOLDER.sub("x" * BLANK_LENGTH, text))


def sentences_in(text):
    return [match.group(0).strip() for match in SENTENCE.finditer(text)]


def split_pages(text, limit=PAGE_LENGTH):
    """Return the pages of a whole story."""
    pages = []
    for block in PAGE_BREAK.split((text or "").replace("\r\n", "\n").strip()):
        block = " ".join(block.split())
        if not block:
            continue
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
    )


def apply_pages(story, pages):
    """Make the story's paragraphs match ``pages``, keeping audio by position.

    Page *n* reuses the story's *n*-th paragraph, so its narration stays
    attached; extra paragraphs are deleted and new pages are added without
    audio. Returns the 1-based numbers of pages whose text changed while they
    had audio, and of deleted paragraphs that had audio.
    """
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
