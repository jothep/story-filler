"""Write story content as a package of TOML files.

The package is the planned source of truth for stories (workstream 3 of the
improvement plan)::

    content/
      library.toml                  story pictures, music and the menu music
      words.toml                    the shared word bank
      stories/<slug>/story.toml     title, picture, music and paragraphs

Paragraph text writes each blank inline: ``{{moon}}`` when the blank key is
the key of its word in ``words.toml``, or ``{{moon|marama}}`` when the two
differ. The importer turns each one back into a ``__BLANK_<key>__``
placeholder and its Blank Link, so the API and the frontend stay unchanged.

Media values are the names of objects already in media storage, such as
``word_images/moon.jpg``. Python reads TOML with the standard library
(``tomllib``), so the package adds no dependency.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from django.utils.text import slugify

from .blanks import PLACEHOLDER, placeholder_key, placeholders_in
from .models import AppConfig, BackgroundMusic, Paragraph, Story, StoryPicture, Word

BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")
TOML_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


class ContentError(Exception):
    """The database holds content that the package cannot represent exactly."""

    def __init__(self, problems):
        super().__init__("\n".join(problems))
        self.problems = problems


# ===== TOML writing =====


def toml_string(value):
    """Return ``value`` as a TOML basic string."""
    characters = []
    for character in value:
        if character in TOML_ESCAPES:
            characters.append(TOML_ESCAPES[character])
        elif ord(character) < 0x20 or ord(character) == 0x7F:
            characters.append(f"\\u{ord(character):04X}")
        else:
            characters.append(character)
    return '"' + "".join(characters) + '"'


def toml_key(key):
    return key if BARE_KEY.fullmatch(key) else toml_string(key)


def toml_value(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise TypeError(f"Unsupported TOML value: {value!r}")
    return str(value) if isinstance(value, int) else toml_string(value)


def toml_fields(fields):
    return [f"{toml_key(key)} = {toml_value(value)}" for key, value in fields.items()]


def dump_toml(document):
    """Serialise the package's documents.

    A document maps keys to scalars (strings or integers), to tables of
    tables of scalars (``[words.moon]``), or to arrays of tables of scalars
    (``[[paragraphs]]``). Scalars come first, as TOML requires.
    """
    scalars = {
        key: value
        for key, value in document.items()
        if not isinstance(value, (dict, list))
    }
    lines = toml_fields(scalars)
    for key, value in document.items():
        if isinstance(value, dict):
            for name, fields in value.items():
                lines += ["", f"[{toml_key(key)}.{toml_key(name)}]"]
                lines += toml_fields(fields)
        elif isinstance(value, list):
            for fields in value:
                lines += ["", f"[[{toml_key(key)}]]"]
                lines += toml_fields(fields)
    return "\n".join(lines).lstrip("\n") + "\n"


# ===== Keys =====


def unique_key(base, used, separator):
    """Return ``base``, or ``base`` with a number, so that it is not in ``used``."""
    key = base
    number = 2
    while key in used:
        key = f"{base}{separator}{number}"
        number += 1
    used.add(key)
    return key


def slug_keys(objects, title):
    """Map each object's id to a hyphenated key made from its title."""
    used = set()
    return {
        obj.pk: unique_key(slugify(title(obj)) or "item", used, "-") for obj in objects
    }


def word_keys(words):
    """Map each word's id to a key in the placeholder alphabet.

    Keys come from the English translation, as the automatic linking rule does,
    then the Māori word.
    """
    used = set()
    keys = {}
    for word in words:
        base = (
            placeholder_key(word.english_translation)
            or placeholder_key(word.maori_word)
            or "word"
        )
        keys[word.pk] = unique_key(base, used, "_")
    return keys


def with_media(fields, **media):
    """Add the stored names of the media that are set."""
    for name, value in media.items():
        if value:
            fields[name] = value.name
    return fields


# ===== Package =====


@dataclass
class Package:
    library: dict
    words: dict
    stories: dict = field(default_factory=dict)

    def files(self):
        """Map each file's path inside the package to its TOML text."""
        files = {
            Path("library.toml"): dump_toml(self.library),
            Path("words.toml"): dump_toml(self.words),
        }
        for slug, story in self.stories.items():
            files[Path("stories", slug, "story.toml")] = dump_toml(story)
        return files


