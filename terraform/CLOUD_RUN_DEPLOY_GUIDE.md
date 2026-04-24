# Cloud Run + Artifact Registry 部署指南

本指南说明如何将 Maori Story Fill 后端部署到 Google Cloud Run，前端部署到 GitHub Pages。

## 🏗️ 架构

```
┌─────────────────┐     ┌──────────────────┐
│  GitHub Pages   │────▶│   Cloud Run      │
│  (前端静态)      │     │   (Django后端)    │
└─────────────────┘     └──────────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │ 免费数据库    │
                        │ (Neon/Supabase)│
                        └──────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │ S3/GCS存储   │
                        │ (媒体文件)    │
                        └──────────────┘
```

**预计成本：$0-2/月** 🎉

---

## 📋 前置条件

### 1. 安装工具

```bash
# Google Cloud SDK
brew install --cask google-cloud-sdk

# Docker（用于构建镜像）
brew install --cask docker

# Terraform
brew install terraform
```

### 2. 认证 GCP

```bash
# 登录 GCP
gcloud auth login

# 设置默认项目
gcloud config set project YOUR_PROJECT_ID

# 配置 Docker 认证（推送镜像用）
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 3. 启用 GCP API

```bash
# 启用必需的 API
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com
```

---

## 🚀 部署步骤

### 步骤1：准备免费数据库

选择一个免费的 PostgreSQL 服务：

#### 选项A：Neon（推荐）
1. 访问：https://neon.tech
2. 创建账号并新建项目
3. 获取连接字符串：
   ```
   postgresql://username:${DB_PASSWORD}@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

#### 选项B：Supabase
1. 访问：https://supabase.com
2. 创建项目
3. 获取连接字符串（Database Settings → Connection String）

#### 选项C：ElephantSQL
1. 访问：https://www.elephantsql.com
2. 创建免费实例（Tiny Turtle plan）
3. 获取连接URL

---

### 步骤2：配置 Terraform 变量

```bash
cd terraform/

# 复制配置模板
cp terraform.tfvars.example terraform.tfvars

# 编辑配置
vim terraform.tfvars
```

**必填项：**
```hcl
gcp_project_id    = "your-gcp-project-id"
database_url      = "postgresql://..."
django_secret_key = "生成的随机密钥"
cors_allowed_origins = "https://yourusername.github.io"
```

**生成 Django Secret Key：**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

### 步骤3：创建 GCP 资源

```bash
cd terraform/

# 初始化 Terraform
terraform init

# 预览将创建的资源
terraform plan

# 创建资源
terraform apply
```

**创建的资源：**
- ✅ Artifact Registry Repository（Docker镜像仓库）
- ✅ Cloud Run Service（后端服务）
- ✅ Service Account（权限管理）
- ✅ IAM配置（公开访问）

**输出信息（保存好）：**
```
artifact_registry_url = "us-central1-docker.pkg.dev/your-project/maori-story-prod"
cloud_run_url        = "https://maori-story-backend-xxx-uc.a.run.app"
```

---

### 步骤4：构建并推送 Docker 镜像

#### 4.1 构建镜像

```bash
cd /Users/zhuxiang/Documents/maori-story-fill/backend

# 获取 Artifact Registry URL（从 terraform output）
REGISTRY_URL=$(terraform -chdir=../terraform output -raw artifact_registry_url)

# 构建镜像
docker build -t $REGISTRY_URL/backend:latest .
```

#### 4.2 推送镜像

```bash
# 推送到 Artifact Registry
docker push $REGISTRY_URL/backend:latest
```

**首次推送可能需要几分钟（~200MB镜像）。**

#### 4.3 更新 Cloud Run 服务

```bash
# Cloud Run 会自动检测新镜像并部署
# 或者手动触发更新：
gcloud run services update maori-story-backend-prod \
  --region=us-central1 \
  --image=$REGISTRY_URL/backend:latest
```

---

### 步骤5：初始化数据库

Cloud Run 服务启动后会自动运行迁移，但需要创建超级用户：

```bash
# 获取 Cloud Run 服务名
SERVICE_NAME=$(terraform -chdir=./terraform output -raw cloud_run_url | sed 's|https://||' | cut -d. -f1)

# 创建超级用户（交互式）
gcloud run services proxy $SERVICE_NAME --region=us-central1 &
sleep 3

# 在另一个终端运行
docker exec -it <container-id> python manage.py createsuperuser

# 或者使用脚本自动创建
# （需要先设置环境变量：DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, DJANGO_SUPERUSER_EMAIL）
```

**更简单的方法：**
直接访问 Cloud Run URL + `/admin/` 创建用户。

---

### 步骤6：配置前端（GitHub Pages）

#### 6.1 更新前端API地址

编辑 `frontend/.env.production`：

```bash
# 获取 Cloud Run URL
CLOUD_RUN_URL=$(terraform -chdir=../terraform output -raw cloud_run_url)

cat > frontend/.env.production << EOF
VITE_API_URL=$CLOUD_RUN_URL
EOF
```

#### 6.2 构建前端

```bash
cd frontend/
npm install
npm run build
```

#### 6.3 部署到 GitHub Pages

