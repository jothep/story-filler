# Django 管理员密码管理指南

## 后台管理地址

⚠️ **Cloud Run 提供两个 URL，都可以使用**：

**选项 1（基于项目 ID，推荐）**：
```
https://maori-story-backend-454222894238.us-central1.run.app/admin/
```

**选项 2（内部标识符）**：
```
https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/
```

> 💡 规则：后端 Cloud Run URL + `/admin/`  
> 📋 两个 URL 指向同一个服务，功能完全相同

### 如何找到后端地址

**方法 1：查看 GCP Console**
1. 访问: https://console.cloud.google.com/run?project=jaskojothep
2. 点击 `maori-story-backend` 服务
3. 复制显示的 URL

**方法 2：使用 gcloud 命令**
```bash
gcloud run services describe maori-story-backend --region=us-central1 --format="value(status.url)"
```

**方法 3：查看文档**
访问 [DEPLOYMENT_URLS.md](DEPLOYMENT_URLS.md) 查看所有部署地址。

## 方法一：通过管理后台修改（最简单 ⭐）

### 前提条件
- 你能登录管理后台
- 记得当前密码

### 步骤

1. **访问管理后台**
   ```
   https://maori-story-backend-454222894238.us-central1.run.app/admin/
   ```

2. **登录**
   - 输入用户名和当前密码
   - 点击"Log in"

3. **修改密码**
   - 登录后，点击页面右上角的 **用户名**
   - 选择 **"Change password"**（修改密码）
   - 或者直接访问：
     ```
     https://maori-story-backend-454222894238.us-central1.run.app/admin/password_change/
     ```

4. **填写表单**
   - Old password（旧密码）
   - New password（新密码）
   - New password confirmation（确认新密码）
   - 点击 **"Change my password"**

5. **完成**
   - 系统会显示"Password change successful"
   - 新密码立即生效

---

## 方法二：通过本地 Django 命令（需要数据库连接）

### 前提条件
- 本地有 Django 环境
- 能连接到 Neon 数据库

### 步骤

1. **配置数据库连接**
   
   通过隐藏输入设置现有部署的环境变量（输入不会显示，也不进入命令行历史）：
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
   ```

2. **查看所有超级用户**
   ```bash
   cd backend
   python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); [print(f'用户名: {u.username}, 邮箱: {u.email}') for u in User.objects.filter(is_superuser=True)]"
   ```

3. **修改密码**
   ```bash
   python manage.py changepassword <用户名>
   ```
   
   例如：
   ```bash
   python manage.py changepassword admin
   ```

4. **按提示输入**
   - 系统会要求输入新密码两次
   - 输入时不会显示字符（这是正常的）
   - 按回车确认

---

## 方法三：通过 Python 脚本（高级）

### 使用交互式管理命令

先按方法二私下设置 `DATABASE_URL` 和 `SECRET_KEY`，再运行：

```bash
cd backend
python manage.py changepassword admin
```

根据提示输入新密码两次；不要把密码作为命令行参数。

### 或使用 Django Shell

```bash
cd backend
python manage.py shell
```

然后在 shell 中执行：
```python
from getpass import getpass
from django.contrib.auth import get_user_model

User = get_user_model()

# 查找用户
user = User.objects.get(username='admin')

# 设置新密码
user.set_password(getpass('New password: '))
user.save()

print(f"密码已修改: {user.username}")
```

---

## 方法四：如果完全忘记密码（创建新管理员）

### 步骤

1. **通过本地连接数据库**
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
   cd backend
   ```

2. **创建新的超级用户**
   ```bash
   python manage.py createsuperuser
   ```

3. **按提示输入**
   - Username（用户名）
   - Email address（邮箱，可选）
   - Password（密码）
   - Password (again)（确认密码）

4. **使用新账户登录**
   - 用新创建的账户登录管理后台
   - 登录后可以删除或禁用旧账户

---

## 密码要求

Django 默认密码验证规则：

- ✅ 至少 8 个字符
- ✅ 不能与用户名太相似
- ✅ 不能是纯数字
- ✅ 不能是常见密码

**推荐密码格式**：
- 至少 12 个字符
- 包含大小写字母、数字和特殊符号
- 使用密码管理器生成并保存独一无二的密码

---

## 常见问题

### Q1: 忘记了用户名怎么办？

通过 Django shell 查看所有超级用户：
```bash
cd backend
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); [print(u.username) for u in User.objects.filter(is_superuser=True)]"
```

### Q2: 登录后台显示 "CSRF verification failed"

- 清除浏览器 Cookie
- 确保 `CSRF_TRUSTED_ORIGINS` 包含了后台地址
- 使用无痕模式重试

### Q3: 密码修改后立即生效吗？

是的，密码修改后立即生效。下次登录需要使用新密码。

### Q4: 在哪个主机上都能访问管理后台吗？

是的！管理后台部署在 Cloud Run 上，可以从任何有网络的设备访问：
```
https://maori-story-backend-454222894238.us-central1.run.app/admin/
```

### Q5: 如何确认管理后台地址？

后台地址在代码中定义：
- 文件：`backend/maori_story_project/urls.py`
- 位置：
  ```python
  urlpatterns = [
      path("admin/", admin.site.urls),  # 这里定义了 /admin/
      path("api/", include("core.urls")),
  ]
  ```

---

## 安全建议

⚠️ **重要安全提示**：

1. **不要使用简单密码**
   - 使用密码管理器生成唯一密码，不要复用公开示例

2. **定期更换密码**
   - 建议每 3-6 个月更换一次

3. **不要分享管理员账户**
   - 为每个管理员创建单独账户

4. **启用两步验证**（可选）
   - 可以通过 Django 插件实现

5. **监控登录日志**
   - 在管理后台查看：Admin → Log entries

6. **使用 HTTPS**
   - Cloud Run 已默认启用 HTTPS ✅

---

## 快速参考

| 场景 | 推荐方法 | 难度 |
|------|---------|------|
| 能登录管理后台 | 方法一：后台直接修改 | ⭐ 简单 |
| 忘记密码，有本地环境 | 方法二：Django 命令 | ⭐⭐ 中等 |
| 完全无法访问 | 方法四：创建新管理员 | ⭐⭐⭐ 复杂 |

---

## 相关文档

- [Django 官方文档 - 用户认证](https://docs.djangoproject.com/en/stable/topics/auth/)
- [CREATE_ADMIN.md](CREATE_ADMIN.md) - 高级管理操作
- [CLOUD_RUN_ENV_VARS.md](CLOUD_RUN_ENV_VARS.md) - 环境变量配置

---

**最后更新**: 2026-04-29
