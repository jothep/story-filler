# Dependency advisory review

Reviewed on **2–3 November 2026**: Debian cleanup, frontend tooling migration,
then the backend base-image replacement from `a16507e`. This record separates
available fixes, compatibility limits and the findings retained after review.
The [verification record](verification.md) contains the release and test results.

## Current backend: Alpine runtime (3 November)

The runtime now uses the official Python 3.13.18 Alpine 3.24 image, pinned by
multi-platform digest. Application dependency versions, Python minor version,
Django LTS version, Gunicorn command and UID 100/GID 101 are unchanged.
The stable Alpine base currently supplies `tzdata` 2026e rather than Debian's
2026f. The application uses UTC; Auckland summer (+13) and winter (+12) offsets
were also checked. Future time-zone changes still require routine base updates.

Alpine uses musl rather than glibc. Thirty-five runtime dependencies have
compatible wheels. `google-crc32c` and `zope-interface` need source builds. A
separate stage verifies their published source hashes and compiles them with
locked Python build tools and Alpine's CRC32C development library. The runtime
contains the resulting wheels and required shared libraries, without compilers,
headers, build tools, pip or ensurepip. CRC32C must use its C implementation;
a silent pure-Python fallback fails verification.

The baseline and candidates were scanned with Trivy 0.76.1 and the same database
updated at `2026-11-02T07:17:05Z`. Full results include unfixed findings and all
severities. Package-manager metadata is retained.

| Check | Previous Debian runtime | Alpine runtime |
| --- | --- | --- |
| OS packages identified | 80 | 32 |
| Python runtime packages identified | 37 | 37 |
| Trivy OS records | 41 HIGH, 70 MEDIUM, 57 LOW, 8 UNKNOWN | 0 reported |
| Distinct HIGH advisories from the previous image | 9 | 8 addressed by component replacement/removal; 1 remains affected |
| Python dependency findings | 0 | 0 |

**The Alpine scan's zero does not mean that every known issue is fixed.**
SQLite 3.53.4 is built with FTS5 and remains affected by
[CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373).
The Alpine package has no relevant backport, and the Alpine advisory feed used by
this scan omits it. The upstream fix is in SQLite 3.54.0. This remains a tracked
HIGH issue even while the image gate passes. Production uses PostgreSQL and the
application does not use SQLite FTS5; local SQLite support is retained. Those
usage facts limit the known application path but do not fix the library.

| Previous HIGH group | Alpine assessment |
| --- | --- |
| util-linux CVE-2026-76642 / 78409 / 78410 | The installed `libuuid` is 2.42.3, which includes the upstream fixes. |
| util-linux CVE-2026-78408 | The affected util-linux `nsenter` implementation is absent. The image's BusyBox implementation is a different component; this is removal of the affected code, not a claim that util-linux 2.42.3 fixes this advisory. |
| ncurses CVE-2025-69720 | The installed 6.6 release is newer than the upstream fix; the affected `infocmp` tool is also absent. |
| acl CVE-2026-54369, systemd CVE-2026-16742, perl CVE-2026-9538 | These packages/components are absent from the new runtime. |
| SQLite CVE-2026-119373 | Still affected; review the next stable Alpine SQLite package and repeat native/database tests before updating. |