```bash
# 方法1：使用 GitHub Actions（推荐）
# 创建 .github/workflows/deploy-pages.yml

# 方法2：手动部署
npm install -g gh-pages
gh-pages -d dist
```

**GitHub Actions 配置示例：**
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Build
        run: |
          cd frontend
          npm install
          echo "VITE_API_URL=${{ secrets.CLOUD_RUN_URL }}" > .env.production
          npm run build
      
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/dist
```

---

## ✅ 验证部署

### 1. 测试后端

```bash
# 获取 Cloud Run URL
CLOUD_RUN_URL=$(terraform -chdir=./terraform output -raw cloud_run_url)

# 测试健康检查
curl $CLOUD_RUN_URL/health

# 测试 API
curl $CLOUD_RUN_URL/api/stories/
```

### 2. 测试前端

访问：`https://yourusername.github.io`

检查：
- ✅ 页面正常加载
- ✅ 能访问后端API
- ✅ CORS配置正确

---

## 🔄 更新部署

### 更新后端

```bash
# 1. 修改代码
cd backend/
# ... 编辑代码 ...

# 2. 重新构建镜像
REGISTRY_URL=$(terraform -chdir=../terraform output -raw artifact_registry_url)
docker build -t $REGISTRY_URL/backend:latest .

# 3. 推送新镜像
docker push $REGISTRY_URL/backend:latest

# 4. Cloud Run 自动更新（或手动触发）
gcloud run services update maori-story-backend-prod \
  --region=us-central1 \
  --image=$REGISTRY_URL/backend:latest
```

### 更新前端

```bash
# 1. 修改代码
cd frontend/
# ... 编辑代码 ...

# 2. 重新构建并部署
npm run build
gh-pages -d dist  # 或者 git push 触发 GitHub Actions
```

---

## 💰 成本监控

### 查看 Cloud Run 使用情况

```bash
# 查看请求数
gcloud run services describe maori-story-backend-prod \
  --region=us-central1 \
  --format='value(status.traffic[0].latestRevision)'

# 查看日志
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format=json
```

### Cloud Run 免费额度

| 资源 | 免费额度/月 |
|------|-----------|
| 请求 | 200万次 |
| CPU时间 | 180,000 vCPU-秒 |
| 内存 | 360,000 GiB-秒 |
| 网络出站 | 1 GB |

**轻度使用基本不会超过免费额度！**

---

## 🐛 故障排查

### 问题1：Cloud Run 无法启动

```bash
# 查看日志
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=100 \
  --format=json

# 常见原因：
# - 数据库连接失败 → 检查 DATABASE_URL
# - 缺少环境变量 → 检查 terraform.tfvars
# - 镜像构建错误 → 检查 Dockerfile
```

### 问题2：CORS 错误

```bash
# 检查 CORS 配置
echo $CORS_ALLOWED_ORIGINS

# 更新配置
terraform apply -var="cors_allowed_origins=https://yourusername.github.io"
```

### 问题3：镜像推送失败

```bash
# 重新认证 Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# 检查权限
gcloud artifacts repositories get-iam-policy maori-story-prod \
  --location=us-central1
```

### 问题4：数据库迁移失败

```bash
# 手动运行迁移
gcloud run jobs create migrate-db \
  --image=$REGISTRY_URL/backend:latest \
  --region=us-central1 \
  --command="python,manage.py,migrate"

gcloud run jobs execute migrate-db --region=us-central1
```

---

## 🔐 安全最佳实践

### 1. 使用 Secret Manager

```bash
# 创建 secret
echo -n "your-secret-key" | \
  gcloud secrets create django-secret-key --data-file=-

# 更新 Cloud Run 使用 secret
gcloud run services update maori-story-backend-prod \
  --region=us-central1 \
  --update-secrets=SECRET_KEY=REMOVED_CREDENTIAL
```

### 2. 限制访问

```hcl
# terraform/main.tf
# 如果只允许前端访问，可以删除 allUsers 权限
# 并使用 Service Account 认证
```

### 3. 配置自定义域名

```bash
# 映射自定义域名
gcloud run domain-mappings create \
  --service=maori-story-backend-prod \
  --domain=api.yourdomain.com \
  --region=us-central1
```

---

## 📊 监控和日志

### 查看实时日志

```bash
gcloud run services logs read maori-story-backend-prod \
  --region=us-central1 \
  --limit=50 \
  --follow
```

### 设置告警

```bash
# 创建告警策略（请求错误率 > 5%）
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="Cloud Run Error Rate" \
  --condition-display-name="Error rate too high" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

---

## 🎓 下一步

- [ ] 配置自定义域名
- [ ] 设置 CI/CD 自动部署
- [ ] 配置 CDN（Cloud CDN或Cloudflare）
- [ ] 添加监控和告警
- [ ] 配置备份策略

---

## 📚 参考文档

- [Cloud Run 官方文档](https://cloud.google.com/run/docs)
- [Artifact Registry 文档](https://cloud.google.com/artifact-registry/docs)
- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [Django on Cloud Run](https://cloud.google.com/python/django/run)

---

**恭喜！你的应用现在运行在完全免费或几乎免费的云基础设施上了！** 🎉