def inline_blanks(paragraph, links, keys, problems):
    """Return the paragraph text with each placeholder written inline.

    ``links`` maps the paragraph's placeholders to word ids. Placeholders that
    cannot be written exactly are added to ``problems`` and left unchanged.
    """
    where = f'"{paragraph.story.title}" paragraph {paragraph.order}'
    if "{{" in paragraph.text or "}}" in paragraph.text:
        problems.append(f"{where}: the text contains {{{{ or }}}}, used for blanks")
    for placeholder in sorted(set(links) - set(placeholders_in(paragraph.text))):
        problems.append(f"{where}: Blank Link {placeholder} is not in the text")

    def replace(match):
        placeholder, key = match.group(0), match.group(1)
        if placeholder not in links:
            problems.append(f"{where}: {placeholder} has no Blank Link")
            return placeholder
        if links[placeholder] is None:
            problems.append(f"{where}: {placeholder} is linked to no word")
            return placeholder
        word_key = keys[links[placeholder]]
        inner = key if word_key == key else f"{key}|{word_key}"
        return "{{" + inner + "}}"

    return PLACEHOLDER.sub(replace, paragraph.text)


def story_document(story, paragraphs, references, problems):
    document = {"title": story.title}
    if story.story_picture_id:
        document["picture"] = references["pictures"][story.story_picture_id]
    if story.background_music_id:
        document["music"] = references["music"][story.background_music_id]
    entries = []
    for index, paragraph in enumerate(paragraphs):
        links = {link.placeholder: link.word_id for link in paragraph.blank_links.all()}
        entry = {}
        if paragraph.order != index:
            entry["order"] = paragraph.order
        entry["text"] = inline_blanks(paragraph, links, references["words"], problems)
        entries.append(with_media(entry, audio=paragraph.audio))
    document["paragraphs"] = entries
    return document


def build_package():
    """Read every story, word and library item into a package.

    Raises ``ContentError`` listing everything that cannot be written exactly.
    """
    pictures = list(StoryPicture.objects.order_by("pk"))
    music = list(BackgroundMusic.objects.order_by("pk"))
    words = list(Word.objects.order_by("pk"))
    references = {
        "pictures": slug_keys(pictures, lambda picture: picture.title),
        "music": slug_keys(music, lambda track: track.title),
        "words": word_keys(words),
    }

    library = {}
    config = AppConfig.objects.order_by("pk").first()
    if config and config.menu_bgm_id:
        library["menu_music"] = references["music"][config.menu_bgm_id]
    library["pictures"] = {
        references["pictures"][picture.pk]: with_media(
            {"title": picture.title}, image=picture.image_file
        )
        for picture in pictures
    }
    library["music"] = {
        references["music"][track.pk]: with_media(
            {"title": track.title}, audio=track.audio_file
        )
        for track in music
    }

    word_table = {
        references["words"][word.pk]: with_media(
            {"maori": word.maori_word, "english": word.english_translation},
            image=word.image,
            maori_audio=word.maori_audio,
            english_audio=word.english_audio,
        )
        for word in words
    }
    package = Package(library=library, words={"words": word_table})

    problems = []
    story_slugs = set()
    for story in Story.objects.order_by("pk"):
        paragraphs = (
            Paragraph.objects.filter(story=story)
            .select_related("story")
            .prefetch_related("blank_links")
            .order_by("order", "pk")
        )
        slug = unique_key(slugify(story.title) or "story", story_slugs, "-")
        package.stories[slug] = story_document(story, paragraphs, references, problems)
    if problems:
        raise ContentError(problems)
    return package


def write_package(package, destination, overwrite=False):
    """Write the package files under ``destination``; return their paths.

    Existing files are replaced only with ``overwrite``. Files that the package
    does not contain are left in place.
    """
    destination = Path(destination)
    files = package.files()
    existing = [path for path in files if (destination / path).exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Package files already exist: "
            + ", ".join(str(path) for path in sorted(existing))
        )
    for path, text in files.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return sorted(files)
