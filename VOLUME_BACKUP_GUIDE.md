# Local Compose backup and isolated recovery

This workflow backs up one PostgreSQL 16 database and its local Docker media
volume. It restores into new resources for inspection. It does not switch an
existing application to those resources or operate the hosted Neon/GCS service.

Use `scripts/local_recovery.py`. The previous `backup.sh`, `backup-volumes.sh`,
`restore-volumes.sh` and `restore-volumes-ec2.sh` entry points refuse execution.
Their old archives are not accepted by the new tool.

## What the backup contains

A completed backup has exactly three files:

- `database.dump`: a PostgreSQL custom-format logical export, made with `pg_dump`.
- `media.tar`: the media files and directories, read from the source volume.
- `manifest.json`: format version, PostgreSQL major version, file sizes and SHA-256
  checksums. It contains no database password or connection address.

The output directory is new and private to its owner. The manifest is written
last; a failed backup is incomplete and must not be treated as usable. The tool
does not delete old backups or overwrite an existing output directory.

The database export does not include cluster-wide roles or server configuration.
The tool does not copy application environment files or container settings. Keep
those configuration sources separately. The backup
files themselves contain application data, which may be private; keep them out of
Git. The repository ignores `backups/`, but storage and access permissions still
need to be managed when copying a backup elsewhere.

## Prepare the source

Use Python 3.13 and a local Docker Engine. All Docker calls require an explicit
Unix socket. Remote TCP and SSH endpoints are rejected. From the repository root:

```sh
recovery_host="$(docker context inspect --format '{{.Endpoints.docker.Host}}')"
recovery_image="$(PYTHONPATH=scripts python3 -c 'from local_recovery import POSTGRES_IMAGE; print(POSTGRES_IMAGE)')"
docker --host "$recovery_host" pull "$recovery_image"
python3 scripts/local_recovery.py --help
```

The image is an official PostgreSQL 16 image pinned by digest. The tool does not
pull images implicitly. Review and retest deliberate image updates.

Identify the actual Compose project, database container and media volume. Do not
infer them from the current directory name. The tool checks Compose ownership,
the running database and stopped backend before reading data. It also rejects a
media volume mounted read-write by a running container.

Pause application writes for the whole backup window. Stop the source backend
using its existing Compose project/configuration, and stop any other writer you
operate. The explicit `--writers-stopped` flag confirms that external writers
have also been paused. Docker checks cannot establish that an unrelated database
client has stopped writing.

The database stays running: `pg_dump` takes a consistent database snapshot.
Pausing application and media writes keeps the database references and files in
the same stable window. Copying a running PostgreSQL data directory with `tar`
is not a substitute for this procedure.

## Create and verify a backup

This example assumes a development stack deliberately created with project name
`story-filler-dev`. Substitute its actual names if yours differ. Supply a new
output directory each time:

```sh
mkdir -p ./backups
python3 scripts/local_recovery.py backup \
  --docker-host "$recovery_host" \
  --project story-filler-dev \
  --db-container maori-dev-db \
  --database maori_story_dev \
  --db-user devuser \
  --media-volume story-filler-dev_media_dev_data \
  --output ./backups/manual-20261102 \
  --writers-stopped

python3 scripts/local_recovery.py verify --bundle ./backups/manual-20261102
```

Both commands must succeed. The tool never stops or restarts the source service;
resume the writers yourself after recording the backup result. If backup fails,
inspect the reported stage, retain the original data and use a new output
location for the next attempt.

Offline verification checks the manifest, required files, checksums, PostgreSQL
archive header and media members. It rejects links, special files, duplicate or
escaping paths and truncated archives. Limits are 2 GiB of bundle data, 2 GiB of
expanded media, 100,000 archive members and 512-character paths. Empty media is
valid. Verification checks integrity; it does not prove the database can be
restored or that the backup's source is trustworthy.

## Restore into an isolated environment

Only restore backups from a trusted database that you control. PostgreSQL dumps
can contain executable database definitions; a matching checksum does not make
an unknown dump safe. The separate acknowledgement is required:

```sh
python3 scripts/local_recovery.py restore \
  --docker-host "$recovery_host" \
  --bundle ./backups/manual-20261102 \
  --trusted-backup
```

The tool takes a private snapshot of the backup, validates it, and checks the
PostgreSQL archive directory before creating destination volumes. It allocates
random resource names and checks their operation labels to avoid reusing an
existing volume. Restoring the database uses one transaction and stops on errors.
Media are restored from validated file/directory entries with normalized
permissions (files `0644`, directories `0755`) and temporary ownership
`1000:1000`, then read back for content
verification. This ownership is for the recovery environment; it is not an
assumption about the production application's runtime user.

The recovery PostgreSQL container has no network or published port. Helpers have
no network, host directory mount or Docker socket mount. The source database,
media volume and running application are not replaced. On failure, cleanup is
limited to resources whose operation label matches this attempt. An interrupted
process can leave its own resources behind; inspect the reported identifiers
before removing anything.

Success reports the new recovery container and volumes. Inspect the restored
records and media, then assess application configuration, file ownership,
permissions and an application-level smoke check before planning any separate
cutover. This tool does not claim to perform that cutover. Keep the old environment
until the replacement has been independently validated.

Remove only the specific disposable recovery resources you no longer need.
Never use a global prune or a wildcard to clean up a recovery attempt.

## Repeat the tests

The archive and operation tests use temporary files and simulated Docker
responses. They need only the Python standard library:

```sh
python3 -m unittest discover -s scripts -p '*recovery*_test.py'
python3 -m unittest discover -s scripts -p 'restore_safety_test.py'
```

Run the integration check on a dedicated, otherwise idle Docker Engine because
it observes resource creation/deletion during failure cases. It uses the pinned
image above and synthetic data. It creates
its own isolated source and destination resources, runs the CLI, checks restored
records, constraints, sequences and media, and checks that source sentinels are
unchanged. It also exercises rejected and failed recovery attempts:

```sh
python3 scripts/recovery_integration.py --docker-host "$recovery_host"
```

The dedicated [recovery workflow](.github/workflows/verify-local-recovery.yml)
runs these checks on Linux without cloud credentials. Dated results are in the
[verification record](docs/verification.md). These checks do not establish
production recovery times or test the hosted database's recovery features.

## References

- PostgreSQL: [pg_dump and consistent logical exports](https://www.postgresql.org/docs/16/app-pgdump.html).
- PostgreSQL: [pg_restore, transactions and trusted sources](https://www.postgresql.org/docs/16/app-pgrestore.html).
- Docker: [volume creation can reuse an existing name](https://docs.docker.com/reference/cli/docker/volume/create/).
