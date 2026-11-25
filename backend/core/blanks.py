"""Link paragraph placeholders such as ``__BLANK_moon__`` to words in the bank.

The key after ``__BLANK_`` names a word entry by its key. When no entry has
that key, a word whose form in any language reads the same, written in
lowercase ASCII with underscores for spaces, is used instead. Macrons are
dropped, so ``kōrero paki`` matches ``korero_paki``. The pattern matches the
one the frontend uses to find blanks.
"""

import re
import unicodedata

from django.db import IntegrityError, transaction

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
    """Map placeholder keys to words, by word key and by form text."""
    if words is None:
        words = Word.objects.only("id", "key").prefetch_related("forms")
    index = {"key": {}, "forms": {}}
    for word in words:
        if word.key:
            index["key"].setdefault(word.key, []).append(word)
        for form in word.forms.all():
            matches = index["forms"].setdefault(placeholder_key(form.text), [])
            if word not in matches:
                matches.append(word)
    return index


def find_word(index, key):
    """Return the one word for ``key``, or ``None`` if none or several match.

    Word keys are checked first, then the text of every language form.
    """
    key = placeholder_key(key)
    matches = index["key"].get(key) or index["forms"].get(key) or []
    return matches[0] if len(matches) == 1 else None


def placeholders_in(text):
    """Return each distinct placeholder in ``text``, in order of appearance."""
    return list(dict.fromkeys(m.group(0) for m in PLACEHOLDER.finditer(text or "")))


def link_placeholders(paragraph, index=None):
    """Create missing Blank Links for ``paragraph``.

    Existing links are never changed or removed. A placeholder gets a link only
    when exactly one word matches its key. Returns the placeholders that still
    have no word, so the caller can ask for them to be linked by hand: no or
    several matches, an existing link without a word, a placeholder too long to
    store, or a word deleted while saving.
    """
    index = index or build_word_index()
    max_length = BlankLink._meta.get_field("placeholder").max_length
    links = dict(paragraph.blank_links.values_list("placeholder", "word_id"))
    unlinked = []
    for placeholder in placeholders_in(paragraph.text):
        if placeholder in links:
            if links[placeholder] is None:
                unlinked.append(placeholder)
            continue
        word = find_word(index, PLACEHOLDER.fullmatch(placeholder).group(1))
        if word is None or len(placeholder) > max_length:
            unlinked.append(placeholder)
            continue
        try:
            # The savepoint keeps a concurrent save of the same link from
            # breaking the surrounding admin transaction.
            with transaction.atomic():
                # Foreign keys are checked at commit, so re-read and lock the
                # word: a word deleted since the index was built is reported,
                # and one still present cannot be deleted before this commits.
                current = Word.objects.select_for_update().filter(pk=word.pk).first()
                if current is None:
                    unlinked.append(placeholder)
                    continue
                BlankLink.objects.get_or_create(
                    paragraph=paragraph,
                    placeholder=placeholder,
                    defaults={"word": current},
                )
        except IntegrityError:
            unlinked.append(placeholder)
    return unlinked
