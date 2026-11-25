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

KEY_LENGTH = 50


def key_base(value):
    """Lowercase ASCII with underscores, as the placeholder keys are written."""
    ascii_text = (
        unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    )
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def unique_key(base, used):
    base = base[: KEY_LENGTH - 4]
    key = base
    number = 2
    while key in used:
        key = f"{base}_{number}"
        number += 1
    used.add(key)
    return key


def copy_words_into_forms(apps, schema_editor):
    Language = apps.get_model("core", "Language")
    Story = apps.get_model("core", "Story")
    Word = apps.get_model("core", "Word")
    WordForm = apps.get_model("core", "WordForm")

    english, _ = Language.objects.get_or_create(code="en", defaults={"name": "English"})
    maori, _ = Language.objects.get_or_create(code="mi", defaults={"name": "Māori"})

    used = set(Word.objects.exclude(key=None).values_list("key", flat=True))
    for word in Word.objects.order_by("pk"):
        if not word.key:
            base = key_base(word.english_translation) or key_base(word.maori_word)
            word.key = unique_key(base or f"word_{word.pk}", used)
            word.save(update_fields=["key"])
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
