# Architecture diagrams

These diagrams distinguish the current managed deployment from the earlier Kubernetes implementation.
For configuration and evidence limits, read [Current deployment architecture](architecture-production-gcp.md).
For the project stages, read [Architecture overview](ARCHITECTURE.md).
For Compose, local Kubernetes and the prototype, read [Local platform lab](local-platform-lab.md).

## Current managed deployment

```mermaid
flowchart LR
    Pages[GitHub Pages] -->|Static application assets| Browser[Browser]
    Browser -->|API requests| Run[Cloud Run<br/>Django API<br/>0–1 instance, 1 vCPU, 512 MiB]
    Run -->|Queries| Neon[(Neon PostgreSQL)]
    Run -->|JSON with media URLs| Browser
    Browser -->|Direct public media reads| Media[(GCS media)]
    Run -.->|Media storage client| Media
```

The browser is the client of Pages, the API and public media storage.
Pages does not proxy API requests, and ordinary media reads do not traverse Cloud Run.
The dotted storage connection represents the implemented backend integration; the latest online checks did not exercise uploads.
Secret Manager and Workload Identity Federation are not configured. Delivery retains the existing service-account JSON key authentication through the `GCP_CREDENTIALS` GitHub Actions secret; the owner configures that secret manually in the new repository.

## Delivery and ownership

```mermaid
flowchart LR
    Code[Application change on main] --> Checks[Tests and build]
    Key[GitHub Actions secret: GCP_CREDENTIALS] --> Auth[Service-account JSON key authentication]
    Auth -.-> Registry
    Auth -.-> Run
    Checks --> Scan[Image vulnerability gate]
    Scan --> Registry[Artifact Registry<br/>SHA and latest tags]
    Registry -->|Deploy SHA tag| Run[Cloud Run]
    Run --> Smoke[Public API smoke check]
    Git[Main push or pull request] --> SecretsScan[Independent Git-history credential scan]
    TF[Terraform] -->|Service configuration and public invocation| Run
    TF -->|Creates| Registry
    TF -->|Creates| Identity[Runtime service account]
    Identity -->|Runtime identity| Run
    TF -.->|GCS state backend| State[(Private Terraform state)]
```

This backend delivery path passed in the new repository's [run 36363802780, attempt 2](https://github.com/jothep/story-filler/actions/runs/36363802780/attempts/2), using `GCP_CREDENTIALS`. At the 28 September check, Cloud Run revision `maori-story-backend-00028-gdm` served image `1713b97` with 100% traffic; environment entries and runtime identity were preserved. The [verification summary](evidence/backend-migration-verification.json) records the runtime comparison and clean scoped log review. The frontend separately runs lint, tests and build before Pages deployment. The new repository's [Pages run for `1713b97`](https://github.com/jothep/story-filler/actions/runs/36363233923) passed on 28 September, followed by a Chrome menu-to-story text/image check at `/story-filler/`. New scan evidence is recorded in the [migration record](repository-migration.md).
Terraform creates the registry and runtime identity as well as the service configuration, but the application workflow owns image updates.
The GCS state inventory was checked and contains the four declared resources; Terraform formatting and validation passed.
No Terraform plan, apply or restore was performed in this verification; the inventory is not a drift or rebuild check. State may contain sensitive values and is not a public portfolio artifact.
Pre-migration evidence from the former private repository: the [backend delivery run for `7d80196`](https://github.com/jothep/maori-story-fill/actions/runs/36299274042) passed application tests, six offline smoke-check tests, image scanning, deployment and the public API smoke check.
At the 27 September check, Cloud Run revision `maori-story-backend-00027-bzj` served that commit-tagged image with 100% traffic. The new repository retains the same authentication method, but this old run does not verify its secret setup or delivery; see the [migration record](repository-migration.md).
The frontend Pages run for `a309a63` and independent credential scans for both release commits also succeeded; links are in the verification record.
A smoke-check failure does not undo deployment. The credential scan runs independently and does not gate the deployment job.
See the current deployment page and [verification record](verification.md) for exact gates and execution status.

## Historical Kubernetes implementation

```mermaid
flowchart LR
    Browser[Browser] --> Ingress[NGINX Ingress<br/>path routing]
    Ingress --> Front[Frontend Service<br/>and Deployment]
    Ingress --> Back[Backend Service<br/>and Deployment]
    Back --> DB[(PostgreSQL Service<br/>and StatefulSet)]
    Back --> Media[(Media PVC)]
    DB --> Data[(Database PVC)]
    Migrate[Migration Job] --> DB
    Admin[Create administrator Job] --> DB
    Secrets[Kubernetes Secret references] -.-> Back
    Secrets -.-> DB
    Secrets -.-> Migrate
    Secrets -.-> Admin
```

This view is grounded in the [checked-in manifests](../Infra/).
Frontend, backend and PostgreSQL each use one replica.
It does not imply load-tested availability, Ingress TLS, autoscaling or a checked-in ArgoCD delivery configuration.
The original article reports a working earlier environment; this review did not recreate it.

The [original Kubernetes illustration](Original%20Kubernetes%20Structure-2026-04-30-232315.png) is preserved as a historical design artifact.
Its TLS/SSL-offloading and frontend/backend health-probe annotations are not supported by the checked-in manifests.
Use the corrected Mermaid view and the qualifications above as the implementation reference; the original image records earlier design intent.
