# ============================================
# Maori Story Fill - GCP Infrastructure
# ============================================
# Terraform 配置：使用 Cloud Run + Artifact Registry 部署后端

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # GCS Backend - 使用 Google Cloud Storage 存储 Terraform 状态
  backend "gcs" {
    bucket = "jaskojothep-terraform-state"
    prefix = "terraform/state/maori-story-fill"
  }
}

# Provider 配置
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ============================================
# Data Sources
# ============================================

# 获取当前 GCP 项目信息
data "google_project" "project" {}

# ============================================
# Artifact Registry - Docker镜像仓库
# ============================================

resource "google_artifact_registry_repository" "maori_story" {
  location      = var.gcp_region
  repository_id = "maori-story-${var.environment}"
  description   = "Docker repository for Maori Story Fill backend"
  format        = "DOCKER"

  labels = {
    project     = "maori-story-fill"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# ============================================
# Cloud Run Service - 后端服务
# ============================================

resource "google_cloud_run_v2_service" "backend" {
  name     = "maori-story-backend-${var.environment}"
  location = var.gcp_region

  template {
    # 扩缩容配置（成本控制）
    scaling {
      min_instance_count = 0  # 无流量时缩减到0
      max_instance_count = 1  # 严格限制为1，防止超额费用
    }

    # 容器配置
    containers {
      # 镜像将手动推送到 Artifact Registry
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.maori_story.repository_id}/backend:latest"

      # 环境变量 - 方案1: 直接注入（测试环境，use_secret_manager=false）
      dynamic "env" {
        for_each = var.use_secret_manager ? [] : [1]
        content {
          name  = "DATABASE_URL"
          value = var.database_url
        }
      }

      dynamic "env" {
        for_each = var.use_secret_manager ? [] : [1]
        content {
          name  = "SECRET_KEY"
          value = var.django_secret_key
        }
      }

      # 环境变量 - 方案2: Secret Manager（生产环境，use_secret_manager=true）
      dynamic "env" {
        for_each = var.use_secret_manager ? [1] : []
        content {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url[0].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.use_secret_manager ? [1] : []
        content {
          name = "SECRET_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.django_secret_key[0].secret_id
              version = "latest"
            }
          }
        }
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

      # 如果使用 S3/GCS
      dynamic "env" {
        for_each = var.use_s3 ? [1] : []
        content {
          name  = "AWS_ACCESS_KEY_ID"
          value = var.aws_access_key_id
        }
      }

      dynamic "env" {
        for_each = var.use_s3 ? [1] : []
        content {
          name  = "AWS_SECRET_ACCESS_KEY"
          value = var.aws_secret_access_key
        }
      }

      dynamic "env" {
        for_each = var.use_s3 ? [1] : []
        content {
          name  = "AWS_STORAGE_BUCKET_NAME"
          value = var.aws_storage_bucket_name
        }
      }

      # 资源限制（符合免费额度）
      resources {
        limits = {
          cpu    = "1"       # 1 vCPU
          memory = "512Mi"   # 512MB
        }
        cpu_idle          = true   # CPU仅在处理请求时计费
        startup_cpu_boost = false  # 不使用启动加速（节省成本）
      }

      # 健康检查端点
      ports {
        container_port = 8000
      }
    }

    # 超时设置
    timeout = "300s"

    # Service Account（用于访问其他GCP服务）
    service_account = google_service_account.cloud_run_sa.email
  }

  # 流量配置
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = {
    project     = "maori-story-fill"
    environment = var.environment
    managed-by  = "terraform"
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,  # 允许手动更新镜像
    ]
  }
}

# ============================================
# Secret Manager（可选：生产环境推荐）
# ============================================

resource "google_secret_manager_secret" "database_url" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = "maori-story-database-url-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    project = "maori-story-fill"
  }
}

resource "google_secret_manager_secret" "django_secret_key" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = "maori-story-django-secret-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    project = "maori-story-fill"
  }
}

# ============================================
# IAM - Service Account for Cloud Run
# ============================================

resource "google_service_account" "cloud_run_sa" {
  account_id   = "maori-story-backend-${var.environment}"
  display_name = "Maori Story Backend Service Account"
  description  = "Service account for Cloud Run backend service"
}

# 授权访问 Secret Manager
resource "google_secret_manager_secret_iam_member" "database_url_access" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = google_secret_manager_secret.database_url[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "django_secret_access" {
  count     = var.use_secret_manager ? 1 : 0
  secret_id = google_secret_manager_secret.django_secret_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# 如果需要访问 GCS（用于媒体文件）
resource "google_project_iam_member" "cloud_run_storage" {
  count   = var.use_gcs_for_media ? 1 : 0
  project = var.gcp_project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# 允许日志写入
resource "google_project_iam_member" "cloud_run_logging" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# ============================================
# Cloud Run IAM - 公开访问配置
# ============================================

# 允许未认证用户访问（公开API）
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================
# 可选：GCS Bucket for Media Files
# ============================================

resource "google_storage_bucket" "media" {
  count    = var.use_gcs_for_media ? 1 : 0
  name     = "${var.gcp_project_id}-maori-story-media-${var.environment}"
  location = var.gcs_location

  # 公开读取（用于提供媒体文件）
  uniform_bucket_level_access = true

  # CORS 配置
  cors {
    origin          = var.cors_allowed_origins_list
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = {
    project     = "maori-story-fill"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# 设置 bucket 为公开可读
resource "google_storage_bucket_iam_member" "media_public" {
  count  = var.use_gcs_for_media ? 1 : 0
  bucket = google_storage_bucket.media[0].name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# ============================================
# Outputs
# ============================================

output "artifact_registry_url" {
  description = "Artifact Registry Docker 仓库地址"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.maori_story.repository_id}"
}

output "cloud_run_url" {
  description = "Cloud Run 后端服务 URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "service_account_email" {
  description = "Cloud Run Service Account Email"
  value       = google_service_account.cloud_run_sa.email
}

output "media_bucket_url" {
  description = "GCS 媒体文件 Bucket URL"
  value       = var.use_gcs_for_media ? "gs://${google_storage_bucket.media[0].name}" : "Not using GCS for media"
}

output "docker_push_command" {
  description = "Docker 镜像推送命令示例"
  value       = "docker push ${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.maori_story.repository_id}/backend:latest"
}

output "secret_manager_status" {
  description = "Secret Manager 使用状态"
  value       = var.use_secret_manager ? "✅ 已启用 Secret Manager（生产环境）" : "⚠️  使用普通环境变量（测试环境）"
}

output "cost_optimization_info" {
  description = "成本优化配置信息"
  value = {
    region         = var.gcp_region
    min_instances  = 0
    max_instances  = 1
    cpu            = "1"
    memory         = "512Mi"
    estimated_cost = "$0/月（免费额度内）"
  }
}
