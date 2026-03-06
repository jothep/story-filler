# ============================================
# Maori Story Fill - AWS Infrastructure
# ============================================
# Terraform 配置：创建 EC2 实例用于部署应用

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # 可选：使用 S3 存储 Terraform 状态（生产环境推荐）
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "maori-story/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Provider 配置
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "MaoriStoryFill"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ============================================
# Data Sources
# ============================================

# 获取最新的 Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical (Ubuntu官方)

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# 获取当前 AWS 账户信息
data "aws_caller_identity" "current" {}

# ============================================
# Security Group
# ============================================

resource "aws_security_group" "maori_story_sg" {
  name        = "maori-story-sg-${var.environment}"
  description = "Security group for Maori Story Fill application"
  vpc_id      = var.vpc_id

  # SSH 访问
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
  }

  # HTTP 访问
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS 访问
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 允许所有出站流量
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "maori-story-sg-${var.environment}"
  }
}

# ============================================
# EC2 Instance
# ============================================

resource "aws_instance" "maori_story" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_pair_name
  subnet_id     = var.subnet_id

  vpc_security_group_ids = [aws_security_group.maori_story_sg.id]

  # EBS 根卷配置
  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    delete_on_termination = false  # 停止实例时保留数据
    encrypted             = true

    tags = {
      Name = "maori-story-root-${var.environment}"
    }
  }

  # User Data - 初始化脚本
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    db_password        = var.db_password
    django_secret_key  = var.django_secret_key
    git_repo_url       = var.git_repo_url
    git_branch         = var.git_branch
  }))

  # 启用详细监控（可选，额外费用约$2/月）
  monitoring = var.enable_detailed_monitoring

  # 实例元数据配置（安全最佳实践）
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # 强制使用 IMDSv2
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "maori-story-${var.environment}"
  }

  lifecycle {
    ignore_changes = [
      ami,  # 避免因 AMI 更新导致实例重建
    ]
  }
}

# ============================================
# Elastic IP
# ============================================

resource "aws_eip" "maori_story_eip" {
  domain = "vpc"

  tags = {
    Name = "maori-story-eip-${var.environment}"
  }
}

# 将 Elastic IP 绑定到 EC2 实例
resource "aws_eip_association" "maori_story_eip_assoc" {
  instance_id   = aws_instance.maori_story.id
  allocation_id = aws_eip.maori_story_eip.id
}

# ============================================
# IAM Role (可选 - 用于访问其他AWS服务)
# ============================================

# IAM 角色
resource "aws_iam_role" "maori_story_role" {
  name = "maori-story-ec2-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "maori-story-ec2-role-${var.environment}"
  }
}

# IAM 策略 - CloudWatch Logs（日志上传）
resource "aws_iam_role_policy" "cloudwatch_logs_policy" {
  name = "cloudwatch-logs-policy"
  role = aws_iam_role.maori_story_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/ec2/maori-story-*"
      }
    ]
  })
}

# IAM 实例配置文件
resource "aws_iam_instance_profile" "maori_story_profile" {
  name = "maori-story-ec2-profile-${var.environment}"
  role = aws_iam_role.maori_story_role.name
}

# 可选：将 IAM 角色附加到实例（取消注释以启用）
# resource "aws_iam_instance_profile_association" "maori_story" {
#   instance_id       = aws_instance.maori_story.id
#   iam_instance_profile = aws_iam_instance_profile.maori_story_profile.name
# }

# ============================================
# CloudWatch Alarms（可选 - 监控告警）
# ============================================

# CPU 使用率告警
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "maori-story-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ec2 cpu utilization"

  dimensions = {
    InstanceId = aws_instance.maori_story.id
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
}

# 状态检查失败告警
resource "aws_cloudwatch_metric_alarm" "instance_status_check" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "maori-story-status-check-failed-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "This metric monitors instance status check failures"

  dimensions = {
    InstanceId = aws_instance.maori_story.id
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
}

# ============================================
# Outputs
# ============================================

output "instance_id" {
  description = "EC2 实例 ID"
  value       = aws_instance.maori_story.id
}

output "instance_public_ip" {
  description = "实例的 Elastic IP 地址"
  value       = aws_eip.maori_story_eip.public_ip
}

output "instance_public_dns" {
  description = "实例的公共 DNS"
  value       = aws_instance.maori_story.public_dns
}

output "security_group_id" {
  description = "安全组 ID"
  value       = aws_security_group.maori_story_sg.id
}

output "ssh_command" {
  description = "SSH 连接命令"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.maori_story_eip.public_ip}"
}

output "web_url" {
  description = "应用访问地址"
  value       = "http://${aws_eip.maori_story_eip.public_ip}"
}
