# Adding and editing stories

Stories are edited in the Django admin at `/admin/` on the backend service. See [administrator accounts](admin-account.md) for signing in. Saved changes go live straight away; there is no draft state yet.

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

## Writing a story

1. Open **Stories** and add a story. Choose the language it is written in, the language players learn, its picture and its background music. Players fill each blank with the word's form in the learning language; when the two languages differ, the form in the story language is shown as the translation. For a story that teaches English words, choose English for both.
2. Add the paragraphs in the inline form. Give each one an order number, its text and, optionally, a narration recording.
3. Mark each blank in the text with `{{key}}`, for example `The {{moon}} rose.`. Saving stores it as the placeholder `__BLANK_moon__`, which you can also type directly. The key names a word entry:
   - its key, for example `{{moon}}`; or, when no entry has that key,
   - the text of one of its forms: `{{kōrero paki}}` becomes `__BLANK_korero_paki__`.

   Text between the braces is lowercased, macrons are dropped and spaces become underscores. Saving refuses empty or unclosed braces such as `{{}}` or `{{moon`.
4. Save. If your account may add Blank Links, each new placeholder that matches exactly one word gets a Blank Link to it automatically. Any placeholder that matches no word, or more than one, is listed in a warning at the top of the page. Link those on the **Blank Links** page, where the placeholder must match the paragraph text exactly.

The game's word list is made of the words linked to the story's blanks; there is no separate word selection.

Saving never changes an existing Blank Link; to link a placeholder to a different word, edit its Blank Link or change the key in the text. If your account may delete Blank Links, saving removes the links whose placeholder is no longer in the text and lists them at the top of the page, so removed blanks leave no extra words in the story's word list.

## Menu music

Choose the main menu's background music under **Application Configuration**.
