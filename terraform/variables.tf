# ============================================
# Maori Story Fill - Terraform Variables
# ============================================

# ----------------------
# AWS 基础配置
# ----------------------

variable "aws_region" {
  description = "AWS 区域"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "环境名称 (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# ----------------------
# 网络配置
# ----------------------

variable "vpc_id" {
  description = "VPC ID（使用默认 VPC 或指定现有 VPC）"
  type        = string
  default     = ""  # 留空将使用默认 VPC
}

variable "subnet_id" {
  description = "子网 ID（留空将使用默认子网）"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidrs" {
  description = "允许 SSH 访问的 CIDR 列表"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # 生产环境建议改为你的公网 IP
}

# ----------------------
# EC2 实例配置
# ----------------------

variable "instance_type" {
  description = "EC2 实例类型"
  type        = string
  default     = "t3.small"

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium"], var.instance_type)
    error_message = "实例类型必须是 t3.micro, t3.small 或 t3.medium"
  }
}

variable "key_pair_name" {
  description = "SSH 密钥对名称（必须提前在 AWS 中创建）"
  type        = string
}

variable "root_volume_size" {
  description = "根卷大小（GB）"
  type        = number
  default     = 30

  validation {
    condition     = var.root_volume_size >= 20 && var.root_volume_size <= 100
    error_message = "根卷大小必须在 20-100 GB 之间"
  }
}

# ----------------------
# 应用配置
# ----------------------

variable "db_password" {
  description = "PostgreSQL 数据库密码"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django 密钥"
  type        = string
  sensitive   = true
}

variable "git_repo_url" {
  description = "Git 仓库 URL"
  type        = string
  default     = "https://github.com/your-username/maori-story-fill.git"
}

variable "git_branch" {
  description = "Git 分支"
  type        = string
  default     = "main"
}

# ----------------------
# 监控配置
# ----------------------

variable "enable_detailed_monitoring" {
  description = "启用详细监控（额外费用 ~$2/月）"
  type        = bool
  default     = false
}

variable "enable_cloudwatch_alarms" {
  description = "启用 CloudWatch 告警"
  type        = bool
  default     = false
}

variable "alarm_sns_topic_arn" {
  description = "告警通知的 SNS Topic ARN"
  type        = string
  default     = ""
}

# ----------------------
# 标签
# ----------------------

variable "additional_tags" {
  description = "额外的资源标签"
  type        = map(string)
  default     = {}
}
