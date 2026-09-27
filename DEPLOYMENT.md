> **Historical implementation note — September 2026 review:** This document retains an earlier design, estimate, procedure or plan. It is not the current deployment specification, and its performance, cost, security and recovery claims have not all been revalidated. Use the [architecture index](docs/ARCHITECTURE.md) and [dated verification record](docs/verification.md) for current scope and evidence.

# 部署指南

完整部署 Maori Story Fill 到 GCP Cloud Run + Neon 数据库。

---

## 架构

```
┌─────────────────┐
│ GitHub Pages    │  ← 前端（静态网站）
│ yourusername.   │
│ github.io       │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│ Cloud Run       │  ← 后端（Django API）
│ maori-story-    │
│ backend         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Neon PostgreSQL │  ← 数据库（免费500MB）
│ neon.tech       │
└─────────────────┘

┌─────────────────┐
│ Artifact        │  ← Docker镜像仓库
│ Registry        │
└─────────────────┘
```

**总成本：$0/月** ✅

---

## 前置准备

### 1. 安装工具

```bash
# macOS
brew install --cask google-cloud-sdk
brew install --cask docker
brew install terraform

# 验证安装
gcloud --version
docker --version
terraform --version
```

### 2. 认证 GCP

```bash
# 登录
gcloud auth login

# 设置项目
gcloud config set project YOUR_PROJECT_ID

# 配置 Docker 认证
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## 步骤 1：创建 Neon 数据库

### 1.1 注册 Neon

访问：https://neon.tech

点击 "Sign Up" 注册账号（支持 GitHub 登录）

### 1.2 创建项目

1. 进入 Dashboard
2. 点击 "Create a project"
3. 配置：
   - Project name: `maori-story`
   - Region: `US East (Ohio)` 或离你最近的区域
   - PostgreSQL version: 默认（最新版本）
4. 点击 "Create project"

### 1.3 获取连接字符串

创建完成后，页面会显示连接信息：

通过下方隐藏输入，将完整连接字符串保存在当前 shell 的 `DATABASE_URL` 环境变量中。

**保存这个连接字符串！** 稍后需要用到。

### 1.4 验证连接（可选）

```bash
printf 'DATABASE_URL (hidden input): '
read -r -s DATABASE_URL
printf '\n'
: "${DATABASE_URL:?A non-empty value is required}"
export DATABASE_URL
psql "$DATABASE_URL"
# 成功连接会看到 neondb=> 提示符
# 输入 \q 退出
```

---

## 步骤 2：配置 Terraform

### 2.1 创建配置文件

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
```

### 2.2 编辑配置

```bash
vim terraform.tfvars
```

填写以下内容：

```hcl
gcp_project_id = "your-gcp-project-id"  # 替换为你的 GCP 项目 ID
gcp_region     = "us-central1"

# 连接字符串通过 TF_VAR_database_url 传入
# Set TF_VAR_database_url in the shell; omit this value from .tfvars.

# 生成 Django 密钥
# Set TF_VAR_django_secret_key in the shell; omit this value from .tfvars.

# 前端 GitHub Pages URL（稍后配置）
cors_allowed_origins = "https://yourusername.github.io"
```

### 2.3 生成 Django 密钥

```bash
printf 'DATABASE_URL (hidden input): '
read -r -s DATABASE_URL
printf '\n'
: "${DATABASE_URL:?A non-empty value is required}"
export DATABASE_URL
export TF_VAR_database_url="$DATABASE_URL"
# 仅首次部署生成；已有部署请私下输入其现有签名密钥。
export TF_VAR_django_secret_key="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
```

密钥仅保存在当前 shell 的 `TF_VAR_django_secret_key` 中，不会显示在终端。已有部署请通过隐藏输入加载现有值；不要重新生成。

---

## 步骤 3：部署基础设施

### 3.1 启用 GCP API

```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com
```

### 3.2 初始化 Terraform

```bash
terraform init
```

输出：
```
Initializing the backend...
Successfully configured the backend "gcs"!
Terraform has been successfully initialized!
```

### 3.3 预览资源

```bash
terraform plan
```

会显示将创建的资源：
- Artifact Registry Repository
- Service Account
- Cloud Run Service
- IAM Binding

### 3.4 创建资源

```bash
terraform apply
```

输入 `yes` 确认。

部署完成后，保存输出信息：

```
Outputs:

registry_url = "us-central1-docker.pkg.dev/your-project/maori-story"
service_url  = "https://maori-story-backend-xxx-uc.a.run.app"
push_command = "docker push us-central1-docker.pkg.dev/your-project/maori-story/backend:latest"
```

---

## 步骤 4：构建并推送 Docker 镜像

### 4.1 构建镜像

```bash
cd ../backend

# 获取仓库地址
REGISTRY_URL=$(terraform -chdir=../terraform output -raw registry_url)

# 构建镜像
docker build -t $REGISTRY_URL/backend:latest .
```

构建需要 3-5 分钟。

### 4.2 推送镜像

```bash
docker push $REGISTRY_URL/backend:latest
```

首次推送需要 2-3 分钟（约 200MB）。

### 4.3 验证推送

```bash
gcloud artifacts docker images list $REGISTRY_URL
```

应该看到 `backend` 镜像及其标签。

---

## 步骤 5：初始化数据库

### 5.1 运行数据库迁移

```bash
# 获取 Cloud Run 服务 URL
SERVICE_URL=$(terraform -chdir=../terraform output -raw service_url)

# 等待服务启动
sleep 30

# 测试服务
curl $SERVICE_URL/health
# 输出: OK
```

