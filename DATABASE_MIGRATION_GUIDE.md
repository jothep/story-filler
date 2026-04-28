# 数据库迁移指南

## 什么是数据库迁移（Migration）？

### 简单理解

```
Django models.py (Python 代码)
    ↓ makemigrations (生成迁移文件)
migrations/0001_initial.py (SQL 操作指令)
    ↓ migrate (执行 SQL)
PostgreSQL 数据库 (实际的表和字段)
```

**类比**:
- **models.py** = 建筑设计图（代码）
- **迁移文件** = 施工指令书（如何从旧版本改到新版本）
- **数据库** = 实际的建筑（存储数据的表）

---

## Django 迁移机制详解

### 1. 迁移文件 (Migration Files)

**位置**: `backend/core/migrations/`

```
backend/core/migrations/
├── __init__.py
├── 0001_initial.py           # 初始表结构
├── 0002_add_word_image.py    # 添加单词图片字段
└── 0003_alter_story_title.py # 修改故事标题字段
```

**作用**:
- 记录数据库结构的变化历史
- 可以前进（upgrade）或回退（downgrade）
- **应该保存到 Git**（因为是代码，不是数据）

**示例 - 0001_initial.py**:
```python
class Migration(migrations.Migration):
    dependencies = []
    
    operations = [
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
```

这相当于 SQL:
```sql
CREATE TABLE core_story (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP
);
```

---

### 2. 迁移历史表 (django_migrations)

**数据库中的记录**:
```
id | app  | name            | applied
---+------+-----------------+-------------------------
1  | core | 0001_initial    | 2026-04-28 12:00:00
2  | core | 0002_add_field  | 2026-04-28 12:05:00
```

**作用**:
- Django 记录哪些迁移已经执行过
- 防止重复执行同一个迁移
- **不保存到 Git**（这是数据库运行时状态）

---

## 什么保存到 Git？什么不保存？

### ✅ 应该保存到 Git

| 内容 | 位置 | 说明 |
|------|------|------|
| **迁移文件** | `backend/core/migrations/*.py` | 数据库结构变更历史 |
| **模型定义** | `backend/core/models.py` | 表结构的代码表示 |
| **初始数据** | `backend/core/fixtures/*.json` | 示例/默认数据（可选）|

### ❌ 不应该保存到 Git

| 内容 | 位置 | 说明 |
|------|------|------|
| **实际数据** | Neon 数据库 | 用户上传的内容、故事、图片 |
| **迁移历史** | `django_migrations` 表 | 运行时状态 |
| **数据库密码** | 环境变量 | 敏感信息 |
| **超级用户密码** | 数据库 `auth_user` 表 | 加密存储 |

---

## 你的当前情况

### 架构

```
你的电脑 (本地)
    ↓ 运行 migrate
Neon PostgreSQL (远程)
    ← 创建表结构
    
Cloud Run 容器
    ↓ 连接到
Neon PostgreSQL (同一个)
    ← 读取已有的表
```

**关键点**:
- Neon 数据库是**外部服务**，独立于 Cloud Run
- 迁移只需运行**一次**（不管是本地还是Cloud Run）
- 一旦迁移完成，所有连接到这个数据库的服务都能看到表

---

## 执行迁移的三种方式

### 方案 A: 本地运行（推荐）⭐

**优点**:
- 直接看到输出和错误
- 可以交互式创建超级用户
- 调试方便

**步骤**:

```bash
# 1. 进入后端目录
cd backend

# 2. 设置环境变量（从 terraform.tfvars 获取）
export DATABASE_URL="postgresql://user:${DB_PASSWORD}@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"
export SECRET_KEY="你的Django密钥"

# 3. 运行迁移
python manage.py migrate

# 输出示例：
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, core, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   Applying admin.0001_initial... OK
#   Applying core.0001_initial... OK
#   Applying sessions.0001_initial... OK

# 4. 创建超级用户
python manage.py createsuperuser

# 交互式输入：
# Username: admin
# Email: your@email.com
# Password: ******** (不会显示)
# Password (again): ********
# Superuser created successfully.
```

**密码处理**:
- 密码通过命令行交互式输入
- Django 自动加密存储到数据库（bcrypt hash）
- **不会**出现在任何文件中
- **不会**保存到 Git

---

### 方案 B: Cloud Run Jobs

**优点**:
- 不需要本地 Python 环境
- 使用生产环境配置

**缺点**:
- `createsuperuser` 无法交互式输入密码

**步骤**:

