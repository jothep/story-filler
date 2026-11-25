"""Copy the Māori and English word columns into word forms.

Creates the English and Māori languages, gives each word a key derived from
its English translation (as placeholders such as __BLANK_moon__ already use),
copies its text and audio into one form per language, and sets existing
stories to English with Māori as the learning language. Stored files are
referenced by name, not copied. Running it again changes nothing.
"""

import re
import unicodedata

from django.db import migrations

KEY_LENGTH = 40


def key_base(value):
    """Lowercase ASCII with underscores, as the placeholder keys are written."""
    ascii_text = (
        unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    )
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def fit(base, suffix=""):
    """Shorten ``base`` so that ``base + suffix`` fits the key column."""
    return base[: KEY_LENGTH - len(suffix)].rstrip("_") + suffix


def numbered_key(base, used):
    number = 2
    while fit(base, f"_{number}") in used:
        number += 1
    key = fit(base, f"_{number}")
    used.add(key)
    return key


def copy_words_into_forms(apps, schema_editor):
    Language = apps.get_model("core", "Language")
    Story = apps.get_model("core", "Story")
    Word = apps.get_model("core", "Word")
    WordForm = apps.get_model("core", "WordForm")

    english, _ = Language.objects.get_or_create(code="en", defaults={"name": "English"})
    maori, _ = Language.objects.get_or_create(code="mi", defaults={"name": "Māori"})

    words = list(Word.objects.order_by("pk"))
    used = {word.key for word in words if word.key}
    bases = {
        word.pk: fit(
            key_base(word.english_translation)
            or key_base(word.maori_word)
            or f"word_{word.pk}"
        )
        for word in words
        if not word.key
    }
    # Give each base to its first word before numbering repeats, so a number
    # never takes the key that another word's own text would produce.
    for word in words:
        if not word.key and bases[word.pk] not in used:
            word.key = bases[word.pk]
            used.add(word.key)
            word.save(update_fields=["key"])
    for word in words:
        if not word.key:
            word.key = numbered_key(bases[word.pk], used)
            word.save(update_fields=["key"])
    for word in words:
        for language, text, audio in (
            (maori, word.maori_word, word.maori_audio),
            (english, word.english_translation, word.english_audio),
        ):
            if text:
                WordForm.objects.get_or_create(
                    word=word,
                    language=language,
                    defaults={"text": text, "audio": audio.name or None},
                )

    Story.objects.filter(language=None).update(language=english)
    Story.objects.filter(learning_language=None).update(learning_language=maori)


class Migration(migrations.Migration):
    dependencies = [("core", "0010_languages_and_word_forms")]

    operations = [
        migrations.RunPython(copy_words_into_forms, migrations.RunPython.noop)
    ]
