terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "jaskojothep-terraform-state"
    prefix = "terraform/state/maori-story-fill"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Artifact Registry
resource "google_artifact_registry_repository" "maori_story" {
  location      = var.gcp_region
  repository_id = "maori-story-${var.environment}"
  format        = "DOCKER"
}

# Service Account
resource "google_service_account" "cloud_run" {
  account_id   = "maori-story-${var.environment}"
  display_name = "Maori Story Cloud Run"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "backend" {
  name     = "maori-story-backend-${var.environment}"
  location = var.gcp_region

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.maori_story.repository_id}/backend:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = false
      }

      ports {
        container_port = 8000
      }

      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }

      env {
        name  = "SECRET_KEY"
        value = var.django_secret_key
      }

      env {
        name  = "DEBUG"
        value = "False"
      }

      env {
        name  = "ALLOWED_HOSTS"
        value = var.allowed_hosts
      }

      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = var.cors_allowed_origins
      }

      env {
        name  = "USE_S3"
        value = var.use_s3
      }

      dynamic "env" {
        for_each = var.use_s3 == "true" ? [1] : []
        content {
          name  = "AWS_ACCESS_KEY_ID"
          value = var.aws_access_key_id
        }
      }

      dynamic "env" {
        for_each = var.use_s3 == "true" ? [1] : []
        content {
          name  = "AWS_SECRET_ACCESS_KEY"
          value = var.aws_secret_access_key
        }
      }

      dynamic "env" {
        for_each = var.use_s3 == "true" ? [1] : []
        content {
          name  = "AWS_STORAGE_BUCKET_NAME"
          value = var.aws_storage_bucket_name
        }
      }
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }
}

# Public access
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "registry_url" {
  value = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.maori_story.repository_id}"
}

output "service_url" {
  value = google_cloud_run_v2_service.backend.uri
}