```bash
# 1. 创建迁移 Job
gcloud run jobs create migrate-db \
  --image=us-central1-docker.pkg.dev/jaskojothep/maori-story/backend:latest \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=你的Neon URL,SECRET_KEY=你的密钥" \
  --command=python \
  --args="manage.py,migrate" \
  --project=jaskojothep

# 2. 执行迁移
gcloud run jobs execute migrate-db --region=us-central1

# 3. 创建超级用户（需要用脚本）
gcloud run jobs create create-superuser \
  --image=... \
  --set-env-vars="DATABASE_URL=...,SECRET_KEY=...,DJANGO_SUPERUSER_USERNAME=admin,DJANGO_SUPERUSER_EMAIL=admin@example.com,DJANGO_SUPERUSER_PASSWORD=临时密码" \
  --command=python \
  --args="manage.py,createsuperuser,--noinput"
```

**问题**: 密码必须通过环境变量传递（安全风险）

---

### 方案 C: 自动化脚本

创建一个一次性使用的管理脚本：

```python
# backend/create_admin.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maori_story_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password=os.environ['ADMIN_PASSWORD']
    )
    print("Superuser created")
else:
    print("Superuser already exists")
```

```bash
export ADMIN_PASSWORD="你的密码"
python create_admin.py
```

**注意**: `create_admin.py` 不要提交到 Git！

---

## 迁移后的状态

### 数据库中创建的表

```sql
-- Django 系统表
django_migrations         -- 迁移历史
django_content_type       -- 模型注册
django_session            -- 会话
auth_user                 -- 用户（包括超级用户）
auth_group                -- 用户组
auth_permission           -- 权限

-- 你的应用表
core_story                -- 故事
core_paragraph            -- 段落
core_word                 -- 单词
core_blanklink            -- 填空关联
core_backgroundmusic      -- 背景音乐
core_storypicture         -- 故事图片
core_appconfig            -- 应用配置
```

### 检查迁移状态

```bash
# 查看所有迁移
python manage.py showmigrations

# 输出：
# core
#  [X] 0001_initial
#  [X] 0002_add_word_image
#  [ ] 0003_pending_migration  # 未执行

# 查看数据库中的表
psql "$DATABASE_URL" -c "\dt"
```

---

## 数据迁移和备份策略

### 场景 1: 迁移到另一个数据库

**方法 A - Django dumpdata/loaddata**:

```bash
# 1. 从旧数据库导出
python manage.py dumpdata core > backup.json

# 2. 切换到新数据库
export DATABASE_URL="新数据库URL"

# 3. 运行迁移（创建表结构）
python manage.py migrate

# 4. 导入数据
python manage.py loaddata backup.json
```

**优点**: Django 原生支持，跨数据库兼容  
**缺点**: 大数据量较慢，不包含媒体文件

---

**方法 B - PostgreSQL pg_dump**:

```bash
# 1. 备份整个数据库
pg_dump "$OLD_DATABASE_URL" > backup.sql

# 2. 恢复到新数据库
psql "$NEW_DATABASE_URL" < backup.sql
```

**优点**: 快速，完整备份  
**缺点**: 只适用于 PostgreSQL

---

### 场景 2: 迁移后端服务（Cloud Run → 其他）

```
旧架构:
Cloud Run (容器A) → Neon DB
                     ↑
GCS Bucket (媒体文件)

新架构:
新服务器 (容器B) → Neon DB (同一个)
                    ↑
GCS Bucket (同一个)
```

**迁移步骤**:
1. 新服务器使用相同的 `DATABASE_URL`
2. 新服务器使用相同的 `GS_BUCKET_NAME`
3. 运行 `python manage.py migrate`（Django 会检测已有表，跳过）
4. 直接启动服务

**关键**: 数据库和存储都是外部的，服务只是客户端

---

### 场景 3: 数据库完全迁移（Neon → 另一个 PostgreSQL）

```bash
# 1. 备份数据
pg_dump "$NEON_URL" > full_backup.sql

# 2. 新数据库运行迁移
export DATABASE_URL="新PostgreSQL URL"
python manage.py migrate

# 3. 恢复数据（跳过 django_migrations 表）
psql "$NEW_DATABASE_URL" < full_backup.sql
```

**或使用 Django 方式**:
```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > data.json
python manage.py loaddata data.json
```

---

## 敏感信息管理

### 超级用户密码

**存储位置**: 数据库 `auth_user` 表

**存储格式**: 
```
PASSWORD_HASH_OMITTED
```

**特点**:
- ✅ 单向加密，无法反向解密
- ✅ 即使数据库泄露，密码也是安全的
- ❌ 如果忘记密码，只能重置

**重置密码**:
```bash
python manage.py changepassword admin
```

---

### 数据库连接字符串