Do not add an ignore rule for the SQLite issue or replace the stable system
library with an unreviewed cross-distribution package. The next check is whether
Alpine's stable branch supplies SQLite 3.54.0 or a confirmed backport. See
[SQLite releases](https://www.sqlite.org/changes.html) and the advisory above.

Google's Debian 13 Distroless Python candidate was also built and tested. It
retained 38 OS packages and the same 37 application dependencies. Its native
checks and Django tests passed, but the Debian Python 3.13.5 package still carried
five additional HIGH advisories (CVE-2026-15308, 19445, 19553, 7210 and 82049).
It removed three of the previous HIGH groups while retaining six, leaving eleven
distinct HIGH advisories. That candidate was not selected. Comparing only package
record totals would have concealed the additional interpreter findings.

## Earlier Debian cleanup (2 November)

The backend image updates `tzdata` to the reviewed stable package
`2026f-0+deb13u1`. After creating the service account, it removes `adduser`,
`passwd` and `mount` through APT. Their four unused dependencies are removed as
well: `libbsd0`, `libsemanage-common`, `libsemanage2` and `libsepol2`.
The service account, essential packages, certificate store, required libraries
and package-manager metadata remain. Backend Python dependency locks were
unchanged by that OS follow-up.

| Scope | Before | After |
| --- | --- | --- |
| Frontend production dependency findings | 0 | 0 |
| Frontend development findings | 6 moderate packages / 1 advisory | 0 |
| Backend OS HIGH records | 45 | 41 |
| Backend OS MEDIUM records | 71 | 70 |
| Backend OS LOW records | 61 | 57 |
| Backend OS UNKNOWN records | 8 | 8 |
| Backend OS CRITICAL records | 0 | 0 |
| Distinct backend OS advisories | 85, including 9 HIGH | Unchanged |
| OS records with a vendor fix listed | 0 | 0 |

The two images were scanned against the same vulnerability database. The nine
fewer package-level records reflect removal of unused components, not nine fixed
vulnerabilities. Other binary packages still carry the shared source-package
findings. Both Python locks and the final image's Python packages report zero
known findings with the corrected audit coverage below.

## Python audit coverage corrected

The previous `pip-audit --strict --require-hashes` command used a temporary pip
environment. Its installation report omitted packages already installed there:
`packaging` from the runtime lock, and `packaging`, `pip`, `setuptools` and `wheel`
from the development lock. The reports covered 36/37 and 76/80 entries without
reporting a collection failure.

The audit now uses `--disable-pip` to read the complete pinned locks directly.
All **37 runtime entries and 80 development entries** are included, with no known
vulnerabilities found. Installation still enforces distribution hashes and runs
`pip check`; direct advisory lookup does not replace those checks.

A separate [coverage check](../scripts/check_dependency_audit.py) compares each
name and version in the report with the generated hash lock. Its regression tests
reject the observed omissions, skips, duplicates, wrong versions and unsupported
lock syntax. CI uses a fail-on-error pipeline so saving the JSON cannot conceal
the scanner's failure. This fixes a monitoring gap; it does not claim that the
omitted packages previously contained a known vulnerability.

## Frontend: affected development dependency tree replaced

The previous six moderate package findings shared
[GHSA-g3hv-75wg-m249 / CVE-2026-118764](https://github.com/advisories/GHSA-g3hv-75wg-m249).
An ESLint 10 upgrade retained affected minimatch versions and was incompatible
with the existing React plugin. A minimatch major-version override changed the
CommonJS API expected by its callers. Those options were not used.

The frontend now uses **Oxlint 1.90.0 plus TypeScript 6.0.3 checkJs**. ESLint,
its React/Hooks plugins and their affected dependency chain are removed from the
lock. Production and full-tree npm audits both report zero known findings.
The two frontend workflows now reject findings at every severity, rather than
allowing moderate development advisories.

This replacement preserves the intent of the reviewed 82 JavaScript, React and
Hooks rules through direct rules, syntax checks and type checks. Positive and
negative regression cases cover the replacement paths. The
[frontend guide](../frontend/README.md#javascript-react-and-type-checks) explains
specific differences, including JSDoc prop contracts and the small React wrapper
name check. Prettier is retained.

Native tooling was examined separately from npm advisories:

- The clean local installation verified registry signatures for 178 packages and
  attestations for 56 packages.
- Oxlint's Linux x64 native package integrity and provenance match release commit
  `9b6fff42fa6edf0bec55861b6f0764c7b9acd86b` for
  [oxlint_v1.90.0](https://github.com/oxc-project/oxc/releases/tag/oxlint_v1.90.0).
- Trivy found no known advisories in the 441 Rust dependency entries identified
  from that release's Cargo lock and workspace manifests. This source-level
  check supplements package provenance; it does not claim that a stripped native
  binary exposes every compiled dependency to a scanner.
- The optional Go-based `oxlint-tsgolint` package is absent. An alternative
  Go-based linter was rejected after its bundled runtime reported known HIGH
  findings, despite a clean npm audit.

These are dated scans, not a guarantee against future advisories. Update tool
versions and repeat compatibility, registry and native-dependency checks together.

## Earlier Debian assessment (2 November)

The image reviewed in this earlier batch used the pinned official Python 3.13
Debian 13 slim base.
Runtime and development Python locks are audited separately from operating-system
packages. A passing Python audit does not clear Debian findings.

The Debian stable repositories were checked for every installed package, not
only those with HIGH findings. The only available package update was
`tzdata` from 2026e to 2026f. No candidate package update addressed the reported
vulnerabilities. The dated Debian tracker also listed the corresponding stable
release entries as open.

Some fixes already exist upstream or in Debian's development distribution.
Those are not interchangeable with tested stable packages. This review does not
mix distributions or replace system libraries with hand-built versions to lower
the scan count. SQLite, TLS and other libraries used by Python remain installed.

The HIGH findings fall into the following groups. One advisory can be reported
against several binary packages built from the same source package.

| Source package | Advisory | Why a compatible patch is not applied |
| --- | --- | --- |
| util-linux | [CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642), [CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408), [CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409), [CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410) | The stable packages remain affected; a safe update is not available in the selected repository. Essential packages and required libraries are retained. |
| acl | [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369) | The upstream fix introduces new interfaces. Debian lists a future stable point update rather than an individual backport. |
| ncurses | [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720) | Debian stable has no security update for this command-line tool issue. Python's linked terminal libraries are retained. |
| sqlite3 | [CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373) | The stable package has no fix. The library is used by Python and local application tests; deleting it breaks supported behavior. |
| systemd | [CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742) | A fix exists in newer upstream/development releases, but the selected stable package has no update. A source-package finding does not by itself establish that its vulnerable daemon is installed or reachable. |
| perl | [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538) | Debian postpones the stable update while upstream regressions are resolved. Essential base components are not forcibly removed. |

## Maintenance rules

- Keep full scan counts separate from release thresholds. The backend gate blocks
  fixable HIGH/CRITICAL findings; the full report includes unfixed findings and
  every severity. A successful gate is not a zero-vulnerability result.
- Preserve package-manager metadata. Remove an unused package through its package
  manager, then check dependency consistency and the actual application runtime.
- Recheck stable security updates and base-image releases before the next image
  update. Keep an exact record of version changes and repeat runtime tests.
- Do not suppress an advisory simply because the affected feature appears unused.
  Record that observation separately from vendor status and patch availability.

Sources: the [Debian security tracker](https://security-tracker.debian.org/tracker/),
the advisory links above, and the npm package metadata and compatibility tests
linked from the frontend guide. Counts and patch availability are dated evidence.
