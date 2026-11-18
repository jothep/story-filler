# Improvement plan: content workflow, code quality and repository cleanup

**Status:** planned, not started. **Created:** 18 November 2026.

This plan covers the content workflow, application code and repository layout.
It does not change the hosting model (GitHub Pages, Cloud Run, Neon, GCS).

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

- Add a story by writing one story file and preparing only media that is new.
- Review content changes like code: pull request, CI checks, revert.
- Record a source and licence for every published asset, and generate credits from that record.
- Make the repository easy to navigate for a first-time reader.

## Findings

| Area | Finding | Evidence |
| --- | --- | --- |
| Data model | Authors must select a story word bank, but the API derives the word list from Blank Links. The field is never read | [models.py](../backend/core/models.py#L199), [serializers.py](../backend/core/serializers.py#L138) |
| Data model | Each `__BLANK_x__` placeholder needs a manual Blank Link on a separate admin page, with the placeholder typed again | [models.py](../backend/core/models.py#L302) |
| Publishing | Saving in admin publishes immediately; there is no draft state or preview | [ADMIN_GUIDE.md](../ADMIN_GUIDE.md) Q4 |
| Media | Live audio mixes 22 MP3, 8 Ogg and 1 M4A files. Images are compressed on upload; audio is not processed | [models.py](../backend/core/models.py#L41), [AUDIO_DEBUG_GUIDE.md](AUDIO_DEBUG_GUIDE.md) |
| Media | Replacing or deleting an asset leaves the old object in GCS | No cleanup code in `backend/core` |
| Credits | Credits are hard-coded and list one music track; the live menu track is a different piece. Assets carry no source or licence fields | [credits.js](../frontend/src/constants/credits.js#L21) |
| Admin code | The same audio MIME helper is copied into four admin classes | [admin.py](../backend/core/admin.py) |
| Frontend | Drag and drop supports mouse and touch only, so the game cannot be played with a keyboard | [StoryPlayerUI.jsx](../frontend/src/pages/StoryPlayerUI.jsx#L64) |
| Frontend | Styling is split across 78 inline style objects, CSS files, a styles module and theme tokens | `frontend/src` |
| Tests | 55 frontend and 40 backend tests, but no end-to-end test of the core story flow | `frontend/src`, `backend/core` |
| Repository | 18 Chinese-language guides sit in the root; 9 carry historical banners and several are not linked from anywhere. The admin guide describes an older data model and includes account details | Root directory |
| Developer setup | A fresh local database has no sample story | [README.md](../README.md) |

## Workstreams

### 1. Repository cleanup

- Review each root guide (ADMIN_GUIDE, ADMIN_PASSWORD_GUIDE, CHANGELOG-2026-04-30, CLOUD_RUN_ENV_VARS, CLOUD_RUN_URL_STABILITY, CODE_ANALYSIS, COST_COMPARISON, CREATE_ADMIN, DATABASE_MIGRATION_GUIDE, DEPLOYMENT, DEPLOYMENT_QUICKSTART, DEPLOYMENT_URLS, MIGRATION_GUIDE, ORACLE_CLOUD_SETUP, PUBLIC_ACCESS_GUIDE, REFACTORING_PLAN, TERRAFORM_GUIDE, WORKFLOW). Move historical ones to `docs/history/` with an index, or remove them if they add no evidence.
- Where a guide still describes current operations, replace it with a short English page under `docs/operations/`.
- Rewrite the admin guide for the current model, without account details.
- Rename the root `Requirements.txt` (the original course brief, not a pip file) and move it to `docs/history/`.
- Review the EC2-era scripts in `scripts/` (`start-instance.sh`, `stop-instance.sh`, `instance-status.sh`, `restore-volumes-ec2.sh`, `export-data.sh`, `import-data.sh`) and the root `deploy.sh` and `backup.sh`, and archive or remove them.
- Keep `Infra/` and `demo/`: [ARCHITECTURE.md](ARCHITECTURE.md) cites them as historical evidence. Label them clearly instead.
- Update links in README and the docs index.

**Done when:** the root holds only README, LICENSE, SECURITY, CHANGELOG, configuration files and the code and infrastructure directories (`backend/`, `frontend/`, `scripts/`, `terraform/`, `docs/`, plus the retained `Infra/` and `demo/`); public docs are in English; every internal link resolves.

### 2. Data model and admin fixes

- Remove `Story.word_bank` with a migration. In the same change, remove its `filter_horizontal` and fieldset entries in `StoryAdmin` and its `prefetch_related` entry in `StoryDetailAPIView.get_queryset()`; otherwise story reads and admin editing fail.
- Create Blank Links automatically when a paragraph is saved, matching each placeholder to a word.
- Move the audio MIME helper into one shared function.
- Add a draft/published status to Story; the public API returns published stories only. The story package carries the same status (workstream 3).
- Delete the stored file when an asset is replaced or removed (or rely on workstream 4's cleanup).

**Done when:** a story can be created without visiting the Blank Link page, and no admin field is ignored by the API.

### 3. Content as code

- Define a story package:

  ```text
  content/
    words.yaml                  # shared lexicon: Māori, English, media, provenance
    stories/rona-and-the-moon/
      story.yaml                # title, status, cover, music, paragraphs
      media/
  ```

- `status` (`draft` or `published`) maps directly to the Story field: import sets it, export writes it back, and the public API serves published stories only. A story without a status imports as a draft.
- Write blanks inline in paragraph text, for example `Rona looked up at the {{marama}}.`. The importer translates each one into the existing `__BLANK_<key>__` placeholder and creates its Blank Link, so the API and the frontend parser stay unchanged. Keys are ASCII slugs, because the parser accepts only `[A-Za-z0-9_]` and Māori words can contain macrons.
- Add `export_content` to bootstrap the package from the live story, then `import_content` to validate, process media, upload to GCS and upsert the database. Imports are repeatable and support a dry run.
- Add a CI job that checks every blank resolves to a word, every word has its required media, files meet format and size rules, and provenance is complete.
- Use the package as seed data for local development and tests.
- Treat the repository as the source of truth; make content models read-only in admin.

**Done when:** *Rona and the Moon* round-trips through export and import with no data change, and a pull request that breaks a blank fails CI.

### 4. Media processing

- Audio: one format (MP3), mono for speech, loudness normalisation (ffmpeg `loudnorm`), trimmed silence.
- Recordings: support one long take split by silence and named from a word list or paragraph order.
- Images: fixed sizes and format.
- Name uploaded files by content hash. Storage uses `GS_FILE_OVERWRITE=False`, which renames a file on collision, so the importer checks whether the hash key already exists and reuses it instead of saving again.
- Serve hash-named files with long cache headers, and remove objects no package references.

**Done when:** every live asset passes the format checks, a repeated import uploads no new objects, and GCS holds no unreferenced objects.

### 5. Media provenance and credits

- Add provenance to every asset: source, creator or tool, licence, credit text and date.
- Replace the current word and paragraph audio with generated audio whose terms allow public redistribution, produced through workstream 4.
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
- Check readability of the pixel font at its smallest sizes on mobile.

**Done when:** the full story can be completed with a keyboard and the end-to-end test runs in CI.

### 7. More stories

- Add two or three stories through the new pipeline, reusing the shared lexicon.

## Order

1. **Quick wins:** workstream 1, workstream 2 except draft status, and the credit corrections from workstream 5.
2. **Pipeline:** workstreams 3 and 4, starting with `export_content`.
3. **Content and polish:** audio replacement and generated credits (workstream 5), draft status, workstream 6, then workstream 7.

## Open decisions

- Which text-to-speech tools to use for English and te reo Māori, and whether their terms allow public redistribution.
- Where media originals live: in the repository, Git LFS or a private bucket.
- Whether admin stays editable for urgent fixes once the repository is the source of truth.
- Whether to also publish a static JSON snapshot of stories to Pages. It would remove the cold start from the visitor path, but Cloud Run and Neon would no longer serve public reads.
