# 后端公开访问配置说明

## 为什么你能在网上直接访问后端？

你访问的URL: `https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/`

### 架构图

```
你的浏览器
    ↓ HTTPS 请求
Google Cloud Load Balancer (自动配置)
    ↓
Cloud Run 容器 (后端 Django)
    ↓
Neon PostgreSQL 数据库
```

---

## 1. Cloud Run 自动提供公网访问

### 配置位置: `terraform/main.tf`

```hcl
resource "google_cloud_run_v2_service" "backend" {
  name     = "maori-story-backend"
  location = "us-central1"
  
  # 默认配置 - 接受所有流量
  # ingress = "INGRESS_TRAFFIC_ALL"  (默认值，未显式设置)
}
```

**说明**:
- Cloud Run 默认创建**公开 HTTPS 端点**
- 自动分配域名: `*.run.app`
- 自动配置 SSL 证书（Let's Encrypt）
- 自动负载均衡

**ingress 选项**:
- `INGRESS_TRAFFIC_ALL` (默认) - 接受所有互联网流量
- `INGRESS_TRAFFIC_INTERNAL_ONLY` - 仅内部 VPC 访问
- `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` - 仅通过内部负载均衡器

---

## 2. IAM 公开访问权限

### 配置位置: `terraform/main.tf`

```hcl
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"  # ← 关键配置
}
```

**说明**:
- `member = "allUsers"` - 允许任何人调用服务
- `role = "roles/run.invoker"` - 调用权限
- 没有这个配置，访问会返回 403 Forbidden (GCP 层面)

**替代方案**:
```hcl
# 仅允许特定用户
member = "user:your@email.com"

# 仅允许服务账号
member = "serviceAccount:name@project.iam.gserviceaccount.com"

# 仅允许认证用户
member = "allAuthenticatedUsers"
```

---

## 3. Django ALLOWED_HOSTS 配置

### 配置位置: `backend/maori_story_project/settings.py`

```python
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
```

### 当前 Terraform 配置: `terraform/main.tf`

```hcl
env {
  name  = "ALLOWED_HOSTS"
  value = "*"  # ← 允许所有域名
}
```

**说明**:
- Django 的主机头验证
- `*` = 接受任何域名（开发方便，生产环境建议指定）
- 如果不匹配，返回 400 Bad Request

**生产环境建议**:
```hcl
value = "maori-story-backend-tc2dttesfa-uc.a.run.app,yourdomain.com"
```

---

## 4. CORS 跨域配置

### 配置位置: `backend/maori_story_project/settings.py`

```python
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]
)
```

### 当前 Terraform 配置:

```hcl
env {
  name  = "CORS_ALLOWED_ORIGINS"
  value = "https://jothep.github.io"
}
```

**说明**:
- 允许前端（GitHub Pages）调用后端 API
- 浏览器的跨域安全限制
- 只影响浏览器中的 JavaScript 请求
- 不影响直接访问（如 curl 或浏览器直接打开）

---

## 当前 403 错误原因

**错误信息**: `Forbidden (403) - CSRF verification failed. Request aborted.`

**原因**: Django 的 CSRF（跨站请求伪造）保护

### 问题分析

```
浏览器访问: https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/
    ↓
Django 检查: Referer 头和 CSRF token
    ↓
不匹配 → 403 错误
```

### 为什么会失败？

Django 默认安全设置需要以下之一：
1. **CSRF_TRUSTED_ORIGINS** - 信任的源域名
2. 有效的 CSRF token（从表单获取）

---

## 解决方案

### 方案 1: 添加 CSRF_TRUSTED_ORIGINS（推荐）

**修改**: `backend/maori_story_project/settings.py`

```python
# 在 CORS_ALLOWED_ORIGINS 之后添加
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in env.list("ALLOWED_HOSTS", default=["localhost"])
    if host not in ["*", "localhost", "127.0.0.1"]
]

# 或者直接指定
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://maori-story-backend-tc2dttesfa-uc.a.run.app"]
)
```

**Terraform 配置**:

```hcl
env {
  name  = "CSRF_TRUSTED_ORIGINS"
  value = "https://maori-story-backend-tc2dttesfa-uc.a.run.app"
}
```

---

### 方案 2: 禁用 CSRF（不推荐，仅测试）

```python
# settings.py
MIDDLEWARE = [
    # ... 其他中间件
    # "django.middleware.csrf.CsrfViewMiddleware",  # 注释掉
]
```

