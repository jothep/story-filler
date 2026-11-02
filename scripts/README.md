# Maintenance and release checks

Install the backend development lock in an isolated Python environment, then run
the offline checks from the repository root:

```bash
python -m unittest discover -s scripts -p '*_test.py'
```

The release-order tests create temporary Git histories and replace `gcloud` with
a local test executable. They do not authenticate or contact Google Cloud.
Retired-entry tests also replace operational commands; all four legacy backup
and restore commands remain disabled.

The Pylint configuration tests load Django's model metadata with a temporary
signing key, in-memory SQLite and local storage. They accept valid model fields
and managers, then verify that undefined names and missing model attributes fail
even when the overall lint score exceeds the minimum. No production settings or
database records are needed.

## Dependency audit coverage

`check_dependency_audit.py` checks a pip-audit JSON report against one generated
hash lock. Every locked package must appear once at the locked version, with
vulnerability results and no skip reason. The parser accepts the repository's
exact pins and SHA-256 continuations; unsupported requirements fail explicitly.

```sh
python -m pip_audit --strict --require-hashes --disable-pip \
  -r backend/requirements.txt --format json --output /tmp/runtime-audit.json
python scripts/check_dependency_audit.py backend/requirements.txt /tmp/runtime-audit.json
```

Run both commands successfully. Coverage alone does not mean the report has no
vulnerabilities. CI preserves pip-audit's failure status while retaining its JSON
output, then checks coverage. Tests include the missing preinstalled packages
found during the [dependency review](../docs/dependency-findings.md).

## Local backup and recovery

`local_recovery.py` coordinates explicit local Docker operations;
`recovery_archive.py` validates the bundle and media paths without extracting
them. Both use only the Python standard library. Read
[the operator guide](../VOLUME_BACKUP_GUIDE.md) before using them.

The offline suite checks archive integrity, source selection, new-resource
ownership and failure cleanup. `recovery_integration.py` is deliberately separate
from unit-test discovery: it needs Docker and the pinned PostgreSQL image. It
creates synthetic source data and isolated recovery resources, checks successful
restoration and real database failure, then cleans up only its own resources.

The dedicated `verify-local-recovery.yml` workflow runs these checks on Linux
without cloud credentials. It never connects to the hosted database or replaces
existing application data. Its success is separate from the backend deployment
workflow's result.

## Backend delivery

The backend workflow has three jobs:

1. **Test:** install the development dependency lock, audit both Python dependency
   locks, require Black/Flake8 and Django-aware Pylint, and run application and
   maintenance tests. Pull requests receive no cloud secrets.
2. **Build, test and scan:** build one image with a unique run tag. Run the Django
   tests and import Gunicorn's gevent worker in that image as its default app user,
   with networking disabled, an in-memory SQLite database, and a temporary random
   signing key. Scan the same local image, then authenticate and push it. The job
   passes the pushed digest to deployment.
3. **Deploy:** hold the service's concurrency lock while checking release order,
   updating Cloud Run, verifying its serving revision, and checking the API.

Backend source, release workflow, release helper, and smoke-check changes can
produce a release on `main`. Terraform, other maintenance scripts and root Python
lint configuration changes run tests without deploying the application. A manual
run on `main` requests a release.
Terraform is never applied by this workflow.

When updating pinned GitHub Actions, check the repository's selected-actions
allowlist before publishing. Include the exact commit SHA of each action and any
actions called by its composite steps. Preserve the existing restrictions; do not
add wildcard patterns or enable all actions to resolve a blocked workflow.

## Release ordering

`cloud_run_release.py` only reads Cloud Run release metadata and Git history. It
does not update services, route traffic, or inspect runtime environment variables.
It requires one actual serving revision at 100% traffic and the existing policy
that routes 100% to the latest revision. Split, pinned, empty, or unknown traffic
configurations stop automatic delivery for review.

New revisions carry a `source_commit` label and an immutable image digest. The
helper also recognizes the existing pipeline's full 40-character commit image
tags in the configured repository, allowing the current release to transition to
this scheme. Cloud Run can resolve an old revision's image tag to a digest while
keeping the tag in the service template. In that case, the helper uses the template
only after its observed generation matches the current configuration, the service
is ready, and its latest created and ready revisions both match the revision
serving all traffic. An explicit template revision name must also match. A pending
or unrelated template cannot identify the running release. Unknown provenance is
rejected rather than assigned a guessed commit.

Within the deployment lock, the candidate and serving commits must exist in the
repository and belong to `origin/main` history. A later documentation commit does
not invalidate a backend release. An older candidate is skipped; divergent
histories are rejected. Repeating the same commit and digest is a no-op. The same
commit with a different digest requires review and a new release commit.

The lock prevents overlapping deployments from this workflow; it does not imply
FIFO ordering or coordinate manual cloud changes. The Git ancestry check is what
prevents a slow old build from replacing a newer deployment. After an update,
verification checks the actual traffic revision, commit label, and image digest
against the deployment result before running the public API smoke check.

### When a release is refused

Read the failure reason and compare the currently serving revision, image,
source commit, and Git history. Use the same limited metadata projections as the
helper; a full service export may contain private runtime settings. Keep intentional
traffic splits or pinned revisions in place until their owner reviews the routing
decision. Unknown image provenance needs to be established from release records,
not replaced with a guessed commit label.

For a changed dependency or base image, commit the reviewed change to `main` and
let that new commit produce a new candidate. Do not overwrite an existing commit's
release merely to bypass a digest mismatch. If the code is already on `main` but no
automatic application release was requested, the workflow can be started manually
on `main` after review. The same release checks still apply. An older superseded
run needs no retry because a newer source version already serves traffic.

There is no force flag or environment-variable bypass. Rollback and repair of
unknown provenance or routing are separate, explicitly reviewed operations.

Cloud Run copies labels to new revisions, and its revision status records the
resolved image digest. See the official [label configuration][labels],
[revision metadata][revisions], and [GitHub concurrency][concurrency] references.

## Scan policy

The workflow pins the Trivy action and scanner version. It blocks fixable HIGH
and CRITICAL image vulnerabilities (`ignore-unfixed: true`); a passing scan is
limited to that policy and the vulnerability database available on that run.
Separate strict, hash-checked dependency audits check both Python lock files.
Review version updates and their checks together rather than rebuilding an old
commit silently.

[labels]: https://docs.cloud.google.com/run/docs/configuring/services/labels
[revisions]: https://docs.cloud.google.com/run/docs/reference/rest/v1/namespaces.revisions
[concurrency]: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
