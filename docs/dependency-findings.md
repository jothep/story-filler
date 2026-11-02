# Dependency advisory review

Reviewed on **2 November 2026**, starting from `ac6f44e`. This record separates
available fixes, compatibility limits and the findings retained after review.
The [verification record](verification.md) contains the release and test results.

## Changes and remaining counts

The backend image updates `tzdata` to the reviewed stable package
`2026f-0+deb13u1`. After creating the service account, it removes `adduser`,
`passwd` and `mount` through APT. Their four unused dependencies are removed as
well: `libbsd0`, `libsemanage-common`, `libsemanage2` and `libsepol2`.
The service account, essential packages, certificate store, required libraries
and package-manager metadata remain. No application package lock changed.

| Scope | Before | After |
| --- | --- | --- |
| Frontend production dependency findings | 0 | 0 |
| Frontend development findings | 6 moderate packages / 1 advisory | Unchanged |
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

## Frontend: one advisory across six development packages

The fresh production audit reports no findings. The full npm tree reports six
moderate affected packages from the same advisory,
[GHSA-g3hv-75wg-m249 / CVE-2026-118764](https://github.com/advisories/GHSA-g3hv-75wg-m249).
They belong to ESLint's development dependency tree, not the browser bundle.

The compatible minimatch 3.x release is still 3.1.5, which is already installed.
The advisory lists versions below 11.0.1 as affected. Independent installations
confirmed two upgrade obstacles:

- ESLint 10.14.0 still installs minimatch 10.2.6, which remains in that range.
- React plugin 7.37.5 does not support ESLint 10. npm rejects the peer combination,
  and executing the current rules with ESLint 10 fails in `react/display-name`
  because it calls the removed `context.getFilename()` API.

A minimatch 11 override is not a compatible patch: its CommonJS export is an
object, while the current callers expect the function exported by 3.x. Neither
peer checks nor React rules were bypassed. Package versions, the lock and audit
thresholds remain unchanged.

The installed 3.1.5 implementation does not contain the preprocessing functions
described in this advisory. Lint patterns also come from repository configuration,
not website requests. These observations narrow the exposure of this particular
installation; they do not remove the published finding or prove all glob use is
safe. The [frontend guide](../frontend/README.md#remaining-development-dependency-findings)
records the compatibility experiments.

ESLint 9 is also [past its support period](https://eslint.org/version-support/).
It remains a maintenance issue. Revisit the upgrade when a compatible minimatch
fix or dependency range is available and the
[React compatibility issue](https://github.com/jsx-eslint/eslint-plugin-react/issues/3977)
is resolved. Any migration must retain the current React and Hooks checks and
pass their positive and negative test examples.

## Backend: distribution findings and available fixes

The current image uses the pinned official Python 3.13 Debian 13 slim base.
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
