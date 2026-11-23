# Historical records

This folder keeps earlier guides, plans and scripts from the project's local, AWS, Oracle Cloud and first Google Cloud stages. They are records of how the project developed, not current instructions. Most are written in Chinese.

The files were moved from the repository root, `scripts/` and `terraform/` in November 2026; Git history keeps the earlier copies. Their content is unchanged apart from:

- relative links, updated so they resolve from this folder;
- the administrator username in `ADMIN_GUIDE.md`, replaced with a placeholder;
- a link to a guide that was later deleted, turned into plain text in `MIGRATION_GUIDE.md`.

The scripts are not maintained. Do not run them.

For current information, start with the [README](../../README.md), [architecture overview](../ARCHITECTURE.md), [current deployment](../architecture-production-gcp.md), [local platform lab](../local-platform-lab.md), [backup and recovery guide](../../VOLUME_BACKUP_GUIDE.md) and [operations pages](../operations/).

## Guides and notes

| File | Original location | What it covered | Current source |
| --- | --- | --- | --- |
| [ADMIN_GUIDE.md](ADMIN_GUIDE.md) | Root | Django admin content entry for an earlier data model | [Adding and editing stories](../operations/content-admin.md) |
| [ADMIN_PASSWORD_GUIDE.md](ADMIN_PASSWORD_GUIDE.md) | Root | Ways to change or reset the administrator password | [Administrator accounts](../operations/admin-account.md) |
| [CREATE_ADMIN.md](CREATE_ADMIN.md) | Root | Creating or resetting an administrator | [Administrator accounts](../operations/admin-account.md) |
| [CHANGELOG-2026-04-30.md](CHANGELOG-2026-04-30.md) | Root | Change notes for 30 April 2026: single-line menu logo, layout tidy-up, removal of unused assets | [CHANGELOG](../../CHANGELOG.md) for later changes |
| [CLOUD_RUN_ENV_VARS.md](CLOUD_RUN_ENV_VARS.md) | Root | Updating runtime variables with `gcloud run services update` | Terraform now manages runtime configuration; see [current deployment](../architecture-production-gcp.md). Changing it with `gcloud` would drift from Terraform |
| [CLOUD_RUN_URL_STABILITY.md](CLOUD_RUN_URL_STABILITY.md) | Root | Cloud Run URL formats | [Current deployment](../architecture-production-gcp.md) |
| [DEPLOYMENT_URLS.md](DEPLOYMENT_URLS.md) | Root | Service URLs at the time | [README](../../README.md) |
| [PUBLIC_ACCESS_GUIDE.md](PUBLIC_ACCESS_GUIDE.md) | Root | Why the backend is publicly reachable, and a 403 investigation | [Current deployment](../architecture-production-gcp.md) |
| [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) | Root | Django migrations and the first Neon setup | [Production database migrations](../operations/database-migrations.md) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Root | Step-by-step deployment to Cloud Run and GitHub Pages | [Current deployment](../architecture-production-gcp.md) |
| [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) | Root | Short version of the deployment steps | [Current deployment](../architecture-production-gcp.md) |
| [WORKFLOW.md](WORKFLOW.md) | Root | Early workflow notes from the first Neon setup | [Architecture overview](../ARCHITECTURE.md) |
| [CODE_ANALYSIS.md](CODE_ANALYSIS.md) | Root | Early code analysis report | [Verification record](../verification.md) |
| [COST_COMPARISON.md](COST_COMPARISON.md) | Root | Hosting cost comparison across the options considered | [Architecture overview](../ARCHITECTURE.md) |
| [ORACLE_CLOUD_SETUP.md](ORACLE_CLOUD_SETUP.md) | Root | Oracle Cloud free-tier deployment guide from the platform evaluation | [Architecture overview](../ARCHITECTURE.md) |
| [REFACTORING_PLAN.md](REFACTORING_PLAN.md) | Root | AWS-oriented refactoring and migration plan | [Architecture overview](../ARCHITECTURE.md) |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Root | Data migration for the EC2 and S3 stage | [Backup and recovery guide](../../VOLUME_BACKUP_GUIDE.md) |
| [TERRAFORM_GUIDE.md](TERRAFORM_GUIDE.md) | Root | Terraform for the AWS EC2 stage | [Terraform README](../../terraform/README.md) (Google Cloud) |
| [terraform/CLOUD_RUN_DEPLOY_GUIDE.md](terraform/CLOUD_RUN_DEPLOY_GUIDE.md) | `terraform/` | Earlier Cloud Run deployment guide | [Terraform README](../../terraform/README.md) |
| [terraform/GCS_BACKEND_SETUP.md](terraform/GCS_BACKEND_SETUP.md) | `terraform/` | Setting up the Terraform state bucket | [Terraform README](../../terraform/README.md) |
| [course-requirements.txt](course-requirements.txt) | Root, as `Requirements.txt` | The original course requirements list, reproduced as written. Not a pip file | None |

## Scripts

| File | Original location | What it did | Current source |
| --- | --- | --- | --- |
| [deploy.sh](deploy.sh) | Root | Deployment to Oracle Cloud or another server | [Current deployment](../architecture-production-gcp.md) |
| [scripts/start-instance.sh](scripts/start-instance.sh), [scripts/stop-instance.sh](scripts/stop-instance.sh), [scripts/instance-status.sh](scripts/instance-status.sh) | `scripts/` | Starting, stopping and checking the EC2 instance | None; the EC2 stage has ended |
| [scripts/export-data.sh](scripts/export-data.sh), [scripts/import-data.sh](scripts/import-data.sh) | `scripts/` | Exporting and importing Docker database and media data | [Backup and recovery guide](../../VOLUME_BACKUP_GUIDE.md) (`scripts/local_recovery.py`) |

The retired backup and restore entry points (`backup.sh`, `scripts/backup-volumes.sh`, `scripts/restore-volumes.sh`, `scripts/restore-volumes-ec2.sh`) stay in place: they refuse to run and point to the current recovery tool, and [`scripts/restore_safety_test.py`](../../scripts/restore_safety_test.py) checks that behaviour.
