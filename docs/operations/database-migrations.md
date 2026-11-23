# Production database migrations

The release workflow builds and deploys the backend but does not run Django migrations against the production Neon database; see [current deployment](../architecture-production-gcp.md). Apply them by hand with the steps below.

## Order relative to a release

- **Additions** (a new table, or a new nullable column or one with a default): migrate first, then release the code that uses them.
- **Removals** (a dropped field, table or relation): release the code that no longer uses them first, then migrate. Old code still running against the new schema would query something that no longer exists.

A pull request with a migration should say which order applies.

## Steps

1. Create a Neon branch of the production database as a restore point.
2. Prepare a shell as for an [administrator password reset](admin-account.md): install the backend dependencies from the repository root, change to `backend/`, and set `DATABASE_URL`, `SECRET_KEY` and `DEBUG=False` privately.
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
6. Close the shell, or unset the variables. Delete the Neon branch once you no longer need the restore point.

## Pending

| Migration | Kind | When to apply |
| --- | --- | --- |
| `core.0009_remove_story_word_bank` | Removal: drops the story word bank relation and its table, which nothing reads | After the release that contains it |
