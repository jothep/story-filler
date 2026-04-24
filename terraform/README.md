# Terraform 配置文件

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `main.tf` | 主配置文件，定义所有 AWS 资源 |
| `variables.tf` | 变量定义 |
| `outputs.tf` | 输出配置 |
| `terraform.tfvars` | 变量值（**包含敏感信息，不提交到 Git**） |
| `terraform.tfvars.example` | 变量值示例模板 |
| `user-data.sh` | EC2 实例初始化脚本 |

## 🚀 快速开始

```bash
# 1. 复制配置模板
cp terraform.tfvars.example terraform.tfvars

# 2. 编辑配置（填写密钥和密码）
vim terraform.tfvars

# 3. 初始化 Terraform
terraform init

# 4. 预览资源
terraform plan

# 5. 创建资源
terraform apply
```

## 📚 详细文档

请参阅项目根目录的 [TERRAFORM_GUIDE.md](../TERRAFORM_GUIDE.md)

## ⚠️ 注意事项

- **不要提交 `terraform.tfvars` 到 Git**（已在 .gitignore 中排除）
- **不要提交 `.terraform/` 目录**
- **使用 GCS Backend 存储状态**（已配置 Google Cloud Storage）
  - 存储桶：`jaskojothep-terraform-state`
  - 状态路径：`terraform/state/maori-story-fill`
  - 自动版本控制和备份

## 💰 成本估算

- **EC2 t3.small**: $0.0208/小时
- **EBS 30GB gp3**: $2.40/月
- **Elastic IP**: $0（绑定时免费）

**每月使用 160 小时**：约 **$7-10/月**
