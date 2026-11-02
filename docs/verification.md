# Verification record

Legacy deployment reviewed on **27 September 2026**; repository migration begun on **28 September 2026**. This record distinguishes repository implementation from observations of a deployed service. A successful check applies to its stated scope and date, not to continuous uptime or all future versions.

New-repository checks are listed first. The later pre-migration sections retain evidence from the former private `jothep/maori-story-fill` repository and do not verify subsequent changes. See the [migration record](repository-migration.md) for migration scope and the [public aggregate snapshot](evidence/README.md) for historical activity counts.

## Published backend base-image replacement 3 November 2026

[PR #3](https://github.com/jothep/story-filler/pull/3) was merged as
`8ef92114802332e9239e7e250db333d8a37a3bcc`. Its files exactly match reviewed head
`56683c03f8f5ce1f36133ef13ff956ee4d9da617`. Local validation completed 469
automated tests, seven recovery scenarios and real final-image PostgreSQL/HTTP
checks before release.

| Check | Result | Evidence |
| --- | --- | --- |
| Final PR backend pipeline | Passed | [Run 41514246169](https://github.com/jothep/story-filler/actions/runs/41514246169): all three lock audits, style, 31 Django/136 script tests, image integration and full scan; authentication, push and deployment skipped |
| Final PR security checks | Passed | Actual JavaScript/Python [CodeQL analysis 41514246245](https://github.com/jothep/story-filler/actions/runs/41514246245) and [history scan 41514246214](https://github.com/jothep/story-filler/actions/runs/41514246214) |
| Independent review | Passed | Image/lock, workflow and runtime-script reviews; timing, cleanup and rerun findings corrected and regression-tested |
| Third-party Sourcery review | Skipped on final head | Its weekly character allowance was exhausted. This is not a passing review; the earlier findings were addressed and independently checked |
| Main release | Passed | [Run 41519045124](https://github.com/jothep/story-filler/actions/runs/41519045124): test, rebuild, integration, full report, scan gate, push, actual deployment, revision verification and API reads |
| Main security checks | Passed | Actual JavaScript/Python [CodeQL analysis 41519244722](https://github.com/jothep/story-filler/actions/runs/41519244722), manually dispatched because the push path filter excludes this batch, and [history scan 41519045086](https://github.com/jothep/story-filler/actions/runs/41519045086) |
| Published image report | Checked | Linux amd64; 32 Alpine packages and all 37 Python packages; zero scanner findings, with the separately tracked SQLite advisory still affected |
| Independent online check | Passed | Source/revision/digest match; story list, story 1 with eight paragraphs and 11 words, and configuration JSON; static CSS and public picture/audio resources accessible |

Cloud Run revision `maori-story-backend-00032-6tt` serves **100%** of traffic.
Its source label is `8ef92114802332e9239e7e250db333d8a37a3bcc`, and its image is
`us-central1-docker.pkg.dev/jaskojothep/maori-story/backend@sha256:616c69a700cb09abfb66771d4ddfc43ecef22d6b13e72d139122f415a66f1ba1`.
The final release report still identifies `sqlite-libs` 3.53.4-r0. The known
[CVE-2026-119373](dependency-findings.md#current-backend-alpine-runtime-3-november)
remains tracked; no claim of a completely vulnerability-free runtime is made.

The public audio object uses `application/octet-stream`; HTTP 200/206 and its
M4A container header were verified. An initial probe assumed an audio-specific
MIME type and an MP3 header, which did not match this existing M4A object. No
storage metadata or content was changed. These checks cover read accessibility,
not media upload or browser playback.

No production data, migrations, IAM or frontend release changed. Local verification
left the original container set and ten anonymous volumes unchanged, and the
dedicated review VM was stopped.

## Backend base-image review 3 November 2026

Starting from `a16507e`, this batch replaces the Debian slim runtime with pinned
Python 3.13.18 on Alpine 3.24. It preserves all 37 application dependency versions,
the non-root runtime identity and the existing Gunicorn command. Two native
extensions are built in a separate stage with locked source hashes and build
tools. No frontend code, production data, migrations or cloud IAM changes are
included.

| Check | Result | Scope |
| --- | --- | --- |
| Runtime lock | Passed | All 37 versions and all 714 previous artifact hashes retained; 37 published source hashes added through pip-tools and independently checked against PyPI |
| Dependency audits | Passed | Exact coverage of 37 runtime, 80 development and three image-build packages; zero known Python package findings |
| Wheel compatibility | Passed | All 37 packages still download with required hashes and wheel-only installation on Linux glibc amd64 and macOS arm64 |
| Final Linux amd64 image | Passed | Runtime UID 100/GID 101; exact installed-package/lock match; no pip, ensurepip, compiler or development tools |
| Native functionality | Passed | SQLite, compression libraries, TLS trust store, Pillow PNG/JPEG/WebP, libpq, gevent, native CRC32C and zope C extensions; GCS import/configuration and public URL generation without cloud access |
| Django | 31 passed | Also system checks and no missing migrations; repeated inside the final image |
| Maintenance/configuration | 136 passed | Includes 17 ownership, timeout, late-creation, signal, diagnostic and runtime dependency contracts |
| Default runtime integration | Passed | Synthetic PostgreSQL; separate migrate/seed; unmodified Gunicorn CMD with three workers; story list/detail/configuration, POST rejection, exact static CSS and missing-asset 404; SIGTERM exit 0 |
| Frontend regression | 302 passed | 229 lint/type regressions, 71 component tests and two Pages HTTP checks; production build, lint/types/format, production/full audits passed |
| Recovery integration | Seven scenarios passed | Real synthetic PostgreSQL/media recovery and failure cleanup; original ten anonymous volumes retained |
| Full image scan | Zero scanner findings; one known issue retained | Trivy identifies all 32 OS and 37 Python packages. SQLite CVE-2026-119373 remains affected despite absence from the Alpine advisory feed |
| Release gate | Passed | Existing fixable HIGH/CRITICAL vulnerability gate and image secret scan retained |
| Review and style | Passed | Independent image/lock, runtime-script and workflow reviews; Black, Flake8, Pylint, Prettier, actionlint and diff checks |

The unique automated test total is **469**, plus the seven recovery scenarios and
final image integration checks. The final local image has manifest-list digest
`sha256:13dcb0b97d6487fc5e821a1c0597b7ec08a0fbe1eeafdb640ee41ba68236b10b`.
CI rebuilds and repeats the image checks before publishing its own digest.

The same Trivy 0.76.1 database was used for the Debian baseline and candidates:
updated `2026-11-02T07:17:05Z`, local SHA-256
`9cf3518dfc47bd04da93073cbc893e428f8608fe57b2b04ad4893e82cf25c58d`.
Baseline records were HIGH 41, MEDIUM 70, LOW 57 and UNKNOWN 8, covering 85
advisories including nine HIGH. Eight of those HIGH advisories are addressed by
updated or removed components. SQLite 3.53.4 with FTS5 remains affected and is
tracked in the [advisory review](dependency-findings.md). A Distroless alternative
passed functionality checks but introduced five additional interpreter HIGH
advisories, so it was not selected.

The first hosted review found timing and cleanup edges in the new test harness:
worker readiness, late Docker creates, repeated termination signals during
cleanup and report-name conflicts on reruns. These are covered by follow-up
regressions. Error output is bounded and strips the synthetic test secrets.
Two low-confidence subprocess audit notices were reviewed independently: commands
use argument arrays, validated Docker inputs or fixed Django arguments, and
`shell=False`. Only those two reviewed call sites carry the exact audit-rule
annotation; the scanner and release gates remain enabled.

Pull requests now build and verify the image without cloud credentials. Each run
saves a complete package/vulnerability JSON report for 30 days, then applies the
existing gate. Only a main-branch application release can authenticate, push the
scanned image and deploy its immutable digest.

## Published frontend tooling migration 3 November 2026

[PR #2](https://github.com/jothep/story-filler/pull/2) was merged as
`b7ae4cde2b9f7f7cd047fe1fdecf46ab8572357d` after the reviewed source `6db8b28`
passed local validation, independent review and all hosted PR checks. Sourcery
also approved the PR. The merged frontend and workflow files match the tested
source exactly.

| Check | Result | Evidence |
| --- | --- | --- |
| PR frontend checks | Passed | [Run 41433799938](https://github.com/jothep/story-filler/actions/runs/41433799938): all-severity audits, lint/types/format, 229 lint regressions, 71 component tests, production build and two Pages checks |
| Manual frontend image workflow | Passed without registry push | [Run 41433796697](https://github.com/jothep/story-filler/actions/runs/41433796697): the same frontend checks, image build and configured Trivy gate |
| PR CodeQL analysis | Passed | Both actual analysis steps in [run 41433799805](https://github.com/jothep/story-filler/actions/runs/41433799805) |
| PR credential history scan | Passed | [Run 41433800005](https://github.com/jothep/story-filler/actions/runs/41433800005); local changed-source and full-history scans also reported no findings |
| GitHub Pages release | Passed | [Run 41434780731](https://github.com/jothep/story-filler/actions/runs/41434780731): checks repeated before deployment from `b7ae4cd` |
| Main-branch security checks | Passed | [CodeQL 41434780750](https://github.com/jothep/story-filler/actions/runs/41434780750), including both analysis steps, and [history scan 41434780780](https://github.com/jothep/story-filler/actions/runs/41434780780) |
| Public API reads | Passed | Story list, story 1 with eight paragraphs and 11 words, and configuration JSON |
| Public frontend resources | Passed | Entry HTML, JavaScript, CSS and favicon returned HTTP 200; the served JavaScript contains this release's new root-element check |
| Public browser | Passed | Menu navigation, story title/text/image and 11 vocabulary words rendered; direct refresh of the nested story route also loaded |

No backend workflow was triggered by this batch. Backend operating-system
findings remain for the next review; no database or cloud permissions changed.
Local preview services and the dedicated review VM were stopped. Test containers
were removed; the ten pre-existing anonymous volumes were retained unchanged.

## Frontend tooling migration 3 November 2026

Reviewed on 2–3 November, starting from `191c4d2` on
`codex/frontend-linter-migration`. This batch removes
the affected ESLint development tree. Oxlint checks JavaScript, React and Hooks;
TypeScript checks the existing JavaScript through JSDoc. The application stays
on React/JSX, and Prettier remains required. The previous 82 rule purposes were
reviewed individually, including their configured options and file scopes.

The migration adds shared API/context contracts and component annotations.
Small runtime adjustments preserve cancellation across browser realms, provide
safe messages for non-Error request failures, and report a missing application
mount element explicitly. No backend, database, infrastructure or credential
configuration changes are included.

| Check | Result | Scope |
| --- | --- | --- |
| npm dependency audits | Passed | Full development tree and production-only tree: zero known findings; the six moderate ESLint/minimatch records are gone |
| Package authenticity | Passed | Clean local install: 178 registry signatures and 56 attestations verified |
| Native linter review | Passed | Linux x64 package integrity/provenance matched the Oxlint release; Trivy found zero known findings in 441 identified Rust dependency entries at that source revision |
| JavaScript, React and types | Passed | Oxlint with explicit rules/options, unused-suppression detection, strict checkJs, React wrapper names, and syntax checks for scripts/tests |
| Lint/type regression examples | 229 passed | 82 rule pairs, 26 scope cases, 18 rule-option cases, 13 React wrapper-name cases and eight production-command checks |
| Frontend behavior | 71 passed | Original 62 tests plus nine unexpected-rejection, cancellation and mount-element cases; controlled HTTP and media behavior |
| Production build and Pages | Passed | Production assets built; two tests checked entry/fallback paths, deep links, JS/CSS and missing assets |
| Linux amd64 | Passed | Clean Node 24.22.2 install, GNU native linter loading, lint/type checks, 71 component tests, build and Pages checks |
| Frontend runtime containers | Passed | Both Dockerfiles; real Nginx checks for HTML, JS/CSS/favicon, SPA routes and missing-asset 404s; Node/npm/source absent from runtime |
| Frontend image scans | Zero known findings | Both Alpine 3.24.3 runtime images, all severities including unfixed findings; 71 OS package records scanned per image |
| Local browser | Passed | Production build with synthetic read-only API responses; menu navigation, story text/word bank and nested-route refresh |
| Style and workflow review | Passed | Prettier, Black, Flake8, Django-aware Pylint, actionlint and whitespace checks |
| Existing backend/maintenance suite | 150 passed | 31 Django and 119 maintenance/configuration tests; system and migration checks passed with SQLite and no cloud access |
| Recovery integration | Seven scenarios passed | Real local PostgreSQL/media recovery checks using synthetic data; before/after container and volume sets match |

The automated total is **452 passing tests**, plus the seven recovery integration
scenarios and container/browser checks above. Independent reviewers verified the
application behavior, lint coverage, command failure paths and dependency claims.

The complete toolchain audit gate now fails at every severity in both frontend
workflows. Oxlint does not have an identical algorithm for every ESLint rule:
JSDoc/checkJs replaces the static prop-declaration check, current React types
reject removed APIs, and a small compiler-API helper covers anonymous React
wrappers. Unsafe lifecycle aliases are also rejected. The
[frontend guide](../frontend/README.md#javascript-react-and-type-checks) records
these differences. Type declarations do not validate incoming API JSON at runtime.

The Rust scan supplements provenance and npm audits; it is not a claim that all
compiled dependencies can be recovered from a stripped binary. Backend OS
advisories remain as recorded in [dependency findings](dependency-findings.md).

## Published dependency follow-up 2 November 2026

[PR #1](https://github.com/jothep/story-filler/pull/1) passed frontend, backend, credential-history and CodeQL checks before the reviewed source `8d81af2268581e5172b54f704a6481d38e6a31b2` was merged into `main`. The 230 local automated tests, seven recovery scenarios and candidate runtime/database checks are detailed below.

| Check | Result | Evidence |
| --- | --- | --- |
| Backend release | Passed | [Run 41424061852](https://github.com/jothep/story-filler/actions/runs/41424061852): complete-lock audits and coverage checks, style, tests, built-image tests, existing image security gate, registry push, deployment and API verification |
| Frontend release | Passed | [Run 41424061844](https://github.com/jothep/story-filler/actions/runs/41424061844): audits at the existing thresholds, lint/format, component/lint/Pages tests, build and GitHub Pages deployment |
| Credential history scan | Passed | [Run 41424061853](https://github.com/jothep/story-filler/actions/runs/41424061853) on the release source |
| CodeQL | Passed before merge | [Run 41423718710](https://github.com/jothep/story-filler/actions/runs/41423718710), including both analysis steps; advisory analysis |
| Serving backend | Verified independently | Ready revision `maori-story-backend-00031-sjd`, source `8d81af2`, 100% of traffic; deployed image digest `sha256:414557c6be75721c86ad809ca2ba0279d26d8133bca4bdd3d39b08bea9c81f38` |
| Public reads | Passed independently | Story list, story 1 with eight paragraphs and 11 words, and configuration JSON; GitHub Pages HTML and both entry assets returned successfully |

The release changed the runtime image and audit safeguards, without a database migration, data restoration or IAM change. The dedicated local Docker environment is stopped. Remaining advisories and upgrade limits are recorded in [dependency findings](dependency-findings.md); passing the configured gates does not mean those advisories have disappeared.

## Dependency follow-up review 2 November 2026

This follow-up starts from `ac6f44e`. The backend keeps its Python base digest and both application dependency locks, applies the reviewed stable `tzdata` update, and removes seven unused account-management/mount packages and their dependencies after creating the service account. APT dependency checks, package metadata, essential packages, certificate authorities and required native libraries are retained.

The review also found a gap in the previous Python audit command: its temporary pip resolver omitted already-installed `packaging`, and additionally `pip`, `setuptools` and `wheel` in the development lock. Both audits now read the complete locks with `--disable-pip`. A separate checker compares every reported package and version with the lock. CI preserves the scanner's failure status when saving its JSON. This corrects the earlier full-coverage assumption; no known vulnerability was found in the previously omitted packages.

| Check | Result | Scope |
| --- | --- | --- |
| Automated tests | 230 passed | 31 Django tests, 119 maintenance/configuration tests, 62 frontend component tests, 16 lint examples and two Pages tests |
| Audit coverage | Passed | Exact agreement with all 37 runtime and 80 development pins; zero known Python findings. The old incomplete JSON reports are rejected |
| Coverage regressions | 20 passed | Missing/bootstrap packages, skips, duplicates, unexpected packages, wrong versions, malformed reports and unsupported lock syntax; included in the 119 script tests |
| Scanner failure propagation | Passed | The same explicit Bash/pipefail setup used by CI retains a failed scanner's exit code after `tee` and stops the next command |
| Candidate runtime | Passed | 31 Django tests, system and migration checks as non-root `app`; installer/development tools absent; SSL certificate store, SQLite, libpq, gevent and PNG/JPEG/WebP handling available |
| Native compatibility | Passed | 62 supported native standard-library imports and 113 shared objects checked; no new missing libraries. Optional Tk GUI libraries were absent in both the original slim image and candidate |
| Actual HTTP/database integration | Passed | Candidate image's default Gunicorn/gevent command served story list/detail/configuration using a new synthetic PostgreSQL database, and retained the read-only API |
| Backup/recovery integration | Seven scenarios passed | Existing PostgreSQL/media recovery success and refusal/failure cases; no additional resources left behind |
| Full image scan | Compared against the same database | OS records: HIGH 45→41, MEDIUM 71→70, LOW 61→57, UNKNOWN 8→8, CRITICAL 0. Distinct advisories remain 85, including nine HIGH; no vendor-fixed records were present |
| Frontend compatibility | Existing checks passed; upgrade deferred | Fresh npm production audit has zero findings; full audit retains six moderate packages from one advisory. Isolated trials confirmed ESLint 10/React incompatibility and the minimatch major API change |
| Style and workflow checks | Passed | Black, Flake8, backend Pylint, frontend ESLint/Prettier, production build, actionlint and diff checks |

The image scans used Trivy's database updated at `2026-11-02T01:14:05Z`, with local database SHA-256 `72ddbfd4f4fb1b6458b1cceb050e3c31733fd832615deab4be241ded106fece3`. The reduction is in package-level records, not distinct vulnerabilities. Removing unused packages does not fix the same source-package advisory in other installed components. The [dependency findings](dependency-findings.md) explain each HIGH group, the stable-package limits and the frontend upgrade blockers.

These checks used tracked source copies and synthetic data. No production backup, database migration, data cutover or IAM change was performed. The test container/volume set was unchanged after cleanup; the ten pre-existing anonymous volumes were retained.

## Published recovery tooling 2 November 2026

The fifth batch was merged into `main` at `4f4efdd2c9cd43d3d1f2c006bbef9d8e019a470e` after independent review and a fresh run of all 210 automated tests and seven real Docker recovery scenarios. The final repository check covered tracked files, the full reachable credential scan, documentation links and examples, workflow syntax and deployment scope.

| Check | Result | Evidence |
| --- | --- | --- |
| Recovery CI | Passed | [Run 41410711730](https://github.com/jothep/story-filler/actions/runs/41410711730): 51 recovery tests, seven legacy-entry tests and the seven real PostgreSQL/media scenarios on Linux |
| Backend CI | Passed | [Run 41410711732](https://github.com/jothep/story-filler/actions/runs/41410711732): runtime/development dependency audits, formatting, Flake8, Django-aware Pylint, 31 Django tests and 99 script tests |
| Application deployment scope | Verified | Image build/push and Cloud Run deployment jobs were skipped; no frontend workflow was triggered by the tools-only change |
| Credential history scan | Passed | [Run 41410711694](https://github.com/jothep/story-filler/actions/runs/41410711694); separate local full-history scan also passed |
| CodeQL analysis | Completed successfully | [Run 41410854093](https://github.com/jothep/story-filler/actions/runs/41410854093), explicitly dispatched because the existing push filter covers application directories; advisory analysis |
| Serving backend | Ready | Revision `maori-story-backend-00030-ldj`, source `8a394f8`, remained on 100% of traffic |
| Public API reads | Passed | Story list, story 1 with eight paragraphs and 11 words, and configuration JSON; no data mutation |

All five planned review batches are published. The operator commands remain local tools: this release did not run a production backup, restore, data cutover, database migration or IAM change. The dedicated local test VM is stopped. Its ten previously recorded, unattributed anonymous volumes were retained; the final integration run changed neither the container set nor the volume set.

The remaining dependency findings are recorded under [scan policy](#remaining-findings-and-scan-policy). Hosted Neon/GCS recovery and full application cutover are separate future exercises, not completion requirements for the local recovery tooling. Earlier dated sections retain the scope and status observed at the time of each batch.

## Local backup and recovery review 2 November 2026

The fifth batch was prepared from published commit `a830ec9` on `codex/batch-5-recovery` and independently reviewed at `4f4efdd`. It replaces the unsafe local backup procedures with PostgreSQL 16 logical exports and recovery into new Docker resources. It does not operate Neon/GCS, replace a running application's data or change cloud permissions.

`local_recovery.py` provides backup, verification and restore commands with explicit local Docker targets. Backup checks Compose ownership, the stopped backend's actual media mount, database/tool versions and active media writers. The operator also confirms that external writers have been stopped. It uses `pg_dump` rather than copying live PostgreSQL data files, and writes a private output directory with a completion manifest last. Existing output and old backups are never overwritten or pruned.

`recovery_archive.py` validates the versioned manifest, hashes, sizes and media archive without extracting it. It rejects escaping or conflicting paths, links, special files, sparse members, duplicate manifest keys, truncated records and excessive sizes. Restore first makes a private snapshot and validates that snapshot and the dump directory. Only then does it allocate new, randomly named and labelled resources. The database has no network or published port. Media are normalized and read back for hash comparison. Successful recovery retains the isolated database and two named volumes for inspection; the application is not switched to them.

All four historical shell entry points now refuse execution. The operator guide was rewritten to remove unsafe historical deletion commands and unverified success claims. The new workflow uses the pinned official PostgreSQL 16 image and no cloud credentials.

| Check | Result | Scope |
| --- | --- | --- |
| Automated suite | 210 passed | 31 backend tests, 99 script/configuration tests, 62 frontend component tests, 16 lint examples and two Pages tests; all repeated during the fifth-batch release review |
| Recovery unit tests | 51 passed | 27 operational safeguards and 24 archive-validation tests; included in the 99 script tests above |
| Retired commands | Passed | Seven tests exercise 32 calls across all four old entry points; no operational command is reached |
| Linux standard-library tests | 58 passed | Recovery tests plus retired-entry tests in a fixed Python 3.13 image, with no network or host-directory mounts |
| Real PostgreSQL recovery | Passed | Logical export/import of synthetic multi-table data; Unicode and spaced media names; exact row and media hashes; foreign keys, unique/not-null/check constraints and subsequent sequence values |
| Refused inputs | Passed | A running media writer blocks backup; a damaged checksum is rejected before any recovery resource is created |
| Real database failure | Passed | A valid dump using a source-only tablespace passes archive checks but fails at `pg_restore`; only that attempt's new resources are removed |
| Helper failure cleanup | Passed | Real output-limit and two-second timeout failures stop and remove the helper and its anonymous volume; previously existing resources remain unchanged |
| Complete resource comparison | Passed | All container IDs and volume names match before and after the final seven-scenario integration run; no new resources remain |
| Credential scans | No findings | Gitleaks checked all 18 changed/new text files and the full reachable Git history with redaction enabled |
| Style and workflow checks | Passed | Black and Flake8 across backend and Python scripts, Django-aware Pylint, syntax checks for tracked shell scripts, and actionlint for all six workflows |
| Independent review | Passed | Archive validation, operational ownership, cleanup and CI wiring were cross-reviewed; identified cleanup defects were fixed and retested |

The first review found that killing an attached Docker client does not guarantee its helper container stops. Every helper now has an operation label and explicit cleanup. Testing then exposed anonymous volumes automatically created by the PostgreSQL image. Owned containers are removed with their anonymous volumes; named volumes still require separate ownership checks. A deeply nested JSON/PAX error path was also made to fail safely.

The final integration run was repeated after those fixes. Ten anonymous volumes from earlier test attempts were already present in the dedicated test VM. Its event history no longer established their exact ownership, so they were recorded and left untouched rather than pruned. The final run added none. The dedicated review VM was stopped afterwards; the default Docker environment was not changed.

A checksum establishes integrity, not trust. Only dumps from a trusted local database are supported, and database/media consistency depends on the documented stopped-writer window. Tests use synthetic records and local volumes; they do not demonstrate a hosted restore, point-in-time recovery, application cutover or recovery-time objective. The supported scope and exact commands are in the [operator guide](../VOLUME_BACKUP_GUIDE.md).

The independent release review repeated all 210 tests and the seven real Docker scenarios. Documentation links, CLI examples and workflow scope were also checked. The existing ESLint compatibility issue remains tracked separately; the fifth batch does not change application dependencies or resolve those upstream advisories.

## Hosted maintenance release 2 November 2026

The fourth batch was independently reviewed and all 159 automated tests passed again before `8a394f8b0277a13d52991be70cc6ae5c5961ad46` was merged into `main`. [Frontend run 41404713288](https://github.com/jothep/story-filler/actions/runs/41404713288) and [backend run 41404713244](https://github.com/jothep/story-filler/actions/runs/41404713244) both completed successfully. The new formatting and Django-aware Pylint gates passed in CI, along with both Python dependency audits, runtime-image tests and the existing image scan policy. [CodeQL](https://github.com/jothep/story-filler/actions/runs/41404713355) and [credential history scanning](https://github.com/jothep/story-filler/actions/runs/41404713510) also completed successfully.

Independent read-only checks confirmed that revision `maori-story-backend-00030-ldj` serves 100% of traffic, with source label `8a394f8` and image digest `sha256:f273c68de6fb25f830cf8095c24c445036d7762e24381bc67e4b54ba24d55503`. The story list, story detail and configuration APIs passed. A direct browser visit to `/story-filler/story/1` displayed the title, image, paragraph text and 11 vocabulary words. No database migration, restore or IAM change was performed. The earlier moderate development-tool and unfixed operating-system findings remain subject to their documented policies.

The fifth batch, local backup and isolated recovery tooling, is being prepared separately and is not part of this release.

## Local maintenance review 2 November 2026

The fourth batch starts from published commit `4488d20` on `codex/batch-4-maintenance`. Its subsequent hosted release is recorded above. It makes the maintained application easier to read and turns its formatting and backend lint checks into required CI steps. The historical `demo/` application and generated Django migrations are outside this formatting change.

The frontend now has consistent Prettier formatting, fewer redundant comments and no unused component backup files or starter React icon. Its error boundary uses Vite's development flag for diagnostic visibility, with two component tests. ESLint separates browser code, Node tooling and tests. The 19 existing React rules stay enabled for application code, and Rules of Hooks/effect-dependency checks are added. Sixteen positive and negative examples verify the actual lint configuration.

The backend and Python maintenance scripts use Black's 88-character format. Flake8 now reads a native `.flake8` file; the old `pyproject.toml` Flake8 table was not consumed by that tool. Pylint uses `pylint-django` to understand model fields and managers. It retains the 7.0 score threshold and now fails on any error or fatal diagnostic, even above that score. Three tests confirm that valid model access passes while real missing attributes and undefined names fail. Non-error recommendations remain visible.

| Check | Result | Scope |
| --- | --- | --- |
| Automated tests | 159 passed | 62 frontend component/unit tests, 16 frontend lint examples, two Pages HTTP/build tests, 31 Django tests and 48 maintenance/configuration tests |
| Frontend style and build | Passed | Full frontend ESLint and Prettier checks; Node 24 production build; no local fixture API URL in the build |
| Python style and analysis | Passed | Black and Flake8 for `backend/` and `scripts/`; Django-aware Pylint scored 9.52/10 with no error/fatal findings and 42 non-error recommendations |
| Django system and migration checks | Passed | No system-check problems or model changes requiring a migration; temporary SQLite and local storage |
| Fresh development installs | Passed | Hash-only binary installs and `pip check` on macOS arm64 and Linux amd64 with Python 3.13 |
| Python dependency audits | Passed | Strict hash-checked audits of both locks reported zero known vulnerabilities; Linux development-lock audit also passed |
| Lock-file review | Passed | Existing 78 development pins retained; only `pylint-django` 2.8.0 and `pylint-plugin-utils` 0.9.0 added. Both runtime dependency files and the frontend lock are byte-for-byte unchanged |
| Structure and output comparisons | Passed | Six existing Python maintenance scripts have identical parsed syntax trees. All 30 backend files are equivalent after accounting for one unused import and one constant f-string; nine migration files are byte-for-byte unchanged. Of 45 frontend source/config files, only the documented error-boundary and direct-return simplifications change parsed structure. Generated CSS retains the third batch's filename/hash |
| Workflow validation | Passed | actionlint checks all five workflows; root Python lint configuration changes trigger backend checks; lint failures no longer continue silently |
| Changed-file credential scan | No findings | Gitleaks checked all 60 changed/new text files with redaction enabled |
| Independent review | Passed | Another reviewer checked CI paths and conditions, lint environments, all 80 existing frontend rules and positive/negative checks; no blocking findings |

The frontend dependency review still reports six moderate development-tool findings and zero production findings. A supported ESLint upgrade is blocked by the current React plugin's peer compatibility. The upstream minimatch fix also requires a major version outside the existing dependency ranges. No peer checks or React rules were bypassed, and no forced transitive override was added. See the [frontend maintenance guide](../frontend/README.md#remaining-development-dependency-findings).

Runtime dependency and container definitions are unchanged, so this batch does not claim a new image security scan or repeat the earlier browser gameplay exercise. The existing backend operating-system findings remain tracked below. All test data is temporary; production databases, cloud permissions and runtime credentials were not changed. The dedicated Linux review containers and VM were stopped after verification.

The source and CI changes were reviewed together before publication. The next functional work is a separately tested replacement for the disabled local backup/restore workflow, beginning with disposable data and failure cases. The existing restore commands remain disabled until that work passes its own review. A supported ESLint/React-plugin migration remains tracked independently of that recovery work.

## Hosted frontend lifecycle release 2 November 2026

The third batch was independently reviewed and all 138 automated tests passed again before `68a7ce76cf1afd28dd2284ffb10a75da9d899f24` was merged into `main`. Its frontend was then published through [run 41398092161](https://github.com/jothep/story-filler/actions/runs/41398092161), including the new Pages fallback check. [CodeQL run 41398092180](https://github.com/jothep/story-filler/actions/runs/41398092180) and [credential history scan 41398092152](https://github.com/jothep/story-filler/actions/runs/41398092152) completed successfully.

The public story URL `/story-filler/story/1` loaded directly and after a browser refresh. Story text, picture and word bank appeared. Background music initially showed stopped when autoplay was blocked; a manual click changed it to playing, and it was turned off before continuing. This checks the visible playback control, not recording quality across devices. Pages retains HTTP 404 for the custom fallback document, while the application and its assets load at the original URL.

The backend was not redeployed by this frontend-only change. An independent read-only API smoke check passed again for the story list, story detail and configuration endpoints. The previously verified backend revision and dependency-scan limitations remain as recorded below. The fourth maintenance batch is recorded separately above and is not part of this release.

## Local frontend lifecycle review 2 November 2026

This third batch starts from the published review code and its release record at `80046e5`. It was prepared on `codex/batch-3-frontend`; the subsequent hosted release is recorded above. It changes frontend behavior and adds regression coverage; it does not change database models, production data, credentials or cloud permissions.

- **Incomplete story content:** a blank without its linked word is shown as unavailable and cannot receive drops. Text and paragraph navigation remain usable. Completion checks the actual answers across every paragraph rather than counting arbitrary entries in the answer map.
- **Request ownership:** switching routes, retrying or unmounting cancels the old request. A separate identity check ignores late results from transports that still finish. Route changes hide old content and errors on the first render, before effects start the next request.
- **Audio ownership:** narration, selected-word recordings and background music stop when their owner changes or unmounts. Late callbacks cannot restart old narration or change the new playback state. Rejected playback leaves controls in the stopped state and allows a manual retry. Menu configuration requests and hint timers are cleaned up.
- **Drag cancellation:** cancellation and unmount clear the overlay and page-level dragging state without recording an answer. Normal completed drops still use the existing answer validation.
- **Pages deep links:** each build generates `404.html` from the entry page so React Router can open the original story path. The custom error document retains HTTP 404; JavaScript and CSS use the project base path and load normally. This behavior is checked before CI uploads the Pages artifact.

The targeted regression tests were run against the old implementation before each fix. They reproduced missing-word crashes, incorrect completion, stale requests and errors, abandoned drag state, and late or rejected audio operations. Additional tests check normal paths and route changes before effects run.

| Check | Result | Scope |
| --- | --- | --- |
| Frontend unit/component tests | 60 passed | Six existing tests plus 54 new tests across content, answer completion, drag lifecycle, API behavior, request races and audio ownership |
| Backend tests | 31 passed | Temporary SQLite and local storage in an isolated checkout; no production writes |
| Maintenance/release script tests | 45 passed | Includes the published legacy revision compatibility regressions |
| Frontend lint and changed-file formatting | Passed | Full frontend ESLint; Prettier for changed source, tests and audio fixtures |
| Production build and Pages fallback | Passed | Node 24; two additional Node tests check generated HTML, absolute asset paths, deep-link 404 responses with and without a query, successful asset responses and missing-asset 404s |
| Linux frontend containers | Passed | Both existing Dockerfiles built for Linux amd64; isolated runtime HTTP checks passed for HTML, story routes, generated fallback, three entry resources and missing-asset 404s. The build contained no local fixture API URL. Host port forwarding was not part of this check |
| Browser with synthetic local data | Passed | Missing word and readable next paragraph; unavailable recordings disabled; server error followed by successful retry; real pointer drag, correct answer and completion-page navigation; direct story URL and refresh through a Pages-style 404 server |
| Changed-file credential scan | No findings | Gitleaks scanned all 24 changed/new text files with redaction enabled; pattern detection is not proof of absence |
| Independent review | Passed | Request ownership, incomplete-content handling and drag changes reviewed by another agent; audio ownership reviewed separately |

The two image builds reused unchanged dependency and operating-system layers, so the prior Trivy findings were not rescanned. Temporary containers, the dedicated review VM and local test servers were stopped after verification. The browser scenario uses a local read-only fixture, not the production database. Audio regressions use controlled media events and promises; they do not assess recording quality or every browser's autoplay and codec behavior. No audio library or UI framework was added. Full repository formatting, migration of the remaining ESLint development dependencies, and replacement backup/restore tooling remain later batches.

## Hosted release 2 November 2026

The first two review batches were merged into `main` at `43ba793fc8c5c505dfcd905d2315a4fd3d6cf7c7`. The frontend was published from that commit. The backend was published from `8af5dd842e00bedaf107ec7bf5688e15f02059d0`, which adds the legacy Cloud Run metadata compatibility fix described below. The subsequent frontend lifecycle release is recorded above.

| Check | Result | Evidence |
| --- | --- | --- |
| Frontend delivery | Passed | [Run 41393538930](https://github.com/jothep/story-filler/actions/runs/41393538930): dependency audits, lint, six tests, production build and GitHub Pages deployment |
| Backend delivery | Passed | [Run 41394419852](https://github.com/jothep/story-filler/actions/runs/41394419852): both dependency audits, 31 Django tests, 45 script tests, runtime-image tests, image security gate, registry push, Cloud Run deployment and public API checks |
| Serving version | Verified independently | Ready revision `maori-story-backend-00029-sv6`, source label `8af5dd8`, 100% of service traffic; running digest matched this workflow's image in Artifact Registry |
| Public API | Passed independently | Story list, story 1 with eight paragraphs and 11 words, and configuration JSON; read-only requests |
| Browser | Passed for normal navigation | Public menu and story details loaded through the menu link. Direct refresh of a nested story URL still returned the Pages 404; correction is part of the next local frontend batch |
| Credential history scan | Passed | [Run 41394419952](https://github.com/jothep/story-filler/actions/runs/41394419952) on the backend release commit |
| CodeQL | Completed successfully | [Run 41392325733](https://github.com/jothep/story-filler/actions/runs/41392325733) on the merged review commit; advisory analysis, not a claim that no alerts exist |

The initial workflows could not start because the repository's selected-actions allowlist did not include the updated pinned actions. The allowlist was updated with 12 exact commit references, including the needed composite-action dependencies. Existing entries and restrictions were preserved. The [maintenance guide](../scripts/README.md) now includes this check when updating action pins.

The first backend deployment attempt stopped before modifying the service. Cloud Run had resolved the old revision's full-commit image tag to a digest, while its original tag remained in the service template. The compatibility fix only accepts that template when the configuration generation is fully observed, the service is ready, and the latest created and ready revisions both match the revision serving all traffic. Nine additional regression tests cover this transition and rejection of pending, unrelated or incomplete metadata. No release protection was disabled.

At 05:34 UTC the independently checked backend digest was `sha256:02bfce299ad3613d051f4b1fe79867b572f47c48555c8ced32f37878effb0967`. The release did not run database migrations, restore data, change runtime credentials or expand cloud IAM permissions. The earlier scan limitations below still apply.

## Local dependency and delivery review 2 November 2026

The second review batch builds on local safety commit `321c80e`. It updates dependency locks, container packaging and delivery checks. The source changes were first prepared and tested in an isolated copy, without production credentials, production database operations, IAM changes or cloud deployment calls. The hosted release is recorded above.

Python dependencies now have direct `.in` inputs and generated runtime/development `.txt` locks with hashes. The locks were resolved on Linux amd64 with CPython 3.13. The runtime uses Django 5.2.18, Django REST framework 3.18.3 and Pillow 13.0.0. Development tools are separate. The frontend keeps its existing application code and uses Node 24 with `npm ci`. Container base images and the Actions used in the three updated delivery workflows are pinned by digest or commit. Terraform keeps Google provider 5.45.2 and now commits its lock and Linux/macOS checksums.

The backend workflow separates read-only tests, image build/test/scan/push, and deployment. It sends the scanned image digest to the deployment job. Under that job's concurrency lock, a helper compares the candidate with the actual serving source commit. It skips stale candidates, allows a release followed only by documentation commits, and rejects unknown origins, conflicting digests, divergent histories or unsupported traffic policies. After deployment, it checks the serving revision, source label and digest before the public API check. Terraform's lifecycle rule preserves the image and these two CI-owned `source_commit` label keys. The release-check tests use real temporary Git histories and a fake Cloud CLI; they are not a live Cloud Run rollout test.

| Check | Result | Scope |
| --- | --- | --- |
| Backend dependencies and tests | Passed | 31 tests in fresh Python 3.13 environments and the Linux amd64 runtime image; system/migration checks passed; runtime and development locks passed strict hash audits with zero known package findings |
| Frontend checks | Passed | Node 24.22.2; lint, six component tests and Vite production build |
| Offline script tests | Passed | 36 tests: 23 release-order regressions plus 13 existing smoke/restore tests |
| Frontend containers | Passed | Both Linux amd64 images built; HTML, nested routes, JavaScript MIME, missing-asset 404s and redirects; actual existing Compose proxy path to port 3000 checked |
| Backend container | Passed | Default non-root user and image command; Gunicorn/gevent served expected story/configuration JSON with temporary SQLite; no startup errors or development/install tools |
| Image security scans | Passed within stated policies | Trivy 0.76.1 with the 2 November vulnerability database; both frontend images reported zero findings; backend had zero Python-package findings and zero fixable HIGH/CRITICAL findings |
| Production-style Compose configuration | Passed | Parsed with temporary inputs; redundant backend command removed so the image owns its runtime flags; full database/media deployment not repeated |
| Workflow validation | Passed | actionlint for all five workflows; changed Actions pinned to verified official releases |
| New release-helper style | Passed | Black 88 and Flake8 with the repository's 88-character/W503 policy; historical modules were not reformatted |
| Terraform checks | Passed | `init -backend=false`, provider checksums for Linux amd64/macOS arm64, `fmt -check` and `validate`; no remote state, plan or apply |

The first backend image test exposed a build-time file-ownership issue: collecting static assets as root created logs that the runtime user could not open. The Dockerfile now runs that step as `app`. Image scanning also found vulnerable libraries bundled inside pip even though the top-level dependency audit passed. The final image removes pip and its ensurepip bootstrap after installation and dependency checks. It retains the application packages; it does not hide package metadata or add unrelated top-level packages to mask bundled dependencies.

Actual Gunicorn startup then exposed a dependency masked by the development environment. The runtime now declares the official `gunicorn[gevent]` extra, which includes the required `packaging` library. The Docker build checks that worker import after removing pip, and CI runs the backend tests inside the built image without network access before scanning or authenticating. Gunicorn's unused control socket is disabled, avoiding an attempted write to the system user's nonexistent home. A final run using the image's default command served both API endpoints without startup errors.

### Remaining findings and scan policy

- **Frontend production dependencies:** no known vulnerabilities in the audit snapshot. The full npm tree retains six moderate findings from one minimatch advisory in the ESLint chain. ESLint 9 is a temporary compatibility choice and needs a supported-version migration with compatible React rules. The [frontend guide](../frontend/README.md#remaining-development-dependency-findings) records the advisory and affected use. CI blocks any production finding and HIGH/CRITICAL findings across the full toolchain.
- **Backend operating system:** the final scan retained 45 HIGH package/advisory records representing nine distinct advisories, with no Debian fix listed. It also reported 71 MEDIUM, 61 LOW and eight UNKNOWN records, and no CRITICAL findings. The existing backend policy continues to block fixable HIGH/CRITICAL findings; it does not mean that all operating-system advisories are resolved. Frontend image scanning blocks all HIGH/CRITICAL findings, including unfixed ones.
- **Dependency freshness:** both Python locks are audited in CI. Fixed package versions and image digests must be deliberately updated; they do not obtain future patches automatically. The frontend images also apply available Alpine updates during a build, so separate builds are not guaranteed to be byte-identical.

The frontend lifecycle fixes are covered by the separate local batch above. Complete repository formatting, the ESLint migration and replacement backup/restore tooling remain later work. The disabled restore commands stay disabled. Current tests do not validate PostgreSQL/GCS integration, migration execution, gameplay/audio in a real browser, load capacity or automatic rollback.

## Local safety review 2 November 2026

The first review batch updates the local source based on `12a466cbf2750042c0934d9b316e4e31040b3ded`. It restores application-configuration add permissions, returns safe API failures, and disables the two unsafe legacy volume-restore commands. Successful API payloads, nullable content, model definitions and storage settings remain unchanged. These checks were performed locally before the hosted release recorded above.

The backend regressions were first run against the original code: 10 failed and 10 passed, exposing the intended permission, error-disclosure and false-success defects. Fake operational commands also confirmed that the original restore scripts could reach service-stop or deletion operations before restoration succeeded. No real recovery operation was executed.

| Check | Result | Scope |
| --- | --- | --- |
| Backend tests | 31 passed | 11 existing tests plus 20 regressions; temporary SQLite database and local storage |
| Public API compatibility | Passed | Existing list/detail/config shapes, optional media, unlinked words, missing configuration, configured music, read-only methods and known HTTP errors |
| Safe failure behavior | Passed | Database/serialization failures return JSON errors without simulated internal details; server logs retain exceptions |
| Offline maintenance tests | 13 passed | Six existing smoke-check tests plus seven restore-entry tests |
| Restore refusal | Passed | 16 calls across the two scripts; arguments, confirmation input and environment variables cannot start operational commands |
| Frontend tests, lint and build | Passed | Six component tests; frontend source and dependencies unchanged |
| Django system and migration checks | Passed | No system-check errors; no model changes requiring migration |
| Changed Python modules | Passed | Black and explicit Flake8 settings for views, serializers and the two new test modules; the admin change is limited to permission checking |
| Shell syntax | Passed | All tracked shell scripts; this does not execute backup, recovery or cloud operations |
| Independent review | Passed | API compatibility, permission handling and restore refusal reviewed separately |

The review baseline also found existing whole-repository formatting issues (28 frontend files and 12 backend files before this batch), dependency advisories and frontend lifecycle defects. Those were outside this first batch. Dependency maintenance, deployment ordering and backend workflow path coverage are addressed in the second batch above; whole-repository formatting and frontend lifecycle work remain separate.

To repeat the relevant checks with dependencies installed in an isolated environment, run the backend suite from `backend/`:

```bash
SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  DATABASE_URL='sqlite:///:memory:' USE_GCS=false DEBUG=false \
  python manage.py test
```

From the repository root, run the offline script tests:

```bash
python -m unittest discover -s scripts -p '*_test.py'
```

From `frontend/`, run `npm run lint`, `npm run test -- --run` and `npm run build`. The focused Python style checks use Black and `flake8 --max-line-length=88 --ignore=W503` on the changed views/serializers and new test modules; the current Flake8 installation does not read the repository's `[tool.flake8]` table without an additional integration.

## New repository: 28 September 2026

These results apply to `jothep/story-filler` at released revision `1713b97ea6264c50c3321ed3fdd164b594cff5ed`, a 190-commit history comprising the 189-commit cleaned baseline and one migration commit. Subsequent documentation commits are not a new application release; the commit and file/blob counts below describe the checked snapshot. The owner made the new repository public on **28 September 2026**. An unauthenticated GitHub repository API request returned HTTP 200 with `private: false`; the former repository remains private.

| Check | Result | Scope and limitation |
| --- | --- | --- |
| [Frontend Pages release](https://github.com/jothep/story-filler/actions/runs/36363233923) | Passed | Lint, component tests, production build and deployment to the new `/story-filler/` path |
| Chrome browser check | Passed | Menu loaded at `https://jothep.github.io/story-filler/`; selecting story 1 displayed text and an image. Full gameplay, audio playback and nested-route refresh were not verified |
| Git-history credential scans | Passed | [Run 36363234688](https://github.com/jothep/story-filler/actions/runs/36363234688) and [run 36363233992](https://github.com/jothep/story-filler/actions/runs/36363233992); pattern-based detection has limits |
| [CodeQL workflow](https://github.com/jothep/story-filler/actions/runs/36363233980) | Completed successfully | Analysis remains advisory; workflow success is not a claim that no alerts exist |
| Fresh-clone credential review | No findings or known-value matches | 214 current tracked files, 190 reachable commits and 682 reachable blobs; Gitleaks plus a supplemental search for 20 known values. Values and private scan inputs are not published |
| Selected old-content lookups in the new repository | HTTP 422 for the old-commit query; HTTP 404 for the old-document query | These specific requests could not retrieve the selected old content. This is not evidence of deletion from the former repository or external copies |
| [Backend delivery, attempt 2](https://github.com/jothep/story-filler/actions/runs/36363802780/attempts/2) | Passed | 11 backend tests, six offline smoke-check tests, JSON-key authentication, image build, Trivy gate, push, Cloud Run update and public API smoke check succeeded |
| Cloud Run after the new release | Verified at 2026-09-28 00:58 UTC | Ready revision `maori-story-backend-00028-gdm`, image tagged with full `1713b97` source SHA, 100% traffic. All environment entries, runtime service account and runtime specification except the image were unchanged |
| Backend workflow-log review | No findings or known-value matches | 23 archive files / 523,552 bytes; Gitleaks 8.30.1 and exact/variant checks covering 20 known values and the new JSON key, including 25 PEM line fragments. This does not establish absence of unknown secrets |
| Independent public API smoke check after release | Passed | Story list/detail and configuration reads only; no writes, media playback or load test |

Frontend, backend and scan results now have new-repository evidence independent of the historical runs below. The [backend verification summary](evidence/backend-migration-verification.json) records the successful attempt and comparison results without credential values or raw logs. The backend retains the existing service-account JSON key method; Workload Identity Federation is not implemented.

## Anonymous verification after publication

After the owner made the repository public on 28 September 2026, an anonymous HTTPS clone at `805c1644080d5b067f0361abe37b222c1035d6c3` was checked with credential helpers and global/system Git configuration disabled. It contained 215 current files, 191 reachable commits and 691 reachable blobs. Gitleaks found no findings in current files or all reachable history. Supplemental matching covered 20 historical/rotated values and the new deployment key, including encoded forms and 25 PEM line fragments; none matched.

All 185 original commit IDs were absent from that clone; all 185 rewritten equivalents were present. Selected old-commit and old-document requests returned HTTP 422/404, including the raw-file URL. The former repository returned HTTP 404 anonymously. These results are recorded in the [public-history verification summary](evidence/public-history-verification.json); later publication-documentation commits are additional to this snapshot.

## Pre-migration live deployment baseline

| Check | Result | Scope |
| --- | --- | --- |
| GitHub Pages in a browser | Passed | Menu loaded from the API; opening a story rendered its illustration, first paragraph and word bank |
| Story list and detail API | HTTP 200 | One story, eight paragraphs and eleven words were observed |
| Configuration API | HTTP 200 | JSON configuration was returned |
| Sample GCS image and audio | HTTP 200 | One image and one audio object were readable; complete audio playback was not tested by this probe |
| Administrator authentication | Passed | Login and logout were verified; the owner also confirmed login |
| Credential rotation | Passed | New database credentials connected; previous credentials were rejected. Cloud Run values matched the private rotation file |
| Cloud Run revision | `maori-story-backend-00026-phc`, 100% traffic | Configuration-only credential update; it retained the previously deployed application image |

The browser reported a normal autoplay restriction before user interaction. These checks do not establish a complete game walkthrough, accessibility compliance, mobile coverage, a performance target, or an availability percentage.

## Legacy local verification of publication changes

| Check | Result | Limitation |
| --- | --- | --- |
| Backend tests | 11 passed | SQLite and local media; not PostgreSQL/GCS integration tests |
| Frontend lint | Passed | Current checked-out source and installed dependencies |
| Frontend tests | 6 passed | Component tests with mocked HTTP/audio |
| Frontend production build | Passed | Does not itself prove the artifact was deployed |
| API smoke-check tests | 6 passed | Covers response validation and retry/error behavior using mocks |
| API smoke check against production | Passed | Public story and configuration reads; no writes or media playback |
| Compose configuration | Three variants parsed | Docker daemon was unavailable; a full local container startup/build was not performed |
| Local routing review | Two corrections implemented | Development API requests now use Nginx's shared origin; production-style Compose strips the frontend base prefix. No container-level routing verification was performed |
| Terraform formatting and validation | Passed | No plan or apply was performed |
| Terraform remote state inventory | Read successfully | The configured GCS backend tracks exactly the four declared resource addresses; this does not prove absence of drift or successful recovery |
| Private local configuration generator | Passed | Owner-only permissions, no credential output, and refusal to overwrite an existing file |
| Credential scan of the portfolio candidate | Gitleaks 8.30.1: no findings | Current files and all 187 reachable commits at `a309a63`; a fresh remote clone also passed. Later revision scans are linked below |
| Known-value search of the portfolio candidate | No residual matches for 16 known values across 650 blobs | Supplemental exact-value check at `a309a63`; does not identify unknown secrets |

The legacy history-scan workflow and updated backend delivery workflow passed in GitHub Actions. Their revision-specific results are recorded below, separately from local checks and the new-repository checks above.

## Delivery evidence

Historical successful runs establish that the earlier delivery paths were used:

- [Backend delivery](https://github.com/jothep/maori-story-fill/actions/runs/25036589237)
- [Frontend delivery](https://github.com/jothep/maori-story-fill/actions/runs/25902475995)
- [CodeQL workflow run](https://github.com/jothep/maori-story-fill/actions/runs/35554033791) — this records workflow completion, not a claim that no alerts exist.

These runs refer to commits from before credential-related history rewriting. They do **not** verify the rewritten commit IDs or the new publication changes. Old-to-new commit mappings are retained privately for audit; private archives and credentials are not portfolio attachments.

## Legacy publication-preparation release runs

| Source revision | Workflow | Result |
| --- | --- | --- |
| `a309a63` | [Frontend delivery](https://github.com/jothep/maori-story-fill/actions/runs/36298824448) | Passed lint, tests, build and Pages deployment |
| `a309a63` | [Git-history credential scan](https://github.com/jothep/maori-story-fill/actions/runs/36298820622) | Passed |
| `a309a63` | [Initial backend release](https://github.com/jothep/maori-story-fill/actions/runs/36298822546) | Tests and image build passed; Trivy blocked 12 fixable HIGH findings before image push or service update |
| `7d80196` | [Git-history credential scan](https://github.com/jothep/maori-story-fill/actions/runs/36299274040) | Passed |
| `7d80196` | [Backend release after remediation](https://github.com/jothep/maori-story-fill/actions/runs/36299274042) | Passed 11 backend tests, 6 smoke-check tests, image build/scan, image push, Cloud Run deployment and public API smoke check |

The blocked findings comprised ten Pillow advisories and two libraries bundled inside pip. Pillow was updated from 12.2.0 to 12.3.0. The final runtime image now removes pip, its ensurepip seed and wheel archives after installation and dependency checks; the builder retains installation tools. Adding unrelated top-level packages would not replace pip's bundled copies. The scan policy and its severity threshold were not relaxed.

In a separate local Python environment with pip and ensurepip absent, application imports and all 11 backend tests passed. The subsequent Linux image scan and deployment also passed in the workflow above. No database schema change is included. Backend lint remains advisory; workflow success does not mean every lint check passed.

After deployment, Cloud Run reported revision `maori-story-backend-00027-bzj` receiving 100% of traffic, with image tag `7d8019603925de68306585f701e5eb5a7442f854`. The database and signing-key values still matched the private rotated configuration. This application release supersedes the configuration-only `00026-phc` baseline above. Passing the configured Trivy gate means no blocking findings under that run's policy and database, not that the image has no vulnerabilities.

## Legacy publication state and new repository

The former `jothep/maori-story-fill` repository remains **private**. The cleaned history was pushed with an exact force-with-lease, and a fresh remote clone passed its full reachable-history scan. The original 185 commits' authorship and timestamps were retained; credential cleanup changed commit IDs. The owner's original staged working draft was not included in the published branch.

A separate GitHub contents-API check found that the previous sensitive document is still retrievable through its old commit ID, outside the new reachable history. That retained content prevents making the former repository public under the owner's publication requirement. A support request has been prepared but not sent. GitHub documents that force-pushing alone may leave cached views accessible and that Support assistance is limited; see [removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). No claim is made that all historic copies have been erased. The chosen publication path is a separate `jothep/story-filler` repository, starting from the 189-commit clean baseline (185 preserved historical commits plus four preparation commits). Its own acceptance evidence is tracked in the migration record, rather than relabelling the old runs.

## Implemented but not fully proven

- Terraform declares the registry, runtime service account, Cloud Run service and public invoker binding, and those four addresses were confirmed in remote state. No clean-room recreation of the whole environment has been demonstrated; Neon, media/state buckets, IAM setup and GitHub configuration are prerequisites outside that resource set.
- Kubernetes manifests preserve the earlier deployment design. The original article reports the historical exercise; the current review did not redeploy a cluster.
- The [local platform lab](local-platform-lab.md) covers Compose, local Kubernetes and the earlier demo separately. The current machine has local cluster tooling, but Colima is stopped. Neither the existing clusters nor other local projects were started or modified. The current NGINX image source now supports `/story-filler/`, but the historical Kubernetes image tags still need replacement with a rebuilt image before a fresh reproduction; the demo has no dedicated dependency lock or substantive tests.
- CodeQL and image scanning are configured. Scan results depend on definitions, scope and advisory settings; no “zero vulnerabilities” claim is made.
- ORM prefetching and image processing exist in code. The previously stated percentage improvements have no reproducible benchmark included here.

The new repository retains the service-account JSON key authentication method used by the old successful releases. The owner configured `GCP_CREDENTIALS` manually as a GitHub Actions secret, and new-repository backend attempt 2 succeeded. Workload Identity Federation is not implemented. The old runs remain historical evidence; the migration record and new-repository section above document the completed migration checks.

## Planned, not claimed as delivered

Workload Identity Federation, Secret Manager integration, automated rollback, hosted Neon/GCS recovery, full application recovery and cutover, measured SLOs, load testing and billing evidence are possible next steps. Application-test PR checks and local PostgreSQL/media recovery tests are implemented and verified in the maintenance batches above.
