# ============================================
# Maori Story Fill - GCP Variables
# ============================================

# ============================================
# 必需变量 (Required)
# ============================================

variable "gcp_project_id" {
  description = "GCP 项目 ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP 区域（例如 us-central1）"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "环境名称（dev, staging, prod）"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# ============================================
# Secret Manager 配置
# ============================================

variable "use_secret_manager" {
  description = "是否使用 Secret Manager 管理敏感信息（false=直接环境变量, true=Secret Manager）"
  type        = bool
  default     = false
}

# ============================================
# 数据库配置
# ============================================

variable "database_url" {
  description = "PostgreSQL 数据库连接字符串（格式：postgresql://user:${DB_PASSWORD}@host:port/dbname）"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django SECRET_KEY（用于加密）"
  type        = string
  sensitive   = true
}

# ============================================
# 应用配置
# ============================================

variable "allowed_hosts" {
  description = "Django ALLOWED_HOSTS（逗号分隔）"
  type        = string
  default     = "*"
}

variable "cors_allowed_origins" {
  description = "CORS 允许的源（逗号分隔）"
  type        = string
  default     = "https://your-username.github.io"
}

variable "cors_allowed_origins_list" {
  description = "CORS 允许的源（列表格式，用于 GCS CORS 配置）"
  type        = list(string)
  default     = ["https://your-username.github.io"]
}

# ============================================
# Cloud Run 配置
# ============================================
# 注意：为了严格控制成本，扩缩容和资源配置已在 main.tf 中硬编码：
# - min_instance_count = 0
# - max_instance_count = 1
# - cpu = "1"
# - memory = "512Mi"
# 如需修改，请直接编辑 main.tf 中的配置

# ============================================
# 存储配置
# ============================================

variable "use_s3" {
  description = "是否使用 S3/GCS 存储媒体文件（字符串 'true' 或 'false'）"
  type        = string
  default     = "false"
}

variable "use_gcs_for_media" {
  description = "是否创建 GCS bucket 用于媒体文件（推荐用 S3 兼容模式）"
  type        = bool
  default     = false
}

variable "gcs_location" {
  description = "GCS Bucket 位置（例如 US, EU, ASIA）"
  type        = string
  default     = "US"
}

# S3 配置（如果使用 AWS S3 而不是 GCS）
variable "aws_access_key_id" {
  description = "AWS Access Key ID（如果使用 S3）"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key（如果使用 S3）"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_storage_bucket_name" {
  description = "S3 Bucket 名称（如果使用 S3）"
  type        = string
  default     = ""
}
