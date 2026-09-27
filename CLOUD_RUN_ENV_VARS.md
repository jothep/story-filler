# Cloud Run Environment Variables Management

This document describes how to manage environment variables for the backend service deployed on Google Cloud Run.

## Current Environment Variables

The backend service requires the following environment variables:

### Required Variables
- `DATABASE_URL` - PostgreSQL connection string (Neon database)
- `SECRET_KEY` - Django secret key for cryptographic signing
- `DEBUG` - Set to `False` for production
- `ALLOWED_HOSTS` - Allowed host/domain names (set to `*` for Cloud Run)
- `USE_GCS` - Set to `true` to enable Google Cloud Storage for media files
- `GS_BUCKET_NAME` - GCS bucket name for media storage

### CORS and CSRF Configuration
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed origins
  - Example: `http://localhost:5173,http://localhost:8080,https://jothep.github.io`
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins for CSRF
  - Example: `http://localhost:8000,http://localhost`
- `CSRF_TRUSTED_ORIGIN_WILDCARDS` - Wildcard patterns for trusted origins
  - Example: `https://*.run.app`

## How to Update Environment Variables

### Method 1: Using gcloud CLI (Recommended)

Update individual variables:
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --update-env-vars="KEY=value"
```

Set all variables at once (replaces all existing variables):
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --set-env-vars="KEY1=value1,KEY2=value2,..."
```

### Method 2: Using YAML file

Create a private, untracked `.local-secrets/cloud-run-env-vars.yaml` from hidden input (JSON is valid YAML). Existing files are not overwritten:
```bash
printf 'DATABASE_URL (hidden input): '
read -r -s DATABASE_URL
printf '\n'
: "${DATABASE_URL:?A non-empty value is required}"
export DATABASE_URL
printf 'SECRET_KEY (hidden input): '
read -r -s SECRET_KEY
printf '\n'
: "${SECRET_KEY:?A non-empty value is required}"
export SECRET_KEY
umask 077
python3 - <<'PYENV'
import json
import os
from pathlib import Path

values = {'DEBUG': 'False', 'ALLOWED_HOSTS': '*', 'USE_GCS': 'true', 'GS_BUCKET_NAME': 'your-bucket-name', 'CORS_ALLOWED_ORIGINS': 'http://localhost:5173,http://localhost:8080,https://jothep.github.io', 'CSRF_TRUSTED_ORIGINS': 'http://localhost:8000,http://localhost', 'CSRF_TRUSTED_ORIGIN_WILDCARDS': 'https://*.run.app'}
values.update({key: os.environ[key] for key in ('DATABASE_URL', 'SECRET_KEY')})
Path('.local-secrets').mkdir(mode=0o700, exist_ok=True)
with Path('.local-secrets/cloud-run-env-vars.yaml').open('x') as config:
    json.dump(values, config, indent=2)
PYENV
```

Apply the configuration:
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --env-vars-file=.local-secrets/cloud-run-env-vars.yaml
```

### Method 3: Using Google Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on `maori-story-backend` service
3. Click "EDIT & DEPLOY NEW REVISION"
4. Scroll to "Container(s), Volumes, Networking, Security"
5. Under "Variables & Secrets" tab, add/edit environment variables
6. Click "DEPLOY"

## Important Notes

- ⚠️ **CI/CD does NOT automatically update environment variables**
  - The deployment workflow only updates the container image
  - Environment variables must be managed manually
  
- 🔒 **Never commit sensitive values to git**
  - Use GitHub Secrets for CI/CD
  - Use Secret Manager for production secrets
  
- 📝 **Document changes**
  - Keep this file updated when adding/removing variables
  - Update `.env.example` files accordingly

## Viewing Current Variables

List all environment variables:
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="table(spec.template.spec.containers[0].env)"
```

Check specific variable:
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)" | grep KEY_NAME
```

## Troubleshooting

### Service fails to start
- Check logs: `gcloud run services logs read maori-story-backend --region=us-central1 --limit=50`
- Verify all required variables are set
- Check for typos in variable names

### CORS errors in browser
- Verify `CORS_ALLOWED_ORIGINS` includes the frontend URL
- Check that the URL matches exactly (including protocol)
- Remember: Origin includes protocol and domain, but NOT path

### Database connection errors
- Verify `DATABASE_URL` format is correct
- Check Neon database is accessible from Cloud Run
- Ensure connection string includes `?sslmode=require`

---

# Cloud Run 环境变量管理（中文版）

本文档描述如何管理部署在 Google Cloud Run 上的后端服务的环境变量。

## 当前环境变量

后端服务需要以下环境变量：

### 必需变量
- `DATABASE_URL` - PostgreSQL 连接字符串（Neon 数据库）
- `SECRET_KEY` - Django 密钥，用于加密签名
- `DEBUG` - 生产环境设置为 `False`
- `ALLOWED_HOSTS` - 允许的主机/域名（Cloud Run 设置为 `*`）
- `USE_GCS` - 设置为 `true` 启用 Google Cloud Storage 存储媒体文件
- `GS_BUCKET_NAME` - GCS 存储桶名称

### CORS 和 CSRF 配置
- `CORS_ALLOWED_ORIGINS` - 允许的源（逗号分隔）
  - 示例：`http://localhost:5173,http://localhost:8080,https://jothep.github.io`
