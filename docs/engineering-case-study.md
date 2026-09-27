# Māori Story Filler: Infrastructure and Delivery Case Study

This personal project complements my years of enterprise work with recent, inspectable infrastructure practice. It is a small story-based learning application with a React frontend, a Django API and administration interface, PostgreSQL data, and uploaded media.

The engineering case concerns how those components are deployed, where their state lives, and how changes reach a running service. The [first article](https://medium.com/@shelldry325/from-on-premises-kubernetes-to-zero-cost-serverless-architecture-a-practical-guide-to-cloud-70e68304e835) describes the migration. This case study connects that account to the current implementation and its limits.

## Evidence and scope

This document reflects a September 2026 review. The [verification record](verification.md) distinguishes implementation, observed deployment behaviour, and pending work. Local changes must not be assumed to be running in production.

On 27 September 2026, the live service was checked after a configuration rotation. Cloud Run revision **00026-phc** retained the existing application image. That check provides evidence about the updated configuration and the existing deployed application; it does not establish that the subsequent repository changes have run through GitHub Actions.

The project is a single application and a personal infrastructure exercise. Its Kubernetes manifests demonstrate an earlier deployment implementation. This review did not recreate that cluster, establish a service availability history, or conduct a disaster recovery exercise.

## Architecture evolution

Local environments are part of the case. [Development Compose](../docker-compose.dev.yml) binds source into Django and Vite containers for iteration, connects services through a bridge network, and separates database/media data into named volumes. [Nginx](../nginx.dev.conf) provides frontend, API, admin and media routes; relative API requests are the intended single-origin path. This makes routing and persistence inspectable locally.

The [Kubernetes implementation](../Infra/) develops those concerns into Deployments and Services, PostgreSQL StatefulSet storage, a media PVC, migration and administrator Jobs, and network/database troubleshooting Pods. The separate Jobs distinguish finite administration tasks from serving application traffic. Resource settings and probes exist for PostgreSQL; application probes, Ingress TLS and autoscaling are not implemented in these manifests.

The [demo](../demo/) is a separate, smaller application: Django serves stories with full_text and directly associated words, while its MUI frontend reads that content from list responses at a fixed local API address. The main application instead has separate list/detail contracts and paragraph, blank-link and media structures. Demo Compose starts only PostgreSQL. Its contract should not be substituted for the production API.

The [local platform lab](local-platform-lab.md) connects these implementations and their gaps. This review has not rerun demo, recreated Kubernetes, or completed a fresh Compose startup.

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

**Keep the IaC boundary explicit.** Terraform does not provision the complete environment. Neon, media storage configuration, CI authentication, and initial state-backend preparation include dependencies outside its current resource definitions. A GCS backend is configured for Terraform state, but that is not evidence of a tested, complete environment rebuild.

**Accept multiple providers deliberately.** Pages, Cloud Run, Neon and GCS address different hosting responsibilities. The resulting system also crosses service boundaries, with separate configuration, access control, billing and troubleshooting. Cost is an operating constraint; this repository does not guarantee a zero bill.

## Delivery and verification

The [backend workflow](../.github/workflows/deploy-backend.yml) runs tests, builds an image, scans it with Trivy, and updates Cloud Run. Trivy blocks fixable HIGH and CRITICAL findings. Backend lint steps and CodeQL analysis have different failure policies, so “all security checks must pass” would overstate the configuration.

The [frontend workflow](../.github/workflows/deploy-frontend.yml) performs lint, tests and a production build before publishing to Pages. Its API endpoint is supplied at build time, allowing frontend source to remain separate from the deployed backend address.

September 2026 follow-up work adds a dedicated [Gitleaks workflow](../.github/workflows/secret-scan.yml) and a [deployment smoke-check script](../scripts/smoke-check.py), supported by [six offline tests](../scripts/smoke_check_test.py). All six tests passed locally. A read-only production run also passed, checking a response containing one story, eight paragraphs and eleven words. GitHub Actions execution of both the secret-scanning workflow and the updated deployment workflow remains unverified. These checks do not exercise administrator workflows, uploads, sustained load, or data recovery.

Application deployment workflows currently have no pull-request trigger. Database migration orchestration and automatic rollback are also outside the implemented release path.

## Preparing the repository for publication

The publication audit found credentials in documentation and Git history. The subsequent work separates credential rotation from repository sanitisation: removing a value from Git does not revoke it, and revoking it does not remove historical copies.

Current examples now use private inputs or generated local configuration. Sensitive local material is excluded from version control, and a sanitised history is being prepared for a controlled remote update. The verification record is the authority for completed checks and remaining publication steps.

This is a September 2026 improvement, not a claim that the original project had complete secrets management. Database credentials, the Django signing key and the administrator login remain separate concerns.

## What this case demonstrates

The strongest evidence is the relationship between a workload, a deployment model, and its operational responsibilities. The project shows practical containerisation, infrastructure configuration, automated delivery, state externalisation and careful qualification of what has been verified.

The [second article draft](articles/02-operating-the-migration.md) develops those operating decisions. Remaining improvements should produce useful evidence: a verified first-deployment path, a successful pipeline run with the new checks, and a bounded rollback exercise with database compatibility made explicit.
