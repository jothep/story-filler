# Terraform 配置

部署 Maori Story Fill 后端到 Google Cloud Run。

## 快速开始

```bash
# 1. 复制配置
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # 填写配置

# 2. 认证 GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. 启用 API
gcloud services enable artifactregistry.googleapis.com run.googleapis.com

# 4. 部署基础设施
terraform init
terraform apply

# 5. 构建并推送镜像
cd ../backend
docker build -t $(terraform -chdir=../terraform output -raw registry_url)/backend:latest .
docker push $(terraform -chdir=../terraform output -raw registry_url)/backend:latest
```

## 配置说明

- **必填变量**: gcp_project_id, database_url, django_secret_key
- **免费数据库**: 推荐 Neon (https://neon.tech)
- **成本**: $0/月（免费额度内）

## 资源

- Artifact Registry (500MB 免费)
- Cloud Run (200万请求/月 免费)
  - Max instances: 1 (成本控制)
  - CPU: 1 core, Memory: 512Mi

详细文档: [CLOUD_RUN_DEPLOY_GUIDE.md](./CLOUD_RUN_DEPLOY_GUIDE.md)
