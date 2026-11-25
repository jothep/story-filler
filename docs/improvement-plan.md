# Improvement plan: content workflow, code quality and repository cleanup

**Status:** in progress; phase 1 (quick wins) done on 24 November 2026; phase 2 revised on 25 November 2026 and under way. **Created:** 18 November 2026.

This plan covers the content workflow, application code and repository layout.
It does not change the hosting model (GitHub Pages, Cloud Run, Neon, GCS).

On 25 November 2026 the direction changed in two ways:

- Story Filler becomes a word-learning game for any language, not only te reo Māori. Each story is written in one language and teaches words in one learning language: Māori, Chinese, any other language, or the story's own language (for example, English words in an English story).
- Content stays in the Django admin, which gains the automation instead. Story Filler has one author, and a separate content package or folder import would add manual steps rather than remove them.

## Why

Adding or changing a story takes a lot of manual work and is hard to manage.
The one live story, *Rona and the Moon*, needs 43 media files and about 27 separate saves across six Django admin pages:

| Item | Files |
| --- | --- |
| Paragraph narration (8 paragraphs) | 8 |
| Words (11): image, Māori audio, English audio | 33 |
| Cover image and background music | 2 |

Its 13 blanks each need a separate Blank Link entry. Content exists only in Neon and GCS, so it cannot be reviewed, diffed or rolled back, and a fresh database starts with no stories.

## Goals

- Teach words in any language, with each story fixed to one learning language.
- Enter a story in the admin without uploading media one file at a time or linking blanks by hand. Audio may be missing and added later.
- See what a story is missing before it is published.
- Record a source and licence for every published asset, and generate credits from that record.
- Make the repository easy to navigate for a first-time reader.

Content history and rollback are not goals.

## Findings

