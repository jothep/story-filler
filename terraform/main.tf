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

# Artifact Registry - Docker 镜像仓库
resource "google_artifact_registry_repository" "maori_story" {
  location      = var.gcp_region
  repository_id = "maori-story"
  format        = "DOCKER"
}

# Service Account
resource "google_service_account" "cloud_run" {
  account_id   = "maori-story-backend"
  display_name = "Maori Story Backend"
}

# Cloud Run - 后端服务
resource "google_cloud_run_v2_service" "backend" {
  name     = "maori-story-backend"
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
        name  = "USE_GCS"
        value = "true"
      }

      env {
        name  = "GS_BUCKET_NAME"
        value = "maori-story-media"
      }

      env {
        name  = "CSRF_TRUSTED_ORIGINS"
        value = "http://localhost:8000,http://localhost"
      }

      env {
        name  = "CSRF_TRUSTED_ORIGIN_WILDCARDS"
        value = "https://*.run.app"
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

# 公开访问（前端调用API）
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "registry_url" {
  description = "Docker镜像仓库地址"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.maori_story.repository_id}"
}

output "service_url" {
  description = "后端API地址（配置到前端）"
  value       = google_cloud_run_v2_service.backend.uri
}

output "push_command" {
  description = "推送镜像命令"
  value       = "docker push ${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.maori_story.repository_id}/backend:latest"
}
