# Terraform: scope and bootstrap order

This configuration manages four resource types for the current GCP deployment:

- an Artifact Registry Docker repository;
- a dedicated Cloud Run runtime service account;
- the Cloud Run service, including its runtime environment and 0–1 instance limit;
- public invocation permission for the application.

The [current architecture](../docs/architecture-production-gcp.md) documents the responsibility split: Terraform owns service configuration; GitHub Actions updates the image. `ignore_changes` on the image field prevents an infrastructure apply from reverting that release selection.

## Prerequisites outside this configuration

The GCP project and enabled APIs, a private GCS Terraform-state bucket, authentication for Terraform and CI, the Neon database, the media bucket and its required IAM bindings, and GitHub settings must already exist or be bootstrapped separately. The backend bucket name in `main.tf` is project-specific; another operator must configure their own backend.

This repository is not a single-command recreation of every service. On 27 September 2026, reading the configured GCS backend confirmed all four declared resource addresses in state. This is not a drift assessment or a clean-room recovery exercise; see the verification record.

## Private inputs

Use `terraform.tfvars.example` for non-secret settings. Provide `database_url` and `django_secret_key` through private `TF_VAR_*` environment variables or an ignored, owner-readable local variable file. Do not paste credential values into public examples, shell arguments or version control.

If a local `.tfvars` file already assigns these fields, it takes precedence over the corresponding environment variables. Keep one deliberate source of current values. Rotating the Cloud Run environment without updating Terraform's private inputs can cause a later apply to restore old settings.

Terraform's `sensitive` marking hides selected display output; it does not remove values from state. Protect the state bucket and do not publish state or saved plans.

## First deployment order

1. Establish the prerequisites and authenticate. Terraform typically uses Application Default Credentials; a Cloud SDK login alone should not be assumed to configure every tool.
2. Run `terraform init` against the intended private backend. Inspect the project and region before planning changes.
3. For a completely new environment, create the registry before pushing an image. A narrowly targeted apply of `google_artifact_registry_repository.maori_story` can be used for this one-time bootstrap; routine updates should use a full reviewed plan.
4. Build and push the initial backend image to that registry. The Cloud Run resource references `backend:latest`, so that image must exist before the initial service creation.
5. Review a full `terraform plan`, then apply it. Ensure the runtime identity has the media permissions established outside this configuration.
6. Configure GitHub's backend and Pages workflows and run their delivery checks. Later backend releases use commit-SHA image tags.

Do not import, recreate or apply against the existing project merely to demonstrate these commands. Inspect the existing state and ownership first.

## Verification and cost boundaries

See the [verification record](../docs/verification.md) for observed deployments. The configuration limits Cloud Run to one instance and allows scale-to-zero, but this is a cost-control choice, not a promise of a zero bill or high availability. Registry, storage, database and network usage remain relevant.
