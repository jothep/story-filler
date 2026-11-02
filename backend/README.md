# Story Filler backend

The Django service exposes read-only story and configuration APIs and provides a
Django admin interface for maintaining content. The current deployment uses
Cloud Run, PostgreSQL and Google Cloud Storage. The earlier Kubernetes examples
are separate from this deployment.

Use Python 3.13. Run the following commands from the repository root.

## Local development

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
```

Set a new `SECRET_KEY` and a **local development** `DATABASE_URL` in
`backend/.env`. Use `USE_GCS=false` for local file storage. Then start your local
PostgreSQL instance and prepare the application:

```sh
python backend/manage.py migrate
python backend/manage.py runserver
```

The development environment includes the application dependencies, formatters,
linters, the lock generator and the dependency audit tool. Production installs
only `backend/requirements.txt`.

## Dependency files

| File | Purpose |
| --- | --- |
| `requirements.in` | Direct runtime dependencies and supported version ranges |
| `requirements.txt` | Generated runtime lock, including transitive dependencies and hashes |
| `requirements-dev.in` | Development tools, constrained to the runtime lock |
| `requirements-dev.txt` | Generated full development and CI environment |
| `requirements-build.in` / `.txt` | Input and hash lock for tools used only in the Alpine wheel-build stage |

Edit the `.in` files when changing dependency policy. Regenerate the `.txt`
files; do not edit individual generated versions or hashes by hand. Commit each
input change together with its updated locks.

Django stays on the 5.2 LTS series. Other direct dependencies have explicit upper
bounds so a feature-series upgrade can be reviewed. Pip, Black, Flake8, Pylint,
pip-tools and pip-audit are development dependencies. The production image uses
pip during its build, then removes the installer and its `ensurepip` bootstrap
bundle. Alpine-specific compilation runs in a separate stage; its build lock
contains setuptools, wheel and packaging, not application dependencies. Updating the application means rebuilding its locked image.

Gunicorn is installed with its `gevent` extra because the selected worker also
needs `packaging` at runtime. Keeping `gevent` as an explicit input sets its
supported version range. Validate worker imports with only the runtime lock:
development tools can otherwise supply missing dependencies and hide an error.

## Refreshing the locks

Generate locks with **CPython 3.13 on Linux amd64**. For runtime and image-build
locks, use the pinned Alpine base from the Dockerfile. Development CI uses Linux
and published wheels. When working on another platform, use a temporary Linux
container rather than resolving platform markers on macOS.

Use pip-tools 7.6.2 and pip 26.2.2 from the development lock. In the temporary
Alpine environment, install the existing `requirements-build.txt` with required
hashes and binary-only installation before generating locks. Install the compiler
and CRC32C development package versions from the Dockerfile as well; source
metadata is resolved without an untracked isolated build environment. Generate
the runtime lock first, then the development and image-build locks:

```sh
python -m piptools compile --generate-hashes --allow-unsafe --strip-extras \
  --no-emit-index-url --no-emit-trusted-host --no-emit-options --no-reuse-hashes \
  --pip-args='--no-build-isolation' \
  --output-file backend/requirements.txt backend/requirements.in

python -m piptools compile --generate-hashes --allow-unsafe --strip-extras \
  --no-emit-index-url --no-emit-trusted-host --pip-args='--only-binary=:all:' \
  --output-file backend/requirements-dev.txt backend/requirements-dev.in

python -m piptools compile --generate-hashes --allow-unsafe --strip-extras \
  --no-emit-index-url --no-emit-trusted-host --no-emit-options \
  --pip-args='--only-binary=:all:' \
  --output-file backend/requirements-build.txt backend/requirements-build.in
```

These commands preserve existing pins where possible. Add `--upgrade` deliberately
when reviewing version updates. `--allow-unsafe` includes installer packages when
required; it does not bypass hash verification.

The runtime lock includes published wheel and source hashes so it remains usable
on both glibc and musl. Installation policy remains explicit: local development
and CI use `--only-binary=:all:`. The Docker builder permits source only for
`google-crc32c` and `zope-interface`, the two packages without compatible musllinux
wheels. It disables build isolation, installs the build-tool hash lock first,
and verifies source hashes before compilation. Other source fallbacks fail.
Do not insert global `--no-binary` options into the shared runtime lock.

## Validation

Install the development lock into a fresh virtual environment, then run:

```sh
python -m pip check
python -m pip_audit --strict --require-hashes --disable-pip -r backend/requirements.txt
python -m pip_audit --strict --require-hashes --disable-pip -r backend/requirements-dev.txt
python -m pip_audit --strict --require-hashes --disable-pip -r backend/requirements-build.txt

SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
DATABASE_URL='sqlite:///:memory:' USE_GCS=false \
python backend/manage.py test core
```

The tests use an isolated SQLite database and do not validate production data or
make Google Cloud Storage requests. Also build and test the Linux image: a
successful macOS installation alone does not establish Linux compatibility.
Use the repository's image scan to check the base operating system and binary
libraries as well as Python packages. Report unresolved findings explicitly;
do not delete package metadata or suppress findings simply to pass a scan.

The audit reads every entry from the complete, hashed locks. `--disable-pip`
avoids a temporary pip environment omitting packages that it already installed
for its own use. Installation with `--require-hashes` and `pip check` still
validate distribution hashes and dependency compatibility separately.
CI also saves the JSON result and uses
[`check_dependency_audit.py`](../scripts/check_dependency_audit.py) to compare
every package name and version with its lock. Missing, skipped, duplicated or
unexpected entries fail that check. The scanner's vulnerability exit status
remains a separate required check.

Also check a fresh environment that contains only the runtime dependencies:

```sh
runtime_check_dir="$(mktemp -d)"
python3.13 -m venv "$runtime_check_dir"
"$runtime_check_dir/bin/python" -m pip install \
  --require-hashes --only-binary=:all: -r backend/requirements.txt
