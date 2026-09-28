# Legacy delivery history — evidence snapshot

This is a retrospective snapshot of the **private legacy repository `jothep/maori-story-fill`**, collected on **28 September 2026 (UTC)** before migration to a new public repository. The legacy repository remains private. These figures describe its retained history; they are not activity counts for the new repository.

## Suggested portfolio wording

> The private development repository records 185 original commits between October 2025 and May 2026, followed by four publication-preparation commits in September 2026. Its retained GitHub Actions history contains 198 workflow runs across 132 source commits: 126 completed successfully and 72 failed. The failures and pipeline revisions are part of the development record. These are workflow-run counts, not deployment counts or estimates of hours worked.

## Actions snapshot

The authenticated GitHub Actions API returned 198 runs across two pages. All were completed, and all reported a single attempt (`run_attempt = 1`), so there were 198 observed attempts and no reruns in this snapshot. There were 174 push-triggered runs, 21 scheduled runs and three manually dispatched runs.

The earliest retained run started on 18 October 2025 at 23:51:12 UTC; the latest started on 27 September 2026 at 06:18:37 UTC. This snapshot covers the records returned by GitHub, without claiming to recover deleted or expired records.

| Workflow family | Runs | Success | Failure |
| --- | ---: | ---: | ---: |
| Earlier backend CI | 41 | 21 | 20 |
| Initial combined pipeline | 1 | 1 | 0 |
| CodeQL analysis | 50 | 45 | 5 |
| Cloud Run delivery | 18 | 6 | 12 |
| GitHub Pages delivery | 37 | 28 | 9 |
| Earlier frontend CI | 48 | 22 | 26 |
| Git history credential scan | 3 | 3 | 0 |
| **Total** | **198** | **126** | **72** |

A successful workflow can represent a test, scan, build or delivery pipeline. Even the six successful Cloud Run workflow runs and 28 successful Pages workflow runs are **workflow completion counts**, not independently measured deployment counts. Per-workflow source-commit counts overlap; only the repository-wide deduplicated total is 132.

## Git history and source snapshot

The original history contains 185 commits. The cleaned legacy `main` contains the same 185 preserved commits plus four later commits, for a total of 189. Rewriting history changed commit identifiers; it did not create another 185 units of work. Do not add 185 and 189 together.

| Recorded author month (UTC) | Original history | Cleaned legacy main |
| --- | ---: | ---: |
| October 2025 | 84 | 84 |
| March 2026 | 24 | 24 |
| April 2026 | 68 | 68 |
| May 2026 | 9 | 9 |
| September 2026 | 0 | 4 |
| **Total** | **185** | **189** |

Git author-name labels are `Xiang` (184 original / 188 cleaned-main commits) and `jothep` (one commit in each history). These labels do not establish separate people, roles, sole authorship or the extent of assistance. Commit counts and dates do not establish hours worked or engineering complexity.

The cleaned source snapshot contains 210 tracked files. Static inspection identifies:

- 11 maintained backend test methods, six frontend test cases and six offline smoke-check test methods. These counts are not coverage percentages or fresh execution results.
- Four Terraform resource declarations across two configuration files: Artifact Registry, a service account, Cloud Run and its public-invoker IAM membership. This does not mean Terraform manages the complete environment.
- Ten Infra YAML files containing 12 Kubernetes resource documents: two Deployments, one StatefulSet, three Services, one Ingress, one PVC, two Jobs and two Pods. A Helm values file adds configuration, not another workload.
- Three Compose files, four Dockerfiles and five current GitHub workflow files. The historical Actions families above include earlier workflows that have since changed or been removed.

The local Compose environments, Kubernetes lab and prototype have implementation evidence, but these counts do not show that they were rerun during this review. Runtime verification is documented separately.

## Data and publication boundary

- `legacy-actions-metrics.json`: API snapshot, status/conclusion/event grouping, workflow-level counts and timestamps, attempt accounting and deduplicated commit count.
- `legacy-repository-metrics.json`: original and cleaned-history counts, author-label and month distribution, tracked-file types and static implementation counts.

The published evidence deliberately excludes commit identifiers, commit messages, run identifiers, private email addresses, credentials and private backup locations. It contains aggregate results, not raw API responses. Any accompanying GitHub screenshots require a separate visual review and should be labelled as a snapshot of the legacy private repository.
