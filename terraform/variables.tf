variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "prod"
}

variable "database_url" {
  description = "PostgreSQL connection string"
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
  description = "CORS allowed origins"
  type        = string
  default     = "https://yourusername.github.io"
}

variable "use_s3" {
  description = "Use S3 for media storage"
  type        = string
  default     = "false"
}

variable "aws_access_key_id" {
  description = "AWS Access Key (if use_s3=true)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS Secret Key (if use_s3=true)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_storage_bucket_name" {
  description = "S3 Bucket name (if use_s3=true)"
  type        = string
  default     = ""
}
