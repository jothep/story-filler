# Security scope and reporting

This is a personal application and infrastructure case study. Its checks cover specific source, dependency, container and runtime concerns; they do not establish that the application is free of vulnerabilities.

## Reporting

Use GitHub private vulnerability reporting from the repository's Security tab when available. Do not post credentials, personal data, or an exploitable vulnerability in a public issue. Ordinary, non-sensitive bugs can be reported through Issues.

## Implemented controls and boundaries

| Control | What it does | Boundary |
| --- | --- | --- |
| Gitleaks workflow | Scans fetched Git history; redacts findings in logs | Pattern-based detection cannot identify every secret. This is an independent workflow, not an enforced deployment dependency |
| Backend Trivy step | Blocks image publication for fixable HIGH/CRITICAL findings | Unfixed findings are ignored by the gate; databases and definitions change over time |
| CodeQL workflow | Configures source analysis for Python and JavaScript/TypeScript | Analysis is advisory (`continue-on-error`); a successful workflow alone does not prove zero findings |
| Non-root backend image | Runs the application without container root privileges | Does not isolate the application from its own database or storage permissions |
| Private configuration | Runtime credentials are supplied outside tracked source; environment and backup files are ignored | Git ignore rules do not protect files already committed; Terraform state can contain sensitive values |
| API smoke check | Exercises public story and configuration reads after deployment | Does not verify authorization, media playback, writes, rollback or recovery; failure does not automatically roll back |

Cloud Run currently receives database credentials and the Django signing key as environment variables. GitHub Actions authenticates using a service-account JSON credential in GitHub Secrets. Workload Identity Federation and Secret Manager integration are **not implemented** in the current configuration.

## September 2026 publication preparation

Previously committed credentials were identified during review. Database credentials and the Django signing key were rotated, the running service was checked, and old database authentication was confirmed to fail. Local configuration and private recovery copies were kept outside tracked source.

Source cleanup and Git-history rewriting are separate from revocation. The [verification record](docs/verification.md) records the scope and state of history scans and remote publication checks. A clean reachable history does not prove that old clones, service caches or external copies have been erased.

Templates use empty values or environment references. Development setup generates local values instead of providing shared default passwords. Container build contexts exclude local environment and credential files.

## Further work

Candidate improvements include keyless CI authentication, versioned secret references, deployment gates that depend on security checks, and a tested recovery procedure. They remain proposals until implemented and verified. Current evidence and limitations are maintained in [docs/verification.md](docs/verification.md).
