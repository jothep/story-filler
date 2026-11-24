# Production database migrations

The release workflow builds and deploys the backend but does not run Django migrations against the production Neon database; see [current deployment](../architecture-production-gcp.md). Apply them by hand with the steps below.

## Order relative to a release

- **Additions** (a new table, or a new nullable column or one with a default): migrate first, then release the code that uses them.
- **Removals** (a dropped field, table or relation): release the code that no longer uses them first, then migrate. Old code still running against the new schema would query something that no longer exists.

A pull request with a migration should say which order applies.

## Steps

Only one person runs production migrations at a time. Agree who it is before step 1.

1. Create a Neon branch from `production` as a restore point, as described under [Neon branches](production-shell.md#neon-branches).
2. Open a [production database shell](production-shell.md) and check that it targets the service's database.
3. Check what will run:

   ```bash
   python manage.py showmigrations core
   python manage.py migrate --plan
   ```

4. Apply:

   ```bash
   python manage.py migrate
   ```

5. Check that the story list and a story load in the game, and that the admin opens.
6. Close the shell. Delete the Neon branch, or let it expire, once you no longer need the restore point.

## Pending

None.

## Applied

| Migration | Kind | Applied |
| --- | --- | --- |
| `core.0009_remove_story_word_bank` | Removal: drops the story word bank relation and its table | 2026-11-24, after the release that contains it |