| Area | Finding | Evidence |
| --- | --- | --- |
| Data model | Authors must select a story word bank, but the API derives the word list from Blank Links. The field is never read | [models.py](../backend/core/models.py#L199), [serializers.py](../backend/core/serializers.py#L138) |
| Data model | Each `__BLANK_x__` placeholder needs a manual Blank Link on a separate admin page, with the placeholder typed again | [models.py](../backend/core/models.py#L302) |
| Languages | The word model, the API and the game assume Māori words with English translations (`maori_word`, `english_translation` and their audio) | [models.py](../backend/core/models.py), [serializers.py](../backend/core/serializers.py), `frontend/src/components` |
| Admin entry | Each paragraph is a page in the game and is typed into its own form; every media file is uploaded through its own form field | [admin.py](../backend/core/admin.py) |
| Publishing | Saving in admin publishes immediately; there is no draft state or preview | [ADMIN_GUIDE.md](history/ADMIN_GUIDE.md) Q4 |
| Media | Live audio mixes 22 MP3, 8 Ogg and 1 M4A files. Images are compressed on upload; audio is not processed | [models.py](../backend/core/models.py#L41), [AUDIO_DEBUG_GUIDE.md](AUDIO_DEBUG_GUIDE.md) |
| Media | Replacing or deleting an asset leaves the old object in GCS | No cleanup code in `backend/core` |
| Credits | Credits are hard-coded and listed one music track; the live menu track is a different piece. Both pieces have been credited since 23 November, but the credits are still hard-coded and assets carry no source or licence fields | [credits.js](../frontend/src/constants/credits.js#L21) |
| Admin code | The same audio MIME helper is copied into four admin classes | [admin.py](../backend/core/admin.py) |
| Frontend | Drag and drop supports mouse and touch only, so the game cannot be played with a keyboard | [StoryPlayerUI.jsx](../frontend/src/pages/StoryPlayerUI.jsx#L64) |
| Frontend | Styling is split across 78 inline style objects, CSS files, a styles module and theme tokens | `frontend/src` |
| Tests | 55 frontend and 40 backend tests, but no end-to-end test of the core story flow | `frontend/src`, `backend/core` |
| Repository | 18 Chinese-language guides sit in the root; 9 carry historical banners and several are not linked from anywhere. The admin guide describes an older data model and includes account details | Root directory |
| Developer setup | A fresh local database has no sample story | [README.md](../README.md) |

## Workstreams

### 1. Repository cleanup

- Move the 18 root guides, the two Chinese guides in `terraform/`, the root `deploy.sh` and the EC2-era scripts (`start-instance.sh`, `stop-instance.sh`, `instance-status.sh`, `export-data.sh`, `import-data.sh`) to [`docs/history/`](history/README.md), with an English index. Archive rather than delete, keeping the original text.
- Move the root `Requirements.txt` (the original course requirements, not a pip file) to `docs/history/course-requirements.txt`.
- Replace guides that still describe current operations with short English pages under [`docs/operations/`](operations/): administrator accounts now; the content admin guide and the production migration procedure with workstream 2.
- Remove account details from the archived admin guide.
- Keep the four retired backup and restore entry points (`backup.sh`, `scripts/backup-volumes.sh`, `scripts/restore-volumes.sh`, `scripts/restore-volumes-ec2.sh`). They refuse to run, point to the current recovery tool, and are covered by `scripts/restore_safety_test.py`.
- Keep `Infra/` and `demo/`: [ARCHITECTURE.md](ARCHITECTURE.md) cites them as historical evidence. Label them clearly instead.
- Update links in README and the docs index.

**Done when:** the root holds only README, LICENSE, SECURITY, CHANGELOG, VOLUME_BACKUP_GUIDE, the retired `backup.sh` entry point, configuration files and the code and infrastructure directories (`backend/`, `frontend/`, `scripts/`, `terraform/`, `docs/`, plus the retained `Infra/` and `demo/`); current docs are in English, with original-language records only in `docs/history/`; every internal link resolves.

### 2. Data model and admin fixes

- Remove `Story.word_bank` with a migration. In the same change, remove its `filter_horizontal` and fieldset entries in `StoryAdmin` and its `prefetch_related` entry in `StoryDetailAPIView.get_queryset()`; otherwise story reads and admin editing fail.
- Create Blank Links automatically when a paragraph is saved, matching each placeholder to a word.
- Move the audio MIME helper into one shared function.
- Draft/published status moved to workstream 4, where it pairs with the completeness check.
- Do not delete media from admin saves; stored-file cleanup is deferred (see [Deferred](#deferred)).
- Write an English content admin guide for the new model, and an English procedure for running production migrations, under `docs/operations/`.

**Done when:** a story can be created without visiting the Blank Link page, and no admin field is ignored by the API.

### 3. Words in any language

- Replace the Māori-specific word fields with:
  - **word entries**: a unique key of lowercase letters, digits and underscores (used in blanks, such as `moon`, and accepted by the game's placeholder parser) and an image shared by every language;
  - **word forms**: one per entry and language, with its text and optional audio.
- The existing word rows become the word entries, so Blank Links keep pointing at them. Only their Māori and English columns move into forms.
- Give each story a story language and a learning language. A blank shows the word in the learning language, with the story-language form as its translation when the two differ. When they are the same, only that form is shown.
- Keep the model ready for players to choose the learning language before opening a story, without building that choice now. The language stays fixed during play.
- Ship it in three releases so the live game keeps working:
  1. Add the new tables and fields. The migration copies each word's Māori and English text and audio into forms, derives its key from the English translation, and sets existing stories to English with Māori as the learning language. From this release the admin edits the forms, and the API derives the old field names from them, so the current game keeps working and no edit goes stale. This is an addition: migrate, then release.
  2. Switch the game to the new fields, label audio buttons by language name, show a placeholder when a word has no image, and make the About text language-neutral.
  3. Remove the old database columns. This is a removal: release, then migrate. The API keeps returning the old field names, derived from the forms, for at least a week after the game switches, so browsers with an older game bundle still work.
- Keep the cloud resource names (`maori-story-*`) and the Django project name. Renaming them changes infrastructure with no benefit to players.

**Done when:** *Rona and the Moon* plays as before from the new model, and a story can teach Chinese or English words without code changes.

### 4. Admin entry automation

- **Pages from pasted text.** Paste a whole story into the story form. A blank line starts a new page (paragraph), and a page longer than the limit is split at sentence ends. Existing pages keep their audio when their text is unchanged.
- **Blanks written inline.** Write `{{moon}}` in the text. Saving stores it as the existing `__BLANK_moon__` placeholder, so the API and the game's parser stay unchanged, and links it to the word entry with that key. Links whose placeholder is no longer in the text are removed, so players see no stale answer choices.
- **Many files at once.** Drop a set of files on a word or story page and match them by name: `moon.jpg` is the image of `moon`, `moon.mi.mp3` its Māori audio, `page-03.mp3` the narration for page 3. Unmatched files are listed, not guessed.
- **Completeness check and draft status.** Each story shows what it is missing. Problems that break play keep the story in draft: a blank without a word, a word without a form in the learning language, or, when the two languages differ, without a form in the story language. Missing audio, a missing image or a long page is a warning only, because audio is often added later. The public API serves published stories only; the migration that adds the status marks existing stories as published.
- **Formats.** Converting media is part of preparing it, not of uploading or releasing it. A local script converts batches of recordings to MP3 with the author's ffmpeg, the format rules are documented, and the admin only checks formats and warns about audio that is not MP3. The backend image gains no media tools. Images keep their current resize and compression on upload.

**Done when:** a new story can be entered in the admin by pasting its text and dropping its files, without visiting the Blank Link page, and the story list shows each story's state and missing items.

### 5. Media provenance and credits

- Add provenance to every asset: source, creator or tool, licence, credit text and date.
- Replace the current word and paragraph audio with generated audio whose terms allow public redistribution, uploaded through workstream 4.
  - English: a text-to-speech service.
  - Te reo Māori: a tool that explicitly supports the language, with pronunciation checked by a fluent speaker where possible.
- Credit Gemini for the word images and cover.
- Correct the music credit to match the tracks actually used.
- Generate the credits section from the provenance records instead of `credits.js`.

**Done when:** every asset served from GCS has a provenance record and the in-app credits match them.

### 6. Frontend quality

- Add keyboard drag support (dnd-kit `KeyboardSensor`) and screen-reader announcements.
- Consolidate styling on one approach with shared theme tokens.
- Add one end-to-end test (Playwright) for open story → fill blanks → complete, against seeded content.
- Check readability of the pixel font at its smallest sizes on mobile, and how text in other scripts (such as Chinese) falls back from it.

**Done when:** the full story can be completed with a keyboard and the end-to-end test runs in CI.

### 7. More stories

- Add two or three stories through the admin automation, reusing the shared word entries, including one that teaches a language other than Māori.

## Order

1. **Quick wins (done):** workstream 1, workstream 2 except draft status, and the credit corrections from workstream 5.
2. **Languages and admin entry:** workstream 3 (three releases), then workstream 4, including draft status.
3. **Content and polish:** audio replacement and generated credits (workstream 5), workstream 6, then workstream 7.

## Deferred

These were planned for phase 2 before the change of direction. They wait until they would remove work for the author.

- A content package in the repository (TOML files with an `export_content` command), a folder import, CI checks of content, and a read-only admin. The export was written and closed unmerged; branch `feat/export-content` keeps it.
- Splitting one long narration into pages by silence, and naming uploads by content hash.
- Removing storage objects that no record references.

## Follow-ups

- **picomatch advisory ([GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)).** The full-tree npm audits allow it through `frontend/audit-allowlist.json`, because no patched release existed on 18 November 2026. The entry has no expiry date and nothing sends a reminder. Check from time to time whether picomatch has a release above 4.0.7. When it does, update the frontend lock, confirm `npm run audit:full` no longer reports the advisory, and delete the entry. See [dependency findings](dependency-findings.md#frontend-picomatch-advisory-allowed-without-a-patch-18-november).

## Open decisions

- Which text-to-speech tools to use for English and te reo Māori, and whether their terms allow public redistribution.
- Whether to also publish a static JSON snapshot of stories to Pages. It would remove the cold start from the visitor path, but Cloud Run and Neon would no longer serve public reads.
