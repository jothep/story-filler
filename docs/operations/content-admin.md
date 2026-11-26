# Adding and editing stories

Stories are edited in the Django admin at `/admin/` on the backend service. See [administrator accounts](admin-account.md) for signing in. Each story is a draft or published; players see published stories only (see [Publishing](#publishing)).

## Media libraries

Upload shared media first, so stories and words can pick it from a list.

| Library | Fields | Accepted files |
| --- | --- | --- |
| Background Music Library | Title, audio file | MP3, M4A, AAC, WAV, OGG; up to 20 MB |
| Story Picture Library | Title, picture | JPG, PNG, WebP; up to 10 MB. Saved as JPEG, scaled to fit 1920 × 1080 |
| Languages | Code (such as `en`, `mi` or `zh-Hans`) and the name players see | — |
| Word Bank | A key (unique; lowercase letters, digits and underscores), an optional picture, and one form per language: its text and optional audio | Pictures as above, scaled to fit 800 × 800; audio as above |

Replacing a file leaves the old copy in storage.

A word entry is one meaning, such as `moon`, with a picture shared by every language. Add a form for each language the word is used in: `marama` in Māori, `moon` in English, `月亮` in Chinese. Audio is optional and can be added later. To add a language, create it under **Languages** first.

## Preparing media

Prepare files before uploading them; the service checks formats but does not convert them.

| Media | Format | Notes |
| --- | --- | --- |
| Word audio and page narration | MP3, mono | Name word audio by key and language code, such as `moon.mi.mp3` |
| Background music | MP3 | Stereo is fine |
| Pictures | JPG, PNG or WebP | Saved as JPEG and scaled on upload |

`scripts/convert_audio.py` converts a batch of recordings (Ogg, WAV, M4A and others) to MP3 with your local ffmpeg (on macOS: `brew install ffmpeg`). It keeps each file's name, never changes the originals and does not replace an existing MP3 unless asked:

```bash
python3 scripts/convert_audio.py ~/Recordings/rona --speech --dry-run
```

```bash
python3 scripts/convert_audio.py ~/Recordings/rona --speech --loudness --trim
```

`--speech` mixes to mono, `--loudness` evens out the volume between recordings, `--trim` cuts silence at the start and end, and `--output DIR` writes the MP3 files to another folder.

## Uploading many files at once

Instead of attaching files one form at a time, upload a whole set and let the names decide where each file goes. Files that do not match are listed with the reason and nothing is guessed. A file for a slot that already has one replaces it (the old file stays in storage). Upload at most about 30 MB at a time.

- **Word pictures and audio:** **Word Bank** → **Upload files**. Name pictures by key, such as `moon.jpg` (or `.png`, `.webp`), and audio by key and language code, such as `moon.mi.mp3` and `moon.en.mp3`. A word needs a form in that language before its audio can be uploaded. Pictures are scaled and saved as JPEG as usual.
- **Page narration:** on a story's page → **Upload narration**. End each file name with its page number in the story's order, alone or after `page`, `-`, `_` or a space: `page-01.mp3`, `2.mp3` or `Rona_moon_03.mp3` (the names `convert_audio.py` keeps). A name like `take2.mp3` is not read as a page number.

Audio must be MP3; convert other recordings first, as described in [Preparing media](#preparing-media).

The same uploads work from the command line, from `backend/`, with the same matching rules. Run with `--dry-run` first to see where each file would go without saving anything:

```bash
python manage.py upload_narration "Rona and the Moon" ../media-work/rona-and-the-moon/mp3 --dry-run
```

```bash
python manage.py upload_word_files ~/Pictures/words --dry-run
```

The story is given by its id or exact title. The commands print which storage they write to, then each saved, planned or skipped file, and name the file each upload replaced. They fail if any file is skipped. For production, open a [production database shell](production-shell.md#uploading-media-from-the-shell) with media storage set up.

## Writing a story

1. Open **Stories** and add a story. Choose the language it is written in, the language players learn, its picture and its background music. Players fill each blank with the word's form in the learning language; when the two languages differ, the form in the story language is shown as the translation. For a story that teaches English words, choose English for both.
2. Paste the whole story into **Whole story** under **Pages**. Each page of the game is a paragraph: a blank line starts a new page, and a page longer than 240 characters is split at sentence ends. A blank counts as 10 characters and a wide character, such as Chinese, as 2. Sentence ends are `.`, `!`, `?`, `…` and `؟` before a space, and `。`, `！` and `？` anywhere; a full stop after a common abbreviation such as `Mr.` or `e.g.` is not one. Saving a change in the box replaces the pages listed below it:
   - page *n* keeps the narration recording of the story's *n*-th page, and saving warns about pages whose text changed while they had a recording, so you can check it still matches;
   - extra pages are deleted (with a warning if they had a recording) and new pages start without one;
   - pages are numbered from 0 in their new order;
   - leaving the box unchanged or empty changes nothing;
   - if you also edit pages in the page forms in the same save, those edits are saved and the box is not applied; apply it in a separate save;
   - if the pages changed after you opened the story (for example in another tab), saving is refused; copy your text, reload and apply it again.

   You can still add or edit single pages in the page forms below the box, with an order number, text and an optional narration recording.
3. Mark each blank in the text with `{{key}}`, for example `The {{moon}} rose.`. Saving stores it as the placeholder `__BLANK_moon__`, which you can also type directly. The key names a word entry:
   - its key, for example `{{moon}}`; or, when no entry has that key,
   - the text of one of its forms: `{{kōrero paki}}` becomes `__BLANK_korero_paki__`.

   Text between the braces is lowercased, macrons are dropped and spaces become underscores. Saving refuses empty or unclosed braces such as `{{}}` or `{{moon`.
4. Save. If your account may add Blank Links, each new placeholder that matches exactly one word gets a Blank Link to it automatically. Any placeholder that matches no word, or more than one, is listed in a warning at the top of the page. Link those on the **Blank Links** page, where the placeholder must match the paragraph text exactly.

The game's word list is made of the words linked to the story's blanks; there is no separate word selection.

Saving never changes an existing Blank Link; to link a placeholder to a different word, edit its Blank Link or change the key in the text. If your account may delete Blank Links, saving removes the links whose placeholder is no longer in the text and lists them at the top of the page, so removed blanks leave no extra words in the story's word list.

## Publishing

A new story starts as a **Draft**, which players do not see. **Before publishing** on the story page lists what it is missing, and the story list shows a summary per story:

- **Problems** break play and keep the story in draft:
  - no pages;
  - a blank without a word;
  - a linked word without a form in the learning language or, when the two languages differ, in the story language;
  - a story without both languages.
- **Warnings** do not block publishing, because these are often added later:
  - a page without narration or longer than 240 characters;
  - a word without audio or a picture;
  - audio that is not MP3 (see [Preparing media](#preparing-media));
  - a story without a picture or without any blanks.

Set **Status** to **Published** and save. The check runs on what was saved. If problems remain, the story stays a draft and the page lists them.

## Menu music

Choose the main menu's background music under **Application Configuration**.
