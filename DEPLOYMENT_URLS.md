# 部署 URL 地址

本文档记录项目所有重要的访问地址。

## 生产环境

### 前端（GitHub Pages）
- **应用地址**: https://jothep.github.io/maori-story-fill/
- **部署平台**: GitHub Pages
- **部署触发**: 推送到 `main` 分支的 `frontend/**` 文件

### 后端（Google Cloud Run）

⚠️ **Cloud Run 提供两个 URL，都可以使用**：

**格式 1（基于项目 ID，推荐）**：
- **API 地址**: https://maori-story-backend-454222894238.us-central1.run.app
- **管理后台**: https://maori-story-backend-454222894238.us-central1.run.app/admin/
- **API 文档**: https://maori-story-backend-454222894238.us-central1.run.app/api/

**格式 2（内部标识符）**：
- **API 地址**: https://maori-story-backend-tc2dttesfa-uc.a.run.app
- **管理后台**: https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/
- **API 文档**: https://maori-story-backend-tc2dttesfa-uc.a.run.app/api/

**部署信息**：
- **部署平台**: Google Cloud Run
- **服务名**: maori-story-backend
- **区域**: us-central1
- **项目 ID**: jaskojothep (454222894238)
- **部署触发**: 推送到 `main` 分支的 `backend/**` 文件

### 数据库（Neon）
- **类型**: PostgreSQL
- **主机**: ep-restless-tree-am3e4dfx.c-5.us-east-1.aws.neon.tech
- **数据库名**: neondb
- **连接**: 通过环境变量 `DATABASE_URL`

### 存储（Google Cloud Storage）
- **存储桶**: maori-story-media
- **区域**: us-central1
- **访问**: https://storage.googleapis.com/maori-story-media/

## 如何获取当前后端 URL

### 方法 1：使用 gcloud 命令
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="value(status.url)"
```

### 方法 2：查看 GitHub Actions workflow 输出
1. 访问: https://github.com/jothep/maori-story-fill/actions
2. 点击最新的 "Deploy Backend to Cloud Run" workflow
3. 查看 "Show service URL" 步骤的输出

### 方法 3：在 Google Cloud Console 查看
1. 访问: https://console.cloud.google.com/run?project=jaskojothep
2. 点击 `maori-story-backend` 服务
3. URL 显示在页面顶部

## 本地开发环境

### 前端开发服务器
- **地址**: http://localhost:5173
- **启动**: `cd frontend && npm run dev`
- **API 代理**: 配置在 `frontend/vite.config.js`

### 后端开发服务器
- **地址**: http://localhost:8000
- **管理后台**: http://localhost:8000/admin/
- **启动**: `cd backend && python manage.py runserver`

## URL 路由说明

### 前端路由（React Router）
- `/` - 主页面（故事列表）
- `/story/:id` - 故事详情页

### 后端路由（Django URLs）

定义在 `backend/maori_story_project/urls.py`:
- `/admin/` - Django 管理后台（由 `django.contrib.admin` 提供）
- `/api/` - API 端点（定义在 `backend/core/urls.py`）
- `/media/` - 媒体文件（图片、音频）

API 端点详细定义在 `backend/core/urls.py`:
- `/api/stories/` - 获取故事列表
- `/api/stories/<id>/` - 获取单个故事
- `/api/config/` - 获取应用配置（BGM 等）

## 重要说明

⚠️ **Cloud Run URL 可能会变化**
- Cloud Run 的 URL 格式为: `https://<service>-<hash>-<region-code>.a.run.app`
- 重新创建服务时 URL 会改变
- **建议使用自定义域名**（可选）

⚠️ **CORS 配置**
- 后端的 `CORS_ALLOWED_ORIGINS` 必须包含前端 URL
- 当前配置在: `env-vars.yaml`
- 包含: `http://localhost:5173`, `http://localhost:8080`, `https://jothep.github.io`

## 自定义域名（可选）

如果将来想使用自定义域名:

### 前端
1. 在 GitHub Pages 设置中添加自定义域名
2. 更新 DNS 记录指向 GitHub Pages

### 后端
1. 在 Cloud Run 中映射自定义域名
2. 更新 DNS 记录
3. 更新 `CORS_ALLOWED_ORIGINS` 和 `ALLOWED_HOSTS`

## 监控和日志

### 前端
- **构建日志**: https://github.com/jothep/maori-story-fill/actions
- **浏览器控制台**: F12 打开开发者工具

### 后端
- **Cloud Run 日志**:
  ```bash
  gcloud run services logs read maori-story-backend --region=us-central1 --limit=50
  ```
- **GCP Console 日志**: https://console.cloud.google.com/logs/query?project=jaskojothep

## 快速访问链接

| 服务 | 链接 |
|------|------|
| 前端应用 | https://jothep.github.io/maori-story-fill/ |
| 后端管理 | https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/ |
| GitHub Actions | https://github.com/jothep/maori-story-fill/actions |
| Cloud Run 控制台 | https://console.cloud.google.com/run?project=jaskojothep |
| Neon 数据库控制台 | https://console.neon.tech/ |

---

**最后更新**: 2026-04-29  
**Cloud Run URL**: https://maori-story-backend-tc2dttesfa-uc.a.run.app  
**服务名**: maori-story-backend  
**区域**: us-central1
