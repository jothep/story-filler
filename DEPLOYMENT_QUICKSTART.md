# 🚀 部署快速开始（GCP Cloud Run + GitHub Pages）

完全免费或接近免费的部署方案！预计成本：**$0-2/月**

---

## 📋 清单

- [ ] GCP账号（免费层）
- [ ] 免费PostgreSQL数据库（Neon/Supabase等）
- [ ] GitHub账号（Pages部署）
- [ ] Docker已安装
- [ ] gcloud CLI已安装

---

## ⚡ 5分钟快速部署

### 1. 准备免费数据库 (2分钟)

选择一个：
- **Neon** (推荐): https://neon.tech → 创建项目 → 获取连接字符串
- **Supabase**: https://supabase.com → 创建项目 → Database Settings
- **ElephantSQL**: https://www.elephantsql.com → 创建实例

**保存连接字符串：**
通过下方隐藏输入，将完整连接字符串保存在当前 shell 的 `DATABASE_URL` 环境变量中。

### 2. 配置 Terraform (2分钟)

```bash
cd terraform/

# 复制配置模板
cp terraform.tfvars.example terraform.tfvars

# 编辑非敏感配置；敏感值通过下方 TF_VAR_* 环境变量传入
vim terraform.tfvars
```

**最小配置：**
```hcl
gcp_project_id = "your-project-id"
# Set TF_VAR_database_url in the shell; omit this value from .tfvars.
# Set TF_VAR_django_secret_key in the shell; omit this value from .tfvars.
cors_allowed_origins = "https://yourusername.github.io"
```

**生成密钥：**
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

### 3. 部署后端到 Cloud Run (5分钟)

```bash
# 认证 GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 启用API
gcloud services enable artifactregistry.googleapis.com run.googleapis.com

# 创建基础设施
cd terraform/
terraform init
terraform apply  # 输入 yes

# 构建并推送镜像
cd ../backend
REGISTRY_URL=$(terraform -chdir=../terraform output -raw artifact_registry_url)
docker build -t $REGISTRY_URL/backend:latest .
docker push $REGISTRY_URL/backend:latest

# 获取 Cloud Run URL
terraform -chdir=../terraform output cloud_run_url
```

**保存输出的URL：** `https://maori-story-backend-xxx.run.app`

### 4. 部署前端到 GitHub Pages (3分钟)

```bash
cd frontend/

# 配置API地址
echo "VITE_API_URL=<你的Cloud Run URL>" > .env.production

# 构建
npm install
npm run build

# 部署（方法1：GitHub Actions）
# 推送代码，自动触发部署

# 或方法2：手动部署
npm install -g gh-pages
gh-pages -d dist
```

### 5. 初始化数据 (1分钟)

访问：`https://maori-story-backend-xxx.run.app/admin`

会自动创建超级用户提示，或运行：
```bash
# 创建超级用户
docker exec -it <container> python manage.py createsuperuser
```

---

## ✅ 验证部署

1. **后端测试：**
   ```bash
   curl https://maori-story-backend-xxx.run.app/health
   ```

2. **前端测试：**
   访问：`https://yourusername.github.io`

3. **Admin测试：**
   访问：`https://maori-story-backend-xxx.run.app/admin`

---

## 🔄 自动化部署（可选）

### 配置 GitHub Actions

1. **创建 GCP Service Account：**
   ```bash
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud iam service-accounts keys create key.json \
     --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

2. **添加 GitHub Secrets：**
   - 仓库 Settings → Secrets and variables → Actions
   - 添加以下secrets：
     - `GCP_PROJECT_ID`: 你的项目ID
     - `GCP_SA_KEY`: key.json的内容
     - `CLOUD_RUN_URL`: Cloud Run服务URL

3. **推送代码触发自动部署：**
   ```bash
   git push
   # 自动部署后端和前端！
   ```

---

## 💰 成本监控

### Cloud Run 免费额度
- 200万请求/月
- 180,000 vCPU-秒/月
- 360,000 GiB-秒/月

**轻度使用完全在免费额度内！**

### 查看使用情况
```bash
gcloud run services describe maori-story-backend-prod \
  --region=us-central1 \
  --format=json
```

---

## 🐛 常见问题

### Q: Cloud Run启动失败？
**A:** 检查日志：
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

常见原因：
- 数据库连接错误 → 检查 `database_url`
- 缺少环境变量 → 检查 `terraform.tfvars`

### Q: CORS错误？
**A:** 更新CORS配置：
```bash
terraform apply -var="cors_allowed_origins=https://yourusername.github.io"
```

### Q: 前端无法访问后端？
**A:** 检查：
1. `.env.production` 文件中的API URL正确
2. Cloud Run服务是公开访问
3. CORS配置包含前端域名

---

## 📚 详细文档

- **完整部署指南:** [terraform/CLOUD_RUN_DEPLOY_GUIDE.md](terraform/CLOUD_RUN_DEPLOY_GUIDE.md)
- **GCS Backend配置:** [terraform/GCS_BACKEND_SETUP.md](terraform/GCS_BACKEND_SETUP.md)
- **数据迁移:** [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

---

## 🎉 完成！

你的应用现在运行在：
- **后端**: Cloud Run（完全托管，自动扩缩容）
- **前端**: GitHub Pages（免费，全球CDN）
- **数据库**: 免费PostgreSQL服务
- **总成本**: $0-2/月

**享受几乎免费的云服务吧！** 🚀
