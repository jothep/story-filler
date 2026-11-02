# Source security review and gate closeout

Review date: **3 November 2026**. This record covers 11 open CodeQL alerts and
the associated merge, publication and recurring-check configuration. It does not
replace the dated [dependency review](dependency-findings.md) or
[verification record](verification.md).

**Status: implementation and local review prepared; remote closeout pending.**
The baseline contained three HIGH and eight MEDIUM alerts, all open, with their
latest recorded analysis at commit
`8ef92114802332e9239e7e250db333d8a37a3bcc`. Locations below refer to that baseline,
not the changed files. No alert is treated as closed solely because code or tests
changed. Fresh CodeQL analysis and repository-side enforcement evidence must be
recorded in the final section before claiming completion.

## Alert-by-alert assessment

| Alert | Severity and rule | Baseline location | Source and reachability assessment | Change and regression coverage |
| --- | --- | --- | --- | --- |
| [#1](https://github.com/jothep/story-filler/security/code-scanning/1) | HIGH · `py/reflective-xss` | `demo/polls/views.py:11`, detail | `<int:question_id>` already rejects markup in public URLs; direct callers could bypass the converter. Default HTML response type was unnecessary. | Explicit `text/plain; charset=utf-8` and `nosniff`; numeric route text, malformed route rejection and direct-call markup covered. |
| [#2](https://github.com/jothep/story-filler/security/code-scanning/2) | HIGH · `py/reflective-xss` | `demo/polls/views.py:16`, results | The same integer converter protects the public results URL. The response body is a plain message, not an HTML page. | Explicit plain-text response and `nosniff`; original text and hostile alternate-call values covered. |
| [#3](https://github.com/jothep/story-filler/security/code-scanning/3) | HIGH · `py/reflective-xss` | `demo/polls/views.py:20`, vote | The vote URL also supplies an integer. The alert does not demonstrate a reachable reflected script through that route. | Explicit plain-text response and `nosniff`; original text and hostile alternate-call values covered. |
| [#12](https://github.com/jothep/story-filler/security/code-scanning/12) | MEDIUM · `py/log-injection` | `backend/core/views.py:34`, list IP | `REMOTE_ADDR` is server-provided request metadata, not a raw forwarded header. Its provenance limits the ordinary attacker path; the log sink still lacked escaping. | Escape IP fields at the sink; malformed metadata cannot add log lines or terminal controls. |
| [#13](https://github.com/jothep/story-filler/security/code-scanning/13) | MEDIUM · `py/log-injection` | `backend/core/views.py:94`, requested ID | `<int:pk>` already prevents control characters in a public story ID. Alternate view callers are outside that route guarantee. | Escape the log-only ID; normal integer messages and malicious direct calls covered. |
| [#14](https://github.com/jothep/story-filler/security/code-scanning/14) | MEDIUM · `py/log-injection` | `backend/core/views.py:95`, detail IP | Server metadata has the same provenance limit as #12; it was interpolated into a plain-text log entry. | Escape IP fields; detail-request output remains readable and on one line. |
| [#15](https://github.com/jothep/story-filler/security/code-scanning/15) | MEDIUM · `py/log-injection` | `backend/core/views.py:104`, successful ID | Public ID remains integer-constrained. The stored title already uses `%r`, which renders control characters visibly. | Reuse the escaped ID for success logging; retain title representation and unchanged API data. |
| [#16](https://github.com/jothep/story-filler/security/code-scanning/16) | MEDIUM · `py/log-injection` | `backend/core/views.py:111`, missing ID | Public ID remains integer-constrained; the warning itself accepted an unescaped alternate-call value. | Use the escaped ID in the warning; malformed values stay on one line and the response remains 404. |
| [#17](https://github.com/jothep/story-filler/security/code-scanning/17) | MEDIUM · `py/log-injection` | `backend/core/views.py:116`, failed ID | Public ID remains integer-constrained. The log message and exception traceback are separate outputs. | Escape the message's ID while preserving `exc_info`, traceback diagnostics and the existing safe 500 response. |
| [#18](https://github.com/jothep/story-filler/security/code-scanning/18) | MEDIUM · `py/log-injection` | `backend/core/views.py:139`, config IP | Server metadata has the same provenance limit as #12; the log sink lacked explicit escaping. | Escape IP fields; configuration-request logging covered alongside list/detail logging. |
| [#19](https://github.com/jothep/story-filler/security/code-scanning/19) | MEDIUM · `js/file-access-to-http` | `frontend/scripts/check-pages-fallback.mjs:81` | Generated HTML supplies asset paths to an intentional local HTTP check. The original string concatenation warrants a destination-boundary review, but exfiltration was not demonstrated: Node 24 fetch rejects credential-bearing URLs used in the proposed origin-switch construction. | Resolve every HTML reference against a build-directory inventory before sending requests. Request paths come from that inventory, with a fixed loopback origin and redirects rejected. Real local HTTP tests cover valid assets, malformed/external/credential-bearing paths and redirected destinations. |

The historical demo's **index view had an additional, unreported stored-HTML
problem**: question text from the database was concatenated into an HTML response.
Unlike the three integer-ID routes, that content is not constrained by a URL
converter. The index now uses the same plain-text content type and `nosniff`,
preserving the text while making stored markup inert. Tests supply synthetic
stored markup through a mocked query. The `demo/` project remains preserved and
included in Python analysis; it was not deleted or excluded to remove alerts.

The logging helper renders CR/LF, terminal controls, Unicode line separators and
bidi controls as visible escape sequences. Literal backslashes are escaped first
so the original values remain distinguishable. Normal IPs, IDs and printable
Māori text remain readable. This change protects the selected log fields, not
arbitrary exception contents or every logger in the process; normal multiline
tracebacks are retained deliberately.

The Pages check remains a local test tool, not a production request endpoint.
HTML selects only files listed in the build-directory inventory; it cannot supply
an arbitrary request string. Every reference is validated before any request is
sent. Boundary tests use loopback servers and synthetic inputs, including an
unknown reference that must cause zero requests and a second server that must
receive no redirected request. The original finding is recorded
as an intentional file-to-request flow with hardening, not a confirmed production
data leak. No query exclusion, source suppression or alert dismissal is used as a
substitute for the final scan.

## Merge and publication policy

The [source workflow](../.github/workflows/codeql-analysis.yml) runs for all pull
requests to `main`, without path filters, and is reusable
by release and maintenance workflows. It analyzes Python and JavaScript/TypeScript
with `security-extended` and scans all fetched Git history with Gitleaks. The
original workflow file, `analyze` job identifier and language categories are
retained. Actual alert closure is verified from the main-branch release analyses;
a successful PR scan alone does not establish it. A final `Security Gate` job uses `if: always()` and requires both
the analysis matrix and credential scan to succeed, so failed or skipped
dependencies do not become a successful aggregate check.

The [SARIF gate](../scripts/check_codeql_results.py) runs only after the official
analyzer succeeds and writes a fresh runner-temporary report. It requires exactly
one regular report for the selected language, SARIF 2.1.0, nonempty runs, CodeQL
tool identity and explicit results arrays. **Every reported result blocks**:
there is no severity threshold, suppression allowance, baseline exemption or
missing-rule escape. Missing/malformed reports, duplicate JSON keys, failed
invocations and error-level analysis notifications also fail. Optional invocation
metadata may be absent; the parser cannot independently prove execution or source
coverage. Failure output contains only restricted rule IDs/counts or fixed
validation messages. SARIF artifacts are retained for 30 days.

Main-branch backend image publication/deployment, GitHub Pages deployment and
manual frontend-image publication depend on fresh reusable security checks for
their caller commit. Backend/Pages pull requests receive their source-security
status from the separate source workflow. The merge boundary additionally needs
the repository's required-check settings to require `Security Gate`; YAML alone
cannot enforce branch protection. The five required checks are `Security Gate`, `Test backend and maintenance
scripts`, `Verify the candidate image; publish from main`, `Check and Build
Frontend`, and `Restore synthetic data in isolated Docker resources`. Each runs
for every PR and is restricted to the GitHub Actions app. The sole-owner workflow
requires a PR but no additional GitHub reviewer; independent review is recorded
before merge.

The Actions allowlist contains 17 reviewed commit-SHA pins, including the internal
actions used by the Trivy/setup/cache and Pages composites. Obsolete mutable tags
and `master` allowances were removed; blanket GitHub-owned and verified-action
permissions remain disabled. Old workflow versions using those retired references
cannot simply be rerun under the tightened policy.

Image gates reject HIGH/CRITICAL vulnerabilities **including unfixed findings**
and exposed secrets. Complete vulnerability reports retain all severities and
package records. Dependency audits retain their existing strict coverage and
all-severity policies. There is no new security ignore file, lowered severity
threshold or silent allowance for these source alerts.

## Keeping the checks proportionate

A required job still starts for every PR. For a strictly confirmed documentation-only
PR, image rebuilding and the Docker recovery exercise are skipped inside their
jobs; the status checks do not disappear or remain pending. The scope check allows
only root Markdown files and Markdown under `docs/`. Source files, workflows,
locks, application documentation and unknown paths keep the full checks. Renames
include both old and new paths. Invalid metadata or a failed comparison fails the
job; only an explicit `docs_only=true` permits the cheaper path.

The frontend checks, backend unit/style/dependency checks and source/history
checks remain active for documentation PRs. Main publication and manual/scheduled
validation always use the full path. The redundant standalone main-push CodeQL
trigger was removed. Each actual application publication keeps its own fresh scan;
when both apps publish, that small duplication avoids introducing cross-workflow
polling, cached scan decisions or another publication trust boundary.

A finding blocks automatic publication for assessment; it does not establish
exploitability. A future confirmed false positive needs a documented source/sink
and reachability review, a narrow rationale and independent review of any precise
gate exception. Broad query exclusions and unexplained dismissals are not the
remedy. No exception is needed for this batch's final source changes.

## Recurring maintenance

[Scheduled security maintenance](../.github/workflows/security-maintenance.yml)
is configured for **Monday 18:17 UTC** and manual dispatch. Its independent jobs
repeat source/history analysis, audit all three Python locks with coverage checks,
audit full and production JavaScript dependencies, and build/scan both application
images. SARIF, Python audit and complete image reports have 30-day retention.
Scheduled runs use the current default-branch revision; they do not publish an
image, deploy an application or receive cloud credentials.

These scans detect newly reported issues in locked dependencies and images; they
do not apply upgrades automatically. A passing run remains dated evidence of the
selected scanners and advisory databases. A failing maintenance run requires
triage and a reviewed change, followed by fresh checks. The schedule's first
successful remote run still needs to be recorded below.

## Validation findings

The first hosted run proved both gates can stop the change: JavaScript analysis
completed successfully but the SARIF gate rejected the remaining file-to-HTTP
result, and `Security Gate` failed. Its report led to the inventory-based Pages
change above; no suppression was added.

Hosted frontend tests also exposed an existing asynchronous test race: waiting
for the story list did not ensure the independently fetched music configuration
had arrived. The test now controls that response explicitly, verifies no audio
before configuration, then requires one audio object with the correct path after
it resolves. Production playback behavior is unchanged.

## Verification and remaining evidence

Local regressions cover plain-text demo responses, malformed logging fields,
unchanged public API behavior, loopback request restrictions and positive/negative
SARIF gate outcomes. Backend database checks must use isolated PostgreSQL and
synthetic data; demo response tests prohibit database access. Production databases,
media, secrets and cloud deployment are outside this local validation.

| Evidence | Status to record before final closeout |
| --- | --- |
| Local test, lint, formatting and image results | 522 automated tests passed: 40 PostgreSQL Django, 172 maintenance, four demo, 229 lint/type contracts, 71 component and six Pages HTTP tests. Seven recovery integration scenarios passed. Formatting, lint/types, actionlint, build, history scan and complete dependency/image audits passed. Final hosted results are recorded separately below. |
| Pull request and exact analyzed commit | Pending URL and commit. |
| Fresh Python and JavaScript CodeQL reports | Pending successful remote runs, retained report links and zero-result gate output. |
| Alert state after analysis | Pending read-back of all 11 baseline alerts; do not infer `fixed` from a passing local test. |
| Required-check enforcement | Applied and read back: strict checks from GitHub Actions, administrator enforcement, PR-only changes, no force pushes/deletions and resolved conversations. PR #5 at `a18937f` was BLOCKED while its frontend and security checks failed. The final passing head remains to be recorded. |
| Main-branch release dependencies | Pending remote run evidence tying successful checks to the published caller commit. |
| Weekly/manual maintenance workflow | Pending first remote run and retained report links. |

Earlier publication/test figures remain in the historical records. They are not
reused as proof that this candidate, its new gates or its branch settings have
passed.
