# Architecture overview

This repository records the evolution of a story application from local containers and Kubernetes to a managed cloud deployment.
It is an infrastructure practice case that complements the author's enterprise experience.
The repository preserves both stages; they are not two independently verified current production environments.

## Current deployment

The current deployment uses GitHub Pages for the React frontend, Cloud Run for the Django API, Neon PostgreSQL for application data, and GCS for media.
The browser fetches static assets from Pages, calls the API directly, and reads public media directly from GCS URLs returned by the API.

Read [Current deployment architecture](architecture-production-gcp.md) for configuration, ownership boundaries, delivery checks and verification status.
The [diagram index](architecture-diagrams.md) provides separate current and historical views.

Key implemented decisions:

- Keep database and media state outside the application container.
- Limit Cloud Run to 0–1 instances, with 1 vCPU and 512 MiB, for a low-traffic cost constraint.
- Use Terraform for the registry, runtime service account, service configuration and public invocation binding; the GCS state inventory confirms these four resources.
- Let the application pipeline select the SHA-tagged image while Terraform ignores image changes.
- Run application tests and image scanning before deployment, with advisory lint checks explicitly distinguished from required gates.

These choices accept cold starts, a capacity limit and external service dependencies.
They do not establish zero cost, high availability or a measured throughput level.

## Local development and container environments

The [local platform lab](local-platform-lab.md) explains the implementation before managed hosting:

- `demo/` preserves the earlier Django/React prototype, with a Compose-managed database and host-run application processes.
- Development Compose combines NGINX, Vite, Django and PostgreSQL, with source mounts, HMR, startup checks and persistent volumes.
- Production-style Compose separates Gunicorn, built frontend assets, proxying and persistent content; it is not the current production deployment.
- Kubernetes expresses the same application and state boundaries through Services, Deployments, StatefulSet, PVCs and operational Jobs.

These files demonstrate environment and lifecycle design. Full container startup was not repeated because the Docker daemon was unavailable during review.

## Earlier Kubernetes implementation

The [Infra directory](../Infra/) contains the earlier deployment manifests:

| Concern | Checked-in implementation |
| --- | --- |
| Application workloads | Single-replica frontend and backend Deployments with ClusterIP Services |
| Request routing | NGINX Ingress rules for frontend, API, admin, static and media paths |
| Database | Single-replica PostgreSQL StatefulSet with persistent storage and health probes |
| Uploaded media | PersistentVolumeClaim mounted into the backend |
| Database changes | A separate Django migration Job |
| Administration | A separate Job that obtains administrator inputs through Secret references |
| Troubleshooting | Network and PostgreSQL client Pods |

A separate PostgreSQL Helm values file is also retained; it is not evidence that both database definitions should be deployed together.
The application manifests reference Kubernetes Secrets without committing their values.
Secret references alone do not prove encryption at rest or a complete secret-management process.

The author's [original article](https://medium.com/@shelldry325/from-on-premises-kubernetes-to-zero-cost-serverless-architecture-a-practical-guide-to-cloud-70e68304e835) reports running the earlier environment.
The manifests provide implementation evidence; this review did not redeploy that cluster.
There are no checked-in ArgoCD Application/AppProject definitions, application autoscalers or Ingress TLS configuration.
PostgreSQL has readiness/liveness probes and resource settings; the frontend and backend manifests do not.
Describe this stage as a historical Kubernetes implementation, not a verified high-availability or complete GitOps platform.

## Verification boundaries

Public frontend, API read endpoints and a sampled GCS object were reachable on 2026-09-27.
Cloud Run revision `maori-story-backend-00026-phc` changed credential configuration while keeping the existing image.
That check does not verify deployment of the current repository cleanup changes.
Historical Actions runs provide release evidence for the source versions recorded in those runs.
The new API smoke check passed six offline tests and a local production check; its GitHub deployment-step execution is pending.
A separate history-scanning workflow is implemented but is not a dependency of the deployment workflow.
See [the verification record](verification.md) for the status of each check.

Terraform formatting and validation passed, and the configured GCS remote state listed the four declared resources.
That inventory does not establish absence of drift. Complete environment rebuilds, load limits, backup restoration and application rollback still require explicit exercises.
Precise performance, availability and cost claims need reproducible measurements or dated billing evidence.
Provider plan features are not evidence that those features have been enabled or tested for this project.

## Reading the rest of the repository

Use the current deployment page above as the architecture reference.
Older root-level deployment guides and design drafts retain historical context and may describe alternative stages or planned work.
Treat their commands as material to review, not a verified end-to-end bootstrap procedure.
The implementation and dated verification records take precedence over unsupported claims in those older documents.
