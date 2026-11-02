# Security scope and reporting

This is a personal application and infrastructure case study. Its checks cover specific source, dependency, container and runtime concerns; they do not establish that the application is free of vulnerabilities.

## Reporting

Use GitHub private vulnerability reporting from the repository's Security tab when available. Do not post credentials, personal data, or an exploitable vulnerability in a public issue. Ordinary, non-sensitive bugs can be reported through Issues.

## Implemented controls and boundaries

This table describes the policy configured in this revision. The
[November security review](docs/security-closeout.md) separates local validation,
remote scan results and required-check enforcement; workflow configuration alone
does not establish that branch protection is active.

| Control | What it does | Boundary |
| --- | --- | --- |
| Gitleaks workflow | Scans fetched Git history with redacted findings; participates in reusable source/release checks | Pattern-based detection cannot identify every secret; the fetched history does not include every external copy |
| Image Trivy gates | Reject HIGH/CRITICAL vulnerabilities, including unfixed findings, and exposed secrets before image publication | Lower-severity vulnerabilities do not block this gate; databases and definitions change over time. Complete vulnerability/package reports are retained separately |
| CodeQL and SARIF gate | Analyzes Python and JavaScript/TypeScript with `security-extended`; rejects every reported result and missing, malformed or failed analysis reports | Zero reported results is limited to the selected analysis. The gate does not establish source coverage or detect findings omitted by the analyzer |
| Merge and release checks | Exposes a stable `Security Gate` check; main-branch publication depends on fresh source and credential scans of the caller commit | Merge enforcement requires repository-side required checks. Its read-back verification is recorded separately from workflow changes |
| Scheduled security maintenance | Configures weekly source, credential, complete Python/JavaScript dependency and application-image scans | Runs without cloud credentials or deployment; it does not patch dependencies or redeploy a running image |
| Non-root backend image | Runs the application without container root privileges | Does not isolate the application from its own database or storage permissions |
| Private configuration | Runtime credentials are supplied outside tracked source; environment and backup files are ignored | Git ignore rules do not protect files already committed; Terraform state can contain sensitive values |
| API smoke check | Exercises public story and configuration reads after deployment | Does not verify authorization, media playback, writes, rollback or recovery; failure does not automatically roll back |

Cloud Run currently receives database credentials and the Django signing key as environment variables. The backend workflow retains service-account JSON key authentication through the `GCP_CREDENTIALS` GitHub Actions secret and the authentication action's `credentials_json` input. The owner configures this secret manually in the new repository; no key value belongs in source or public evidence. Workload Identity Federation and Secret Manager integration are not implemented. See the [migration record](docs/repository-migration.md) for execution evidence.

## September 2026 publication preparation

Previously committed credentials were identified during review. Database credentials and the Django signing key were rotated, the running service was checked, and old database authentication was confirmed to fail. Local configuration and private recovery copies were kept outside tracked source.

Source cleanup and Git-history rewriting are separate from revocation. The [verification record](docs/verification.md) records the scope and state of history scans and remote publication checks. A clean reachable history does not prove that old clones, service caches or external copies have been erased.

Templates use empty values or environment references. Development setup generates local values instead of providing shared default passwords. Container build contexts exclude local environment and credential files.

## Further work

Candidate improvements include keyless CI authentication, versioned secret references, and a tested hosted Neon/GCS recovery procedure. Local Docker recovery is documented separately. These hosted changes remain proposals until implemented and verified. The [security closeout record](docs/security-closeout.md) tracks scan and gate verification; broader evidence and limitations remain in [docs/verification.md](docs/verification.md).
