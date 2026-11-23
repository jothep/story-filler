"""Link paragraph placeholders such as ``__BLANK_moon__`` to words in the bank.

The key after ``__BLANK_`` names a word by its English translation, or by its
Māori word, written in lowercase ASCII with underscores for spaces. Macrons
are dropped, so ``kōrero paki`` becomes ``korero_paki``. The pattern matches
the one the frontend uses to find blanks.
"""

import re
import unicodedata

from .models import BlankLink, Word

PLACEHOLDER = re.compile(r"__BLANK_([A-Za-z0-9_]+)__")


def placeholder_key(value):
    """Return the lowercase ASCII key used in placeholders for ``value``."""
    ascii_text = (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def build_word_index(words=None):
    """Map placeholder keys to words, separately for English and Māori."""
    if words is None:
        words = Word.objects.only("id", "maori_word", "english_translation")
    index = {"english": {}, "maori": {}}
    for word in words:
        english = placeholder_key(word.english_translation)
        maori = placeholder_key(word.maori_word)
        index["english"].setdefault(english, []).append(word)
        index["maori"].setdefault(maori, []).append(word)
    return index


def find_word(index, key):
    """Return the one word for ``key``, or ``None`` if none or several match.

    English translations are checked first, then Māori words.
    """
    key = placeholder_key(key)
    matches = index["english"].get(key) or index["maori"].get(key) or []
    return matches[0] if len(matches) == 1 else None


def placeholders_in(text):
    """Return each distinct placeholder in ``text``, in order of appearance."""
    return list(dict.fromkeys(m.group(0) for m in PLACEHOLDER.finditer(text or "")))


def link_placeholders(paragraph, index=None):
    """Create missing Blank Links for ``paragraph``.

    Existing links are never changed or removed. A placeholder gets a link only
    when exactly one word matches its key. Returns the placeholders that still
    have no link, so the caller can ask for them to be linked by hand.
    """
    index = index or build_word_index()
    linked = set(paragraph.blank_links.values_list("placeholder", flat=True))
    unlinked = []
    for placeholder in placeholders_in(paragraph.text):
        if placeholder in linked:
            continue
        word = find_word(index, PLACEHOLDER.fullmatch(placeholder).group(1))
        if word is None:
            unlinked.append(placeholder)
            continue
        BlankLink.objects.create(
            paragraph=paragraph, placeholder=placeholder, word=word
        )
    return unlinked
