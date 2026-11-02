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

Edit the `.in` files when changing dependency policy. Regenerate the `.txt`
files; do not edit individual generated versions or hashes by hand. Commit each
input change together with its updated locks.

Django stays on the 5.2 LTS series. Other direct dependencies have explicit upper
bounds so a feature-series upgrade can be reviewed. Pip, Black, Flake8, Pylint,
pip-tools and pip-audit are development dependencies. The production image uses
pip during its build, then removes the installer and its `ensurepip` bootstrap
bundle. Updating the application means rebuilding its locked image.

Gunicorn is installed with its `gevent` extra because the selected worker also
needs `packaging` at runtime. Keeping `gevent` as an explicit input sets its
supported version range. Validate worker imports with only the runtime lock:
development tools can otherwise supply missing dependencies and hide an error.

## Refreshing the locks

Generate locks with **CPython 3.13 on Linux amd64**, matching CI and the production
image. When working on another platform, use a temporary Linux container or a
Linux development environment for this step. The lock files contain hashes for
published distributions, but dependency markers are resolved for the environment
that runs pip-tools.

Use the pip-tools version from the development lock. If bootstrapping a separate
lock-generation environment, the toolchain used for this update is
`pip==26.2.2` and `pip-tools==7.6.2`.

Generate the runtime lock first, then the development lock:

```sh
python -m piptools compile --upgrade --generate-hashes --allow-unsafe \
  --strip-extras --no-emit-index-url --no-emit-trusted-host \
  --pip-args='--only-binary=:all:' \
  --output-file backend/requirements.txt backend/requirements.in

python -m piptools compile --upgrade --generate-hashes --allow-unsafe \
  --strip-extras --no-emit-index-url --no-emit-trusted-host \
  --pip-args='--only-binary=:all:' \
  --output-file backend/requirements-dev.txt backend/requirements-dev.in
```

`--allow-unsafe` includes installer packages such as pip and setuptools in the
lock when required; it does not bypass hash verification. `--only-binary` keeps
installation on published wheels and fails if a supported wheel is missing.
Review the resulting version changes before installing them into a fresh test
environment.

## Validation

Install the development lock into a fresh virtual environment, then run:

```sh
python -m pip check
python -m pip_audit --strict --require-hashes -r backend/requirements.txt
python -m pip_audit --strict --require-hashes -r backend/requirements-dev.txt

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

## Container

```sh
docker build --platform linux/amd64 -f backend/dockerfile -t story-filler-backend:local backend
```

The Python 3.13 slim base is pinned to a multi-platform image digest. Review and
update that digest regularly to receive Python and operating-system fixes, then
rebuild, run the tests and scan the new image. A dependency-lock refresh alone
does not update the base image.

The image installs the runtime lock with required hashes and binary wheels only,
then verifies that the configured gevent worker can be imported. It does not
install compilers or development tools. Static files are collected
with a temporary build-only key and SQLite configuration, without production
credentials. The service runs as the non-root `app` user with Gunicorn's gevent
worker, as before.

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
