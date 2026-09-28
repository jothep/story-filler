# After the Migration: Operating a Small Cloud Run Application

*Draft for review. September 2026 follow-up to [From On-premises Kubernetes to Zero-Cost Serverless Architecture](https://medium.com/@shelldry325/from-on-premises-kubernetes-to-zero-cost-serverless-architecture-a-practical-guide-to-cloud-70e68304e835). This article has not been published.*

My first article described moving the Māori vocabulary application, now published as Story Filler, from a local container and Kubernetes setup to managed hosting. It ended by introducing the next subject: the delivery pipeline and security practices supporting that architecture.

This follow-up connects the running application and infrastructure code to September 2026 improvements, successful releases and remaining manual dependencies. Unless explicitly marked as new-repository evidence, release links below refer to the former private repository, `jothep/maori-story-fill`; they may require access and do not establish a run in the new repository. A [public aggregate snapshot](../evidence/README.md) preserves the scope of the retained delivery history.

The project complements my years of enterprise work with recent, inspectable infrastructure practice.

## The local lab remains part of the case

The local implementations expose infrastructure concerns directly. [Development Compose](../../docker-compose.dev.yml) uses source mounts for Django and Vite iteration, a bridge network for service communication, and named database/media volumes. [Nginx](../../nginx.dev.conf) routes API, administration and media paths separately from the frontend. Relative API URLs support a single browser origin. September fixes addressed same-origin routing and repository-prefix handling; Compose parsing passed. Details and remaining gaps are documented in the [local platform lab](../local-platform-lab.md).

[Kubernetes](../../Infra/) makes workload lifecycle and state explicit: Deployments and Services for the application, a PostgreSQL StatefulSet and persistent volumes, and separate migration and administrator Jobs. Network and PostgreSQL client Pods provide troubleshooting entry points. These are concrete configuration exercises; the application manifests still lack probes and Ingress TLS, and the cluster has not been recreated in this review.

The [demo directory](../../demo/) contains a smaller Django/MUI implementation with a distinct API contract. Its frontend displays full_text from story list results at a fixed local address; the main application uses separate list/detail responses with paragraphs and media. Demo Compose runs PostgreSQL only. Demo execution and a fresh Compose startup remain unverified.

Local control and visibility serve development and infrastructure practice; managed hosting addresses the operating cost of the public deployment.

## What changed after the architecture changed

The current arrangement gives each component a different home: GitHub Pages serves the React frontend, Cloud Run runs the Django container, Neon holds the PostgreSQL database, and Google Cloud Storage holds uploaded media. GCS superseded the S3-compatible implementation discussed in the first article.

Managed hosting takes over cluster operation. Dependencies, credentials, database changes and compatibility between releases and stored data remain project responsibilities.

The first article records the migration rationale; the responsibility analysis below is a September 2026 retrospective where no earlier decision record exists.

## Terraform and the application pipeline have different jobs

[Terraform](../../terraform/main.tf) describes a limited set of Google Cloud resources: an Artifact Registry repository, a runtime service account, a Cloud Run service and permission for public invocation. It also supplies application configuration to the service.

The [backend workflow](../../.github/workflows/deploy-backend.yml) tests the application, builds a container image, scans it, and updates Cloud Run using an image tagged with the source commit. Terraform ignores changes to the service's image field.

That arrangement creates a practical handover. Terraform owns the declared infrastructure configuration; the application workflow owns routine image updates. A Terraform change need not choose the image for each release.

There are limits to this separation. Terraform still manages environment variables. A later apply with stale secret inputs can reintroduce an old configuration even when the image pipeline preserves the current values. In the present workflow, the Cloud Run update passes the image and region; it does not replace the service's environment.

There is also a bootstrap boundary. Terraform does not create Neon, all media-storage configuration or CI authentication. Formatting and validation passed, and its configured GCS backend returned four declared resource addresses. That verifies state access, not absence of drift, restoration, or an environment rebuild.

## State remains an application responsibility

The application container is replaceable because the database and uploaded media are external to its filesystem. That makes Cloud Run a workable runtime for this application.

External storage introduces its own operating questions. A database migration must remain compatible with the application version receiving traffic. Uploaded files need an access policy and a recovery approach. Separate services mean separate permissions, failure conditions and costs.

These boundaries matter during rollback. Pointing Cloud Run at an earlier image can reverse an application deployment. It cannot automatically undo a schema migration, restore deleted data or recover a removed object. No completed disaster recovery exercise is claimed for this project.

The current configuration also allows **zero to one Cloud Run instance**. Scaling to zero supports the low-traffic cost objective, while accepting cold starts. Limiting the service to one instance constrains capacity. Neither the configured concurrency nor the platform's general scaling capability establishes an application throughput result.

The same qualification applies to cost. The design seeks low fixed operating costs and uses available allowances. Actual charges depend on usage, storage, network traffic and provider terms. The repository does not establish a permanent zero-cost guarantee.

## A release needs evidence beyond an image build

Existing frontend delivery runs lint, tests and a build before publishing to GitHub Pages. The backend workflow runs application tests and builds and scans its container before updating Cloud Run.

The checks have different meanings. Trivy blocks fixable HIGH and CRITICAL findings; that policy does not establish the absence of every known vulnerability. Backend lint and CodeQL analysis are configured to allow failure. The application deployment workflows do not currently run on pull requests.

September work added a [Gitleaks workflow](../../.github/workflows/secret-scan.yml) and an [API smoke-check script](../../scripts/smoke-check.py), with [six offline tests](../../scripts/smoke_check_test.py). Their GitHub executions are now verified.

The first backend attempt on **a309a63** [stopped at Trivy](https://github.com/jothep/maori-story-fill/actions/runs/36298822546): 12 fixable HIGH findings, ten in Pillow and two in pip-bundled msgpack and setuptools. The [frontend release](https://github.com/jothep/maori-story-fill/actions/runs/36298824448) and [secret scan](https://github.com/jothep/maori-story-fill/actions/runs/36298820622) passed independently.

Commit **7d80196** upgraded Pillow from 12.2 to 12.3. After installing dependencies and running pip check, the image build removes pip, ensurepip and bundled wheels from the runtime; the builder retains its tooling. The Trivy policy was not weakened.

The [next backend run](https://github.com/jothep/maori-story-fill/actions/runs/36299274042) passed 11 backend tests, six offline smoke tests, Trivy, image push, deployment and public API verification. The [new secret scan](https://github.com/jothep/maori-story-fill/actions/runs/36299274040) also passed. This demonstrates a gate blocking a specific release, a bounded fix, and a verified retry. It does not establish zero vulnerabilities or validate uploads, administrator tasks, sustained load or recovery.

At the 27 September pre-migration check, Cloud Run directed **100% of traffic** to revision **00027-bzj**, running image **7d80196**. The earlier **00026-phc** revision remains evidence of configuration rotation using the previous image, not the current application release.

The [verification record](../verification.md) keeps these categories separate and records their limits.

## Publication made credential handling concrete

Preparing the private repository for public review exposed credentials in documentation and Git history.

The response has two independent parts. Credential rotation changes what the running services accept. Repository sanitisation removes sensitive material from the content intended for publication. Either action alone leaves part of the problem unresolved.

A fresh clone of the sanitised history passed scanning, but an old sensitive document remained retrievable by commit ID in the former repository. That repository stays private. The publication path is a new `jothep/story-filler` repository based on the cleaned 189-commit history: 185 preserved historical commits and four preparation commits. The frontend moves to `/story-filler/`; existing cloud resource IDs remain in place. This does not claim that every historical copy has been erased.

The backend keeps its existing service-account JSON key authentication. The owner configured the `GCP_CREDENTIALS` GitHub Actions secret manually in the new repository, and the release authenticated successfully; no credentials were copied into tracked source. Changing to Workload Identity Federation is a possible later improvement, outside this migration. The [migration record](../repository-migration.md) keeps new-repository execution evidence separate from the successful runs described above.

These are September 2026 improvements prompted by publication review, rather than controls that had always existed.

The review also distinguishes three kinds of credential: the database connection, the Django signing key and the administrator's login password. Each has different consumers and a different recovery procedure. A signing-key change can invalidate sessions while leaving the stored administrator password unchanged.

Adding a scanner helps catch future mistakes. It cannot prove that no sensitive value exists anywhere, replace rotation, or remove copies already stored outside the repository.

## What I would verify next

The new repository's [Pages release for `1713b97`](https://github.com/jothep/story-filler/actions/runs/36363233923) completed on 28 September, and Chrome showed the menu followed by story 1 text and an image at `/story-filler/`. The new credential-scan and CodeQL workflows also completed; a fresh clone passed Gitleaks and a search for 20 known values. These checks are recorded with their limits in the migration record.

The new repository's [backend run 36363802780, attempt 2](https://github.com/jothep/story-filler/actions/runs/36363802780/attempts/2) also passed: 11 backend tests, six offline smoke-check tests, JSON-key authentication, image build/scan/push, deployment and public API verification. At the 28 September check, revision **00028-gdm** served image **1713b97** with 100% traffic. All environment entries and the runtime service account were preserved; the runtime specification changed only in image. A scoped log review found no Gitleaks findings or known-value matches, and an independent public API smoke check passed. The [verification summary](../evidence/backend-migration-verification.json) publishes results without credentials or raw logs.

These completed releases apply to source **1713b97**, the 190-commit migration code snapshot. Later documentation commits do not establish another deployment. The owner made the repository public on **28 September 2026**; the former repository remains private. Further engineering work should exercise the initial deployment sequence, including dependencies outside Terraform, and rehearse an application rollback with database compatibility explicitly assessed.

The [case study](../engineering-case-study.md), [current architecture](../architecture-production-gcp.md) and verification record connect these decisions to their implementation, completed checks and remaining work.