**风险**: 容易受到 CSRF 攻击

---

## 完整访问流程

### 场景 1: 直接访问 Admin

```
1. 浏览器输入: https://...run.app/admin/
2. DNS 解析 → GCP Load Balancer
3. Load Balancer → Cloud Run 容器
4. Cloud Run 检查 IAM 权限 (allUsers) → 通过
5. 请求到达 Django
6. Django 检查 ALLOWED_HOSTS (*) → 通过
7. Django 检查 CSRF → 失败 (当前问题)
8. 返回 403
```

**修复后**:
```
7. Django 检查 CSRF_TRUSTED_ORIGINS → 通过
8. 显示登录页面
```

---

### 场景 2: 前端调用 API

```
1. GitHub Pages (jothep.github.io)
2. JavaScript 发起请求: fetch('https://...run.app/api/stories/')
3. 浏览器检查 CORS 预检 (OPTIONS 请求)
4. Django 返回 CORS 头: Access-Control-Allow-Origin
5. 浏览器允许请求
6. API 返回 JSON 数据
```

---

## 网络安全层级

### 第 1 层: GCP IAM (Cloud Run)
- **配置**: `allUsers` IAM 绑定
- **作用**: 决定谁可以调用服务
- **拒绝时**: 返回 403 (GCP 层面，看不到 Django 错误)

### 第 2 层: Django ALLOWED_HOSTS
- **配置**: `ALLOWED_HOSTS = "*"`
- **作用**: 验证 HTTP Host 头
- **拒绝时**: 返回 400 Bad Request

### 第 3 层: Django CSRF
- **配置**: `CSRF_TRUSTED_ORIGINS`
- **作用**: 防止跨站请求伪造
- **拒绝时**: 返回 403 (Django 层面，显示详细错误)

### 第 4 层: Django 用户认证
- **配置**: 登录系统
- **作用**: 验证用户身份
- **拒绝时**: 重定向到 /admin/login/

---

## 配置对比表

| 配置项 | 当前值 | 作用 | 建议 |
|--------|--------|------|------|
| **IAM member** | `allUsers` | GCP 访问控制 | 保持（需要公开） |
| **ALLOWED_HOSTS** | `*` | Django 主机验证 | 指定域名（生产） |
| **CORS_ALLOWED_ORIGINS** | `jothep.github.io` | 跨域 API 访问 | 保持 |
| **CSRF_TRUSTED_ORIGINS** | 未设置 ❌ | CSRF 保护 | 添加后端域名 |

---

## 如何限制访问？

### 场景 1: 仅允许前端访问 API

**不可行** - Cloud Run 的 IAM 是全局的，无法按路径区分

**替代方案**:
```python
# views.py - API 添加 token 验证
from rest_framework.permissions import IsAuthenticated

class StoryListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
```

---

### 场景 2: Admin 需要 VPN

**方法 1: 使用 Cloud Run ingress 限制**

```hcl
resource "google_cloud_run_v2_service" "backend" {
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
}

# 配置 Cloud Armor + Load Balancer
# 只允许特定 IP
```

**方法 2: Django IP 白名单**

```python
# settings.py
ALLOWED_IPS = ['1.2.3.4', '5.6.7.8']

# middleware.py
class IPWhitelistMiddleware:
    def __call__(self, request):
        if request.path.startswith('/admin/'):
            if request.META['REMOTE_ADDR'] not in ALLOWED_IPS:
                return HttpResponseForbidden()
```

---

### 场景 3: 完全私有部署

```hcl
# 1. 内部访问
resource "google_cloud_run_v2_service" "backend" {
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}

# 2. 移除公开权限
# 删除 google_cloud_run_v2_service_iam_member.public 资源

# 3. 通过 VPN 或 Cloud Run Proxy 访问
```

---

## 总结

**当前配置 = 完全公开**:
- ✅ 任何人可以访问 URL
- ✅ 前端可以调用 API
- ❌ CSRF 保护阻止 Admin 登录（需要修复）

**修复步骤**:
1. 添加 `CSRF_TRUSTED_ORIGINS` 配置
2. 重新部署容器
3. Admin 即可正常登录

**生产环境建议**:
1. 指定 `ALLOWED_HOSTS`（不用 `*`）
2. 配置 `CSRF_TRUSTED_ORIGINS`
3. API 添加认证（如 JWT token）
4. 考虑添加 rate limiting
5. 使用自定义域名