- `CSRF_TRUSTED_ORIGINS` - CSRF 信任的源（逗号分隔）
  - 示例：`http://localhost:8000,http://localhost`
- `CSRF_TRUSTED_ORIGIN_WILDCARDS` - 信任源的通配符模式
  - 示例：`https://*.run.app`

## 如何更新环境变量

### 方法一：使用 gcloud CLI（推荐）

更新单个变量：
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --update-env-vars="KEY=value"
```

一次性设置所有变量（替换所有现有变量）：
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --set-env-vars="KEY1=value1,KEY2=value2,..."
```

### 方法二：使用 YAML 文件

通过隐藏输入生成不提交 Git 的私有 `.local-secrets/cloud-run-env-vars.yaml`（JSON 是有效 YAML）；已有文件不会被覆盖：
```bash
printf 'DATABASE_URL (hidden input): '
read -r -s DATABASE_URL
printf '\n'
: "${DATABASE_URL:?A non-empty value is required}"
export DATABASE_URL
printf 'SECRET_KEY (hidden input): '
read -r -s SECRET_KEY
printf '\n'
: "${SECRET_KEY:?A non-empty value is required}"
export SECRET_KEY
umask 077
python3 - <<'PYENV'
import json
import os
from pathlib import Path

values = {'DEBUG': 'False', 'ALLOWED_HOSTS': '*', 'USE_GCS': 'true', 'GS_BUCKET_NAME': 'your-bucket-name', 'CORS_ALLOWED_ORIGINS': 'http://localhost:5173,http://localhost:8080,https://jothep.github.io', 'CSRF_TRUSTED_ORIGINS': 'http://localhost:8000,http://localhost', 'CSRF_TRUSTED_ORIGIN_WILDCARDS': 'https://*.run.app'}
values.update({key: os.environ[key] for key in ('DATABASE_URL', 'SECRET_KEY')})
Path('.local-secrets').mkdir(mode=0o700, exist_ok=True)
with Path('.local-secrets/cloud-run-env-vars.yaml').open('x') as config:
    json.dump(values, config, indent=2)
PYENV
```

应用配置：
```bash
gcloud run services update maori-story-backend \
  --region=us-central1 \
  --env-vars-file=.local-secrets/cloud-run-env-vars.yaml
```

### 方法三：使用 Google Cloud Console

1. 访问 [Cloud Run 控制台](https://console.cloud.google.com/run)
2. 点击 `maori-story-backend` 服务
3. 点击"编辑并部署新修订版本"
4. 滚动到"容器、卷、网络、安全性"
5. 在"变量和密钥"标签下，添加/编辑环境变量
6. 点击"部署"

## 重要说明

- ⚠️ **CI/CD 不会自动更新环境变量**
  - 部署工作流只更新容器镜像
  - 环境变量必须手动管理
  
- 🔒 **永远不要将敏感值提交到 git**
  - CI/CD 使用 GitHub Secrets
  - 生产环境使用 Secret Manager
  
- 📝 **记录变更**
  - 添加/删除变量时更新此文件
  - 相应更新 `.env.example` 文件

## 查看当前变量

列出所有环境变量：
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="table(spec.template.spec.containers[0].env)"
```

检查特定变量：
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)" | grep KEY_NAME
```

## 故障排除

### 服务启动失败
- 查看日志：`gcloud run services logs read maori-story-backend --region=us-central1 --limit=50`
- 验证所有必需变量已设置
- 检查变量名是否有拼写错误

### 浏览器中的 CORS 错误
- 验证 `CORS_ALLOWED_ORIGINS` 包含前端 URL
- 检查 URL 是否完全匹配（包括协议）
- 记住：Origin 包含协议和域名，但不包含路径

### 数据库连接错误
- 验证 `DATABASE_URL` 格式正确
- 检查 Neon 数据库可从 Cloud Run 访问
- 确保连接字符串包含 `?sslmode=require`