Cloud Run 容器启动时会自动运行 `python manage.py migrate`。

### 5.2 创建超级用户

访问 Django Admin 创建超级用户：

```bash
# 打开浏览器
open $SERVICE_URL/admin
```

首次访问时，Django 会提示创建超级用户，或手动创建：

```bash
# 通过 Cloud Run 运行命令
gcloud run services proxy maori-story-backend --region=us-central1 --port=8080 &

# 在另一个终端
docker exec -it <container-id> python manage.py createsuperuser
```

---

## 步骤 6：部署前端到 GitHub Pages

### 6.1 配置前端 API 地址

```bash
cd ../frontend

# 获取后端 URL
SERVICE_URL=$(terraform -chdir=../terraform output -raw service_url)

# 创建生产环境配置
echo "VITE_API_URL=$SERVICE_URL" > .env.production
```

### 6.2 构建前端

```bash
npm install
npm run build
```

### 6.3 部署到 GitHub Pages

**方法 1：GitHub Actions（推荐）**

已配置自动部署（`.github/workflows/deploy-frontend.yml`）。

推送代码即可：
```bash
git push
```

**方法 2：手动部署**

```bash
npm install -g gh-pages
gh-pages -d dist
```

### 6.4 配置 GitHub Pages

1. 访问：https://github.com/yourusername/maori-story-fill/settings/pages
2. Source: 选择 `gh-pages` 分支
3. Save

等待 1-2 分钟，访问：`https://yourusername.github.io`

### 6.5 更新 CORS

获取你的 GitHub Pages URL，更新 Terraform：

```bash
cd ../terraform
vim terraform.tfvars
```

修改：
```hcl
cors_allowed_origins = "https://yourusername.github.io"
```

重新部署：
```bash
terraform apply
```

---

## 验证部署

### 1. 测试后端

```bash
SERVICE_URL=$(terraform -chdir=./terraform output -raw service_url)

# 健康检查
curl $SERVICE_URL/health

# API 测试
curl $SERVICE_URL/api/stories/

# Admin 访问
open $SERVICE_URL/admin
```

### 2. 测试前端

访问：`https://yourusername.github.io`

检查：
- ✅ 页面正常加载
- ✅ 能访问后端 API
- ✅ 没有 CORS 错误

---

## 更新部署

### 更新后端

```bash
# 1. 修改代码
cd backend/
# ... 编辑代码 ...

# 2. 重新构建
REGISTRY_URL=$(terraform -chdir=../terraform output -raw registry_url)
docker build -t $REGISTRY_URL/backend:latest .

# 3. 推送
docker push $REGISTRY_URL/backend:latest

# 4. Cloud Run 自动更新（约1分钟）
```

### 更新前端

```bash
cd frontend/
# ... 编辑代码 ...

npm run build
gh-pages -d dist  # 或 git push 触发 Actions
```

---

## 常用命令

### Terraform

```bash
cd terraform/

# 查看资源状态
terraform show

# 查看输出
terraform output

# 删除所有资源
terraform destroy
```

### Cloud Run

```bash
# 查看服务列表
gcloud run services list

# 查看日志
gcloud run services logs read maori-story-backend \
  --region=us-central1 \
  --limit=50

# 更新服务（手动触发）
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --image=$REGISTRY_URL/backend:latest
```

### Docker

```bash
# 查看本地镜像
docker images | grep maori-story

# 清理未使用的镜像
docker image prune -a

# 登录镜像仓库
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## 故障排查

### 问题 1：Cloud Run 无法启动

**查看日志：**
```bash
gcloud run services logs read maori-story-backend \
  --region=us-central1 \
  --limit=100
```

**常见原因：**
- 数据库连接失败 → 检查 `database_url`
- 缺少环境变量 → 检查 `terraform.tfvars`
- 镜像错误 → 重新构建并推送

### 问题 2：CORS 错误

**症状：** 前端控制台显示 CORS 错误

**解决：**
```bash
cd terraform/
vim terraform.tfvars  # 更新 cors_allowed_origins
terraform apply
```

### 问题 3：数据库迁移失败

**解决：**
```bash
# 手动运行迁移
gcloud run jobs create migrate \
  --image=$REGISTRY_URL/backend:latest \
  --region=us-central1 \
  --command=python,manage.py,migrate

gcloud run jobs execute migrate --region=us-central1
```

### 问题 4：推送镜像失败

**解决：**
```bash
# 重新认证
gcloud auth configure-docker us-central1-docker.pkg.dev

# 检查权限
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

---

## 成本监控

### 免费额度

| 服务 | 免费额度/月 | 当前配置 |
|------|-----------|---------|
| Cloud Run | 200万请求 | 轻度使用 |
| Cloud Run CPU | 180,000 vCPU-秒 | 1 实例 |
| Artifact Registry | 500 MB | ~200MB |
| Neon 数据库 | 500 MB | 按需 |

### 查看使用情况

```bash
# Cloud Run 请求数
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=1000 \
  --format="table(timestamp,severity,textPayload)"

# 账单
gcloud beta billing accounts list
```

---

## 下一步

- [ ] 配置自定义域名
- [ ] 设置 GitHub Actions 自动部署
- [ ] 配置 Cloud CDN
- [ ] 添加监控告警
- [ ] 配置自动备份

---

## 资源链接

- [Neon 文档](https://neon.tech/docs)
- [Cloud Run 文档](https://cloud.google.com/run/docs)
- [Artifact Registry 文档](https://cloud.google.com/artifact-registry/docs)
- [GitHub Pages 文档](https://docs.github.com/en/pages)

---

**部署完成！享受你的免费云应用吧！** 🎉
