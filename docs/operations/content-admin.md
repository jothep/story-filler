# Adding and editing stories

Stories are edited in the Django admin at `/admin/` on the backend service. See [administrator accounts](admin-account.md) for signing in. Saved changes go live straight away; there is no draft state yet.

## Media libraries

Upload shared media first, so stories and words can pick it from a list.

| Library | Fields | Accepted files |
| --- | --- | --- |
| Background Music Library | Title, audio file | MP3, M4A, AAC, WAV, OGG; up to 20 MB |
| Story Picture Library | Title, picture | JPG, PNG, WebP; up to 10 MB. Saved as JPEG, scaled to fit 1920 × 1080 |
| Word Bank | Māori word (unique), English translation, optional picture and Māori and English audio | Pictures as above, scaled to fit 800 × 800; audio as above |

Replacing a file leaves the old copy in storage.

## Writing a story

1. Open **Stories** and add a story. Choose its picture and background music.
2. Add the paragraphs in the inline form. Give each one an order number, its text and, optionally, a narration recording.
3. Mark each blank in the text with a placeholder `__BLANK_<key>__`. The key names a word in the Word Bank:
   - its English translation in lowercase, for example `__BLANK_moon__`; or
   - its Māori word without macrons, with underscores for spaces, for example `__BLANK_korero_paki__` for *kōrero paki*.
4. Save. Each new placeholder that matches exactly one word gets a Blank Link to it automatically. Any placeholder that matches no word, or more than one, is listed in a warning at the top of the page. Link those on the **Blank Links** page, where the placeholder must match the paragraph text exactly.

The game's word list is made of the words linked to the story's blanks; there is no separate word selection.

Saving never changes or removes an existing Blank Link. To link a placeholder to a different word, edit its Blank Link. If you remove a placeholder from the text, delete its Blank Link too; otherwise its word stays in the story's word list.

## Menu music

Choose the main menu's background music under **Application Configuration**.
