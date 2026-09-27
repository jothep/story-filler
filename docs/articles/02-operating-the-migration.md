# After the Migration: Operating a Small Cloud Run Application

*Draft for review. September 2026 follow-up to [From On-premises Kubernetes to Zero-Cost Serverless Architecture](https://medium.com/@shelldry325/from-on-premises-kubernetes-to-zero-cost-serverless-architecture-a-practical-guide-to-cloud-70e68304e835). This article has not been published.*

My first article described moving Māori Story Filler from a local container and Kubernetes setup to managed hosting. It ended by introducing the next subject: the delivery pipeline and security practices supporting that architecture.

This follow-up examines what that promise means in the repository. There is a running application, infrastructure code and automated deployment. There are also manual dependencies, limited verification and improvements made during a September 2026 review.

The project complements my years of enterprise work by making recent hands-on practice visible. The useful story is how the responsibilities fit together, including the points where evidence is still missing.

## The local lab remains part of the case

The local implementations expose infrastructure concerns directly. [Development Compose](../../docker-compose.dev.yml) uses source mounts for Django and Vite iteration, a bridge network for service communication, and named database/media volumes. [Nginx](../../nginx.dev.conf) routes API, administration and media paths separately from the frontend. Relative API URLs support a single browser origin; the integration details and remaining gaps are documented in the [local platform lab](../local-platform-lab.md).

[Kubernetes](../../Infra/) makes workload lifecycle and state explicit: Deployments and Services for the application, a PostgreSQL StatefulSet and persistent volumes, and separate migration and administrator Jobs. Network and PostgreSQL client Pods provide troubleshooting entry points. These are concrete configuration exercises; the application manifests still lack probes and Ingress TLS, and the cluster has not been recreated in this review.

The [demo directory](../../demo/) contains a smaller Django/MUI implementation with a distinct API contract. Its frontend displays full_text from story list results at a fixed local address; the main application uses separate list/detail responses with paragraphs and media. Demo Compose runs PostgreSQL only. The code supports comparison of these implementations without assuming that the demo is interchangeable with the deployed application. Neither demo execution nor a fresh Compose startup has been verified here.

Local control and visibility serve development and infrastructure practice; managed hosting addresses the operating cost of the public deployment.

## What changed after the architecture changed

The current arrangement gives each component a different home: GitHub Pages serves the React frontend, Cloud Run runs the Django container, Neon holds the PostgreSQL database, and Google Cloud Storage holds uploaded media. GCS superseded the S3-compatible implementation discussed in the first article.

The operational responsibilities changed with those choices. The application no longer requires me to operate a Kubernetes cluster for its current deployment. I still have to manage application dependencies, configuration, credentials, database changes and the relationship between a release and stored data.

The original article records the migration rationale. The interpretation of responsibility boundaries below comes from reviewing the implementation in September 2026. It should be read as a retrospective assessment where there is no earlier decision record.

## Terraform and the application pipeline have different jobs

[Terraform](../../terraform/main.tf) describes a limited set of Google Cloud resources: an Artifact Registry repository, a runtime service account, a Cloud Run service and permission for public invocation. It also supplies application configuration to the service.

The [backend workflow](../../.github/workflows/deploy-backend.yml) tests the application, builds a container image, scans it, and updates Cloud Run using an image tagged with the source commit. Terraform ignores changes to the service's image field.

That arrangement creates a practical handover. Terraform owns the declared infrastructure configuration; the application workflow owns routine image updates. A Terraform change need not choose the image for each release.

There are limits to this separation. Terraform still manages environment variables. A later apply with stale secret inputs can reintroduce an old configuration even when the image pipeline preserves the current values. In the present workflow, the Cloud Run update passes the image and region; it does not replace the service's environment.

There is also a bootstrap boundary. The current Terraform configuration does not create Neon, all media-storage configuration or CI authentication. Its GCS state backend needs preparation before it can be used. A complete environment rebuild remains a separate verification task.

For a portfolio, naming these dependencies is useful evidence of infrastructure understanding. “There is Terraform code” and “the whole environment has been rebuilt from that code” are different claims.

## State remains an application responsibility

The application container is replaceable because the database and uploaded media are external to its filesystem. That makes Cloud Run a workable runtime for this application.

External storage introduces its own operating questions. A database migration must remain compatible with the application version receiving traffic. Uploaded files need an access policy and a recovery approach. Separate services mean separate permissions, failure conditions and costs.

These boundaries matter during rollback. Pointing Cloud Run at an earlier image can reverse an application deployment. It cannot automatically undo a schema migration, restore deleted data or recover a removed object. No completed disaster recovery exercise is claimed for this project.

The current configuration also allows **zero to one Cloud Run instance**. Scaling to zero supports the low-traffic cost objective, while accepting cold starts. Limiting the service to one instance constrains capacity. Neither the configured concurrency nor the platform's general scaling capability establishes an application throughput result.

The same qualification applies to cost. The design seeks low fixed operating costs and uses available allowances. Actual charges depend on usage, storage, network traffic and provider terms. The repository does not establish a permanent zero-cost guarantee.

## A release needs evidence beyond an image build

Existing frontend delivery runs lint, tests and a build before publishing to GitHub Pages. The backend workflow runs application tests and builds and scans its container before updating Cloud Run.

The checks have different meanings. Trivy blocks fixable HIGH and CRITICAL findings; that policy does not establish the absence of every known vulnerability. Backend lint and CodeQL analysis are configured to allow failure. The application deployment workflows do not currently run on pull requests.

These details belong in an accurate description of the pipeline. Counting tools would obscure which failures actually prevent a release.

The September follow-up adds two focused improvements: a dedicated [Gitleaks workflow](../../.github/workflows/secret-scan.yml) and a [deployment smoke-check script](../../scripts/smoke-check.py), with [six offline tests](../../scripts/smoke_check_test.py). All six tests passed locally. A read-only run against the production URL also passed, checking a response containing one story, eight paragraphs and eleven words. Those counts describe the data observed during the check, not a capacity result. GitHub Actions execution of the new secret-scanning workflow and the updated deployment workflow remains pending verification. The smoke check does not validate uploads, administrator tasks, prolonged traffic or recovery.

A live verification on **27 September 2026** checked the service following configuration rotation. The active Cloud Run revision, **00026-phc**, reused the existing application image. It is evidence for that deployment configuration and the observed API behaviour. It is not evidence that the newly added repository checks have completed a production release.

The [verification record](../verification.md) keeps these categories separate and records their limits.

## Publication made credential handling concrete

Preparing a formerly private repository for public review exposed a practical security issue: credentials had been written into documentation and retained in Git history.

The response has two independent parts. Credential rotation changes what the running services accept. Repository sanitisation removes sensitive material from the content intended for publication. Either action alone leaves part of the problem unresolved.

This work includes replacing fixed credential examples with private input or generated local configuration, excluding sensitive working files, and preparing a sanitised history for a controlled remote update. Public release depends on completing the recorded checks, including verification of the remote repository after that update.

It is important to preserve the timing. These are September 2026 improvements prompted by the publication review. Presenting them as controls that had always existed would hide the reason the work was necessary.

The review also distinguishes three kinds of credential: the database connection, the Django signing key and the administrator's login password. Each has different consumers and a different recovery procedure. A signing-key change can invalidate sessions while leaving the stored administrator password unchanged.

Adding a scanner helps catch future mistakes. It cannot prove that no sensitive value exists anywhere, replace rotation, or remove copies already stored outside the repository.

## What I would verify next

The next useful work is small enough to produce inspectable results.

First, document and exercise the initial deployment sequence, including resources and credentials outside Terraform's scope. Second, run the new checks through GitHub Actions and retain the resulting execution records. Third, rehearse an application rollback while stating explicitly whether database changes are involved.

Those tasks would strengthen the evidence for reproducibility and release recovery. They do not require turning a small personal application into a multi-region platform.

The [case study](../engineering-case-study.md), [current architecture](../architecture-production-gcp.md) and verification record provide the repository-level view behind these articles. Together, they let a reader follow an engineering decision from its context to its implementation, then see exactly what has been tested and what remains to be demonstrated.