"$runtime_check_dir/bin/python" -m pip check
"$runtime_check_dir/bin/python" -c \
  'from gunicorn.workers.ggevent import GeventWorker'
```

Start the built image and check its HTTP responses as well. Django unit tests
alone do not run the configured Gunicorn worker.

## Python style and static checks

Use the locked Black and Flake8 versions from the development environment:

```sh
python -m black --check backend scripts
python -m flake8 backend scripts
```

Black reads the root `pyproject.toml`; Flake8 reads the root `.flake8`. Both use
88 columns. Flake8 allows only the E203 slice-spacing and W503 operator-line-break
differences needed to match Black. The standalone password-management script
has one documented E402 exception to preserve Django initialization before its
auth import.

The checks cover maintained backend code and repository scripts. Generated
`core/migrations/` files are excluded from formatting and linting; Django's
system checks and `makemigrations --check --dry-run` check model consistency.
From `backend/`, use `python -m black --check .` and `python -m flake8 .` to check
only the backend with the same parent-directory configuration.

Pylint uses the root `.pylintrc` and `pylint-django` to understand Django's model
fields and generated managers. Its existing score threshold is 7.0; any error or
fatal finding also fails the check, regardless of score. Other suggestions stay
visible. Run it with local-only settings:

```sh
(
  cd backend
  SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  DATABASE_URL='sqlite:///:memory:' USE_GCS=false USE_S3=false DEBUG=false \
  python -m pylint --rcfile=../.pylintrc \
    core maori_story_project manage.py change_admin_password.py
)
python -m unittest discover -s scripts -p 'pylint_config_test.py'
```

The configuration tests accept valid Django model access and verify that real
missing attributes and undefined names still fail, including in code scoring
above 7.0. The plugin and its tests are development tools, not runtime dependencies.

## Container

```sh
docker build --platform linux/amd64 -f backend/dockerfile -t story-filler-backend:local backend
```

The official Python 3.13.18 Alpine 3.24 base is pinned to a multi-platform digest.
Build and test `linux/amd64`, the deployment target. Refresh the base and stable
Alpine packages together, then repeat native-library, PostgreSQL, HTTP and image
scans. A lock refresh alone does not update the operating system.

The first stage compiles the two required native extensions with fixed build-tool
versions, `build-base` and `crc32c-dev`. The final stage installs only the 37
runtime packages and the CRC32C shared library. It retains package metadata,
CA certificates, SQLite and Python runtime libraries. Compilers, headers,
setuptools, wheel, pip and ensurepip are absent from the final image.

The runtime account stays at UID 100/GID 101 to preserve existing local volume
ownership. Static files are collected as that account with a temporary build-only
key and SQLite settings. The default Gunicorn command, three gevent workers,
port 8000 and configurable local/GCS storage are unchanged.

The base change addresses eight of the earlier nine HIGH advisory groups through
updated or removed components. SQLite remains affected by CVE-2026-119373 even
though the Alpine feed does not report it. Keep that issue separate from a clean
Trivy result. The [advisory review](../docs/dependency-findings.md) records the
comparison, the rejected Distroless candidate and the remaining update path.

Run the persistent [image verification](../scripts/README.md#built-image-verification)
after building. It checks the exact dependency set, native features, 31 Django
tests and storage configuration offline, then runs the unmodified image against
a temporary PostgreSQL database and verifies API/static responses and shutdown.
CI runs this before merge without cloud credentials; only reviewed `main`
releases can authenticate and publish.

Gunicorn's optional control socket is disabled. Cloud Run manages the process;
the container does not need a separate local control interface or a writable
home directory for it.

The installer is not needed by the running service. It is removed after
installation and `pip check`, along with the `ensurepip` bundle that can recreate
it. Image scanning found vulnerable copies of libraries bundled inside pip;
updating unrelated top-level packages would not replace those copies. Removing
the unused installer removes that code from the runtime image. Development and
lock-generation environments keep pip; their installed dependency audit and the
runtime image scan cover different scopes.

Rebuild the image after a lock change. Changing the lock does not update an
already running service. Database migrations and production deployment remain
separate steps in the repository's release process.

## Upgrade references

- [Django 5.2.18 security fixes](https://docs.djangoproject.com/en/5.2/releases/5.2.18/)
- [Django REST framework 3.18.3 release](https://github.com/encode/django-rest-framework/releases/tag/3.18.3)
- [Pillow 13.0.0 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
- [Gunicorn 26.2.0 release](https://github.com/benoitc/gunicorn/releases/tag/26.2.0)
- [gevent release notes](https://www.gevent.org/changelog.html)
- [pip-tools: reproducible locks and environment markers](https://pip-tools.pypa.io/en/latest/)
