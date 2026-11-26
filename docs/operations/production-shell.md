# Production database shell

[Migrations](database-migrations.md) and [administrator password resets](admin-account.md) run Django management commands on your machine against the production Neon database. Take the connection from the Cloud Run service itself, so the commands reach the database the site uses and not another Neon branch.

## Before you start

- Install the backend dependencies from the repository root as described in the [backend README](../../backend/README.md), for example into a `.venv` at the root, and activate them.
- Sign in to gcloud with an account that can read the `maori-story-backend` Cloud Run service.

## Open the shell

From the repository root:

```bash
cd backend
```

```bash
export DATABASE_URL="$(gcloud run services describe maori-story-backend --project=jaskojothep --region=us-central1 --format=json | python3 -c 'import json,sys; env=json.load(sys.stdin)["spec"]["template"]["spec"]["containers"][0]["env"]; print(next(e["value"] for e in env if e["name"]=="DATABASE_URL"))')"
```

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" DEBUG=False
```

If your shell traces commands (`set -x`), turn that off first with `set +x`, or the trace will print the connection string. The first command prints nothing when it succeeds; an error means `DATABASE_URL` was not set, so stop there. The connection string is not shown and does not enter shell history. `gcloud run services describe --format=json` returns the service in the Knative (v1) shape that the lookup reads. Migrations and password changes do not need the production `SECRET_KEY`; a random value satisfies the settings module. Values set in the shell take precedence over a local `backend/.env`.

## Check the target before writing

```bash
python manage.py shell -c "from django.db import connection as c; s=c.settings_dict; print('host:', s['HOST'], '| db:', s['NAME'])"
```

The host must be the Neon endpoint in the service's `DATABASE_URL`. Stop if the command shows another host, `localhost`, or an error.

## Uploading media from the shell

`upload_narration` and `upload_word_files` write files to media storage as well as rows to the database. In the same shell, also set:

```bash
export USE_GCS=true GS_BUCKET_NAME=maori-story-media GS_DEFAULT_ACL=
```

The empty `GS_DEFAULT_ACL` uploads without an object ACL. The bucket grants public read to everyone through its IAM policy, so the files are public anyway, and an account that may create objects but not set their ACLs can still upload. The service itself keeps its default (`publicRead`). Storage uses Application Default Credentials. Create them once with `gcloud auth application-default login`, signed in with an account that may create objects in the bucket. Each command first prints the storage it writes to; it must say `GoogleCloudStorage (bucket maori-story-media)`. Always run with `--dry-run` first. Replaced files stay in the bucket, and the output names them, so a page can be pointed back at its old file if needed. After an upload, open one new file's public URL to check it is readable.

## Neon branches

Create restore points from the `production` branch, and give them an expiry. After a branch is created, Neon shows the connection details for the new branch. Close that dialog: its connection string points at the new branch, not at production.

## Close the shell

```bash
unset DATABASE_URL SECRET_KEY DEBUG
```

Then deactivate the virtual environment or close the window.
