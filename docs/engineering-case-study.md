# Story Filler: Infrastructure and Delivery Case Study

This personal project complements my years of enterprise work with recent, inspectable infrastructure practice. It is a small story-based learning application with a React frontend, a Django API and administration interface, PostgreSQL data, and uploaded media.

The engineering case concerns how those components are deployed, where their state lives, and how changes reach a running service. The [first article](https://medium.com/@shelldry325/from-on-premises-kubernetes-to-zero-cost-serverless-architecture-a-practical-guide-to-cloud-70e68304e835) describes the migration. This case study connects that account to the current implementation and its limits.

## Evidence and scope

This document reflects the September 2026 review and pipeline runs in the former private repository, `jothep/maori-story-fill`. Its historical run links may require access; the public [aggregate snapshot](evidence/README.md) records the retained activity without exposing private raw records. New-repository work is recorded in the [migration record](repository-migration.md). The [verification record](verification.md) separates implementation, observed deployment behaviour, and pending work.

At the pre-migration check on 27 September, Cloud Run served image **7d80196** through revision **00027-bzj**, receiving 100% of traffic. Revision **00026-phc** was the earlier credential-rotation baseline; the newer release has completed the backend pipeline and public API smoke check.

The project is a single application and a personal infrastructure exercise. Its Kubernetes manifests demonstrate an earlier deployment implementation. This review did not recreate that cluster, establish a service availability history, or conduct a disaster recovery exercise.

## Architecture evolution

Local environments are part of the case. [Development Compose](../docker-compose.dev.yml) binds source into Django and Vite containers for iteration, connects services through a bridge network, and separates database/media data into named volumes. [Nginx](../nginx.dev.conf) provides frontend, API, admin and media routes; relative API requests are the intended single-origin path. This makes routing and persistence inspectable locally.

The [Kubernetes implementation](../Infra/) develops those concerns into Deployments and Services, PostgreSQL StatefulSet storage, a media PVC, migration and administrator Jobs, and network/database troubleshooting Pods. The separate Jobs distinguish finite administration tasks from serving application traffic. Resource settings and probes exist for PostgreSQL; application probes, Ingress TLS and autoscaling are not implemented in these manifests.

The [demo](../demo/) is a separate, smaller application: Django serves stories with full_text and directly associated words, while its MUI frontend reads that content from list responses at a fixed local API address. The main application instead has separate list/detail contracts and paragraph, blank-link and media structures. Demo Compose starts only PostgreSQL. Its contract should not be substituted for the production API.

The [local platform lab](local-platform-lab.md) records September fixes to same-origin API routing and repository-prefix handling. Compose parsing passed; demo execution, Kubernetes recreation and a fresh Compose startup remain unverified.

The migration changed the operating model:

| Responsibility | Earlier implementation | Current architecture |
|---|---|---|
| Frontend hosting | Nginx container | GitHub Pages |
| Application runtime | Django container in Compose or Kubernetes | Cloud Run |
| Relational data | PostgreSQL with local persistent storage | Neon PostgreSQL |
| Uploaded media | Mounted filesystem storage | Google Cloud Storage |
| Infrastructure changes | Local deployment configuration | A defined Terraform scope |

The [current architecture document](architecture-production-gcp.md) describes the boundaries in more detail. GCS is the current media backend; the first article's S3-compatible storage description represents an earlier implementation.

## Decisions worth examining

**Match operations to the workload.** The original article explains the shift toward lower cloud and maintenance costs for a personally maintained application. The current Terraform configuration allows zero to one Cloud Run instance. This limits provisioned capacity and accepts cold starts. It does not demonstrate high throughput or a measured availability target.

**Separate state from the application container.** PostgreSQL data and uploaded media live outside Cloud Run instances. This supports replacing an application image without treating the container filesystem as durable storage. A successful image replacement still says nothing about database rollback or recovery of deleted media.

**Define infrastructure and application responsibilities.** [Terraform](../terraform/main.tf) declares Artifact Registry, a runtime service account, the Cloud Run service and its public invocation policy. The backend workflow builds a commit-tagged image and updates the service image. Terraform ignores changes to that image field.

The September review interprets this arrangement as a useful division of responsibility: infrastructure configuration can evolve separately from routine application releases. The code demonstrates the division; there is no contemporaneous decision record establishing every original reason for it.

**Keep the IaC boundary explicit.** Neon, media storage, CI authentication and backend preparation remain outside the Terraform resource definitions. Formatting and validation passed, and the configured GCS backend returned the four declared resource addresses. Reading state does not establish absence of drift, successful restoration, or a complete environment rebuild.

**Accept multiple providers deliberately.** Pages, Cloud Run, Neon and GCS address different hosting responsibilities. The resulting system also crosses service boundaries, with separate configuration, access control, billing and troubleshooting. Cost is an operating constraint; this repository does not guarantee a zero bill.

## Delivery and verification

The [backend workflow](../.github/workflows/deploy-backend.yml) runs tests, builds an image, scans it with Trivy, and updates Cloud Run. Trivy blocks fixable HIGH and CRITICAL findings. Backend lint steps and CodeQL analysis have different failure policies, so “all security checks must pass” would overstate the configuration.

The [frontend workflow](../.github/workflows/deploy-frontend.yml) performs lint, tests and a production build before publishing to Pages. Its API endpoint is supplied at build time, allowing frontend source to remain separate from the deployed backend address.

September follow-up adds a [Gitleaks workflow](../.github/workflows/secret-scan.yml), an [API smoke check](../scripts/smoke-check.py) and [six offline tests](../scripts/smoke_check_test.py). Both workflows now have successful GitHub execution records.

The gate also stopped a release: [run 36298822546](https://github.com/jothep/maori-story-fill/actions/runs/36298822546) found 12 fixable HIGH findings—ten in Pillow and two in pip-bundled packages. Commit **7d80196** upgraded Pillow from 12.2 to 12.3 and removed pip, ensurepip and bundled wheels from the runtime after dependency checks, retaining builder tooling. The scan policy was unchanged.

The [successful backend run](https://github.com/jothep/maori-story-fill/actions/runs/36299274042) passed 11 backend tests, six offline smoke tests, Trivy, image push, deployment and public API verification. [Secret scanning](https://github.com/jothep/maori-story-fill/actions/runs/36299274040) and the [frontend release](https://github.com/jothep/maori-story-fill/actions/runs/36298824448) also passed. These checks do not exercise sustained load or recovery.

Application deployment workflows currently have no pull-request trigger. Database migration orchestration and automatic rollback are also outside the implemented release path.

## Preparing the repository for publication

The publication audit found credentials in documentation and Git history. The subsequent work separates credential rotation from repository sanitisation: removing a value from Git does not revoke it, and revoking it does not remove historical copies.

A fresh clone of the sanitised legacy history passed scanning, but an old sensitive document remained retrievable by its previous commit ID in that repository. The former repository stays private. Publication therefore moves to `jothep/story-filler`, carrying forward only the cleaned 189-commit baseline and subsequent migration changes. This preserves the development history without claiming removal of every external or server-side copy. The [migration record](repository-migration.md) records the new repository's verification separately.

This is a September 2026 improvement, not a claim that the original project had complete secrets management. Database credentials, the Django signing key and the administrator login remain separate concerns.

## What this case demonstrates

The strongest evidence is the relationship between a workload, a deployment model, and its operational responsibilities. The project shows practical containerisation, infrastructure configuration, automated delivery, state externalisation and careful qualification of what has been verified.

The [second article draft](articles/02-operating-the-migration.md) develops these decisions. Remaining work includes completing the new repository's acceptance checks, a verified first-deployment path, and a rollback exercise with database compatibility made explicit.
