# Content package

The content package holds the stories, the word bank and the media library as TOML files. It is being introduced in [workstream 3 of the improvement plan](../improvement-plan.md#3-content-as-code). For now, `export_content` writes it from a database; the importer and its CI checks come next. Until then, the Django admin remains where content is edited.

## Layout

```text
content/
  library.toml                  story pictures, music and the menu music
  words.toml                    the shared word bank
  stories/<slug>/story.toml     title, picture, music and paragraphs
```

`library.toml`:

```toml
menu_music = "traumerei_mid"

[pictures.rona]
title = "Rona"
image = "story_pictures/rona.jpg"

[music.dvorak-humoresque]
title = "Dvořák — Humoresque"
audio = "bgm/humoresque.m4a"
```

`words.toml`:

```toml
[words.village]
maori = "kāinga"
english = "village"
image = "word_images/village.jpg"
maori_audio = "word_audio_maori/kainga_village.mp3"
english_audio = "word_audio_english/village.mp3"
```

`stories/rona-and-the-moon/story.toml`:

```toml
title = "Rona and the Moon"
picture = "rona"
music = "dvorak-humoresque"

[[paragraphs]]
text = "Her anger was well-known in the {{village}}."
audio = "paragraph_audio/Rona_moon_01.ogg"
```

## Rules

- **Keys.** Pictures, music and story folders use hyphenated keys made from their titles. Word keys use lowercase ASCII letters, digits and underscores, made from the English translation (or the Māori word), as for [automatic Blank Links](content-admin.md). Repeated keys get a number: `light`, `light_2`.
- **Blanks.** Write `{{village}}` when the blank key is the word's key, or `{{light|light_2}}` when the blank `light` uses the word `light_2`. Each becomes a `__BLANK_<key>__` placeholder and its Blank Link. Paragraph text cannot otherwise contain `{{` or `}}`.
- **Order.** Paragraphs are listed in story order. `order` appears only when the stored value differs from the paragraph's position.
- **Media.** Each value is the name of an object already in media storage. Media files are not part of the package.
- **Status.** Stories have no draft or published status yet; it arrives with the draft-status change.

## Export

Exporting only reads the database. Against production, open a [production database shell](production-shell.md) and run, from `backend/`:

```bash
python manage.py export_content
```

It writes to `content/` at the repository root, or to `--output DIR`. On PostgreSQL it reads one consistent snapshot in a read-only transaction. Files are written in full before any is moved into place, so a failed run leaves an existing package unchanged. It does not replace existing files unless you pass `--overwrite`, and it never deletes files. Run one export at a time into a directory.

The export stops without writing anything if the database holds content the package cannot represent exactly, and lists each problem:

- a placeholder with no Blank Link, or a Blank Link with no word;
- a Blank Link whose placeholder is not in the paragraph text;
- paragraph text containing `{{` or `}}`;
- more than one application configuration.

Fix these in the admin, then export again.
