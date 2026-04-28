# 创建或重置 Django Admin 密码

## 如果你在本地有数据库访问权限

### 方法 1：本地运行 Django 管理命令

如果你能本地连接到 Neon 数据库：

```bash
cd backend

# 列出所有超级用户
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); [print(f'{u.username} - {u.email}') for u in User.objects.filter(is_superuser=True)]"

# 修改密码
python manage.py changepassword <username>
```

### 方法 2：创建新的超级用户

```bash
cd backend
python manage.py createsuperuser
```

## 如果你没有本地访问权限

### 通过 Cloud Run Jobs（推荐）

1. 构建包含管理脚本的 Docker 镜像
2. 创建 Cloud Run Job 执行命令
3. 运行 Job 来修改密码

示例：

```bash
# 创建一个一次性的 Cloud Run Job
gcloud run jobs create reset-admin-password \
  --image=us-central1-docker.pkg.dev/jaskojothep/maori-story/backend:latest \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY" \
  --command="python,manage.py,changepassword,admin"

# 执行 Job（交互式）
gcloud run jobs execute reset-admin-password --region=us-central1 --wait
```

## 当前管理员信息

要查看当前的管理员账户，登录 Django Admin 后：
- URL: https://maori-story-backend-454222894238.us-central1.run.app/admin/
- 导航到: Authentication and Authorization → Users
- 筛选: Staff status = Yes 或 Superuser status = Yes

## 安全提醒

⚠️ **不要在代码中硬编码密码**
⚠️ **定期更换管理员密码**
⚠️ **使用强密码（至少 12 位，包含字母、数字、符号）**
⚠️ **不要在公共场所登录管理后台**

## 临时访问（紧急情况）

如果你完全无法访问后台，可以：

1. 临时禁用身份验证（仅用于调试）
2. 登录后立即创建新管理员
3. 重新启用身份验证

**但这不推荐用于生产环境！**