**当前位置**: `terraform/terraform.tfvars` (gitignored)

**建议**:
1. **不要硬编码**到任何提交到 Git 的文件
2. 使用环境变量
3. 开发环境用 `.env` 文件（gitignored）
4. 生产环境用 Terraform/Secret Manager

**示例 .gitignore**:
```
terraform/terraform.tfvars
backend/.env
**/*password*
**/*secret*
```

---

## 最佳实践总结

### ✅ 推荐做法

1. **迁移文件提交到 Git**
   ```bash
   git add backend/core/migrations/
   git commit -m "Add initial database schema"
   ```

2. **本地运行迁移**
   ```bash
   python manage.py migrate
   ```

3. **交互式创建超级用户**
   ```bash
   python manage.py createsuperuser
   # 密码不会出现在任何地方
   ```

4. **定期备份数据**
   ```bash
   python manage.py dumpdata core > backup_$(date +%Y%m%d).json
   ```

5. **版本控制迁移**
   - 每次修改 models.py 后运行 `makemigrations`
   - 迁移文件命名清晰
   - 测试迁移可以正向和反向执行

---

### ❌ 避免做法

1. ❌ 在生产环境手动修改数据库结构
2. ❌ 删除旧的迁移文件（会导致历史丢失）
3. ❌ 在代码中硬编码数据库密码
4. ❌ 将 `terraform.tfvars` 或 `.env` 提交到 Git
5. ❌ 直接在数据库中创建超级用户（绕过 Django）

---

## 立即行动方案

基于你的情况，推荐执行：

### 步骤 1: 本地运行迁移

```bash
cd backend

# 从 terraform.tfvars 获取这两个值
export DATABASE_URL="postgresql://..."
export SECRET_KEY="..."

python manage.py migrate
```

**预期输出**:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, core, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ... (更多)
  Applying core.0001_initial... OK
```

---

### 步骤 2: 创建超级用户

```bash
python manage.py createsuperuser
```

**交互输入**:
- Username: `admin`（或你想要的）
- Email: `your@email.com`
- Password: `<输入密码>`（不会显示）

**密码安全性**:
- 密码只在内存中存在
- Django 立即加密存储到数据库
- 命令行历史不会记录密码
- 不会保存到任何文件

---

### 步骤 3: 验证

```bash
# 测试 API
curl https://maori-story-backend-tc2dttesfa-uc.a.run.app/api/stories/

# 应该返回 [] (空数组，而不是错误)

# 访问 Admin
open https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/
# 用刚创建的账号登录
```

---

### 步骤 4: 提交迁移文件（如果有新的）

```bash
git add backend/core/migrations/
git commit -m "Database schema migrations"
git push
```

**注意**: 只提交 `.py` 迁移文件，不提交 `.pyc` 编译文件

---

## 未来维护

### 添加新字段

```python
# models.py
class Story(models.Model):
    title = models.CharField(max_length=200)
    new_field = models.CharField(max_length=100, default='')  # 新字段
```

```bash
# 生成迁移文件
python manage.py makemigrations

# 输出：
# Migrations for 'core':
#   core/migrations/0004_story_new_field.py
#     - Add field new_field to story

# 执行迁移
python manage.py migrate

# 提交到 Git
git add backend/core/migrations/0004_story_new_field.py
git commit -m "Add new_field to Story model"
```

---

## 故障恢复

### 问题: 迁移执行到一半失败

```bash
# 查看当前状态
python manage.py showmigrations

# 标记迁移为未执行（回退）
python manage.py migrate core 0003  # 回退到 0003

# 修复问题后重新执行
python manage.py migrate
```

---

### 问题: 忘记超级用户密码

```bash
python manage.py changepassword admin
```

---

### 问题: 数据库被清空

```bash
# 从备份恢复
python manage.py loaddata backup.json

# 或从 SQL 备份
psql "$DATABASE_URL" < backup.sql
```

---

## 总结

| 操作 | 保存到 Git？ | 何时执行 | 频率 |
|------|-------------|---------|------|
| 迁移文件 `.py` | ✅ 是 | 修改 models.py 后 | 每次变更 |
| 运行 `migrate` | ❌ 否 | 迁移文件更新后 | 按需 |
| 创建超级用户 | ❌ 否 | 初始化数据库时 | 一次 |
| 数据备份 `.json` | ❌ 否 | 定期备份 | 每周/每月 |
| 密码 | ❌ 否 | 永远不保存 | N/A |

**记住**: 
- **代码（迁移文件）→ Git**
- **数据（实际内容）→ 数据库备份**
- **密码 → 只在加密后的数据库中**
