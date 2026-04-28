variable "gcp_project_id" {
  description = "GCP 项目 ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP 区域"
  type        = string
  default     = "us-central1"
}

variable "database_url" {
  description = "Neon PostgreSQL 连接字符串"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "allowed_hosts" {
  description = "Django ALLOWED_HOSTS"
  type        = string
  default     = "*"
}

variable "cors_allowed_origins" {
  description = "CORS 允许的源（前端 GitHub Pages URL）"
  type        = string
  default     = "https://yourusername.github.io"
}
