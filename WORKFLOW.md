# Maori Story Fill - 工作流程说明

## 架构概览

```
┌─────────────────────┐
│   你（管理员）      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Django Admin       │  ← 内容管理界面（后端的一部分）
│  /admin/            │     上传故事、音乐、图片
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PostgreSQL         │  ← 数据库（Neon）
│  存储所有数据       │     故事文本、配置等
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  REST API           │  ← 后端 API（Django REST Framework）
│  /api/stories/      │     提供 JSON 数据
│  /media/...         │     提供媒体文件
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  React 前端         │  ← 用户界面
│  游戏界面           │     调用 API 获取数据
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│   玩家              │
└─────────────────────┘
```

---

## 当前问题

### ❌ 数据库未初始化

**错误信息**: `relation "core_story" does not exist`

**原因**: Neon 数据库是全新的空数据库，Django 的表结构还没有创建。

**类比**: 就像你买了一个新硬盘，但还没有格式化和创建文件系统。

---

## 完整工作流程

### 步骤 1: 初始化数据库 ⚠️ **当前卡在这里**

需要运行 Django 的数据库迁移命令，创建表结构：

```bash
python manage.py migrate
```

这会在 Neon 数据库中创建以下表：
- `core_story` - 故事表
- `core_paragraph` - 段落表
- `core_word` - 单词表
- `core_backgroundmusic` - 背景音乐表
- `core_storypicture` - 故事图片表
- `core_appconfig` - 应用配置表
- ... 等

**问题**: Cloud Run 容器启动时应该自动运行这个命令，但似乎没有成功。

---

### 步骤 2: 创建管理员账号

运行命令创建超级用户：

```bash
python manage.py createsuperuser
```

输入：
- 用户名
- 邮箱
- 密码

---

### 步骤 3: 通过 Admin 上传内容

访问: `https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/`

登录后可以：

1. **创建故事**
   - 标题
   - 描述
   - 关联图片
   - 关联背景音乐

2. **创建段落**
   - 属于哪个故事
   - 段落文本
   - 顺序

3. **创建单词（填空）**
   - 属于哪个段落
   - 单词文本
   - 单词图片
   - 位置

4. **上传媒体文件**
   - BGM 音频文件 (.mp3)
   - 故事图片 (.jpg, .png)
   - 单词图片 (.jpg, .png)

**文件存储**: 见下方详细说明 ⬇️

---

## ⚠️ 关键问题：文件存储在哪里？

### 数据库 vs 文件系统

**数据库（PostgreSQL/Neon）存储**:
- ✅ 故事文本（标题、描述）
- ✅ 段落文本
- ✅ 单词文本
- ✅ 文件路径（如 `/media/bgm/music.mp3`）
- ✅ 配置信息

**文件系统存储** (二进制文件):
- ❌ 音频文件（.mp3, .wav）
- ❌ 图片文件（.jpg, .png）
- ❌ 其他媒体文件

### 当前配置的文件流程

```
1. 你在 Django Admin 上传图片
   ↓
2. Django 接收文件，保存到 /app/media/story_pictures/image.jpg
   ↓
3. 数据库只存路径: "/media/story_pictures/image.jpg"
   ↓
4. 前端通过 API 获取: 
   {
     "story_picture": "https://maori-story-backend-.../media/story_pictures/image.jpg"
   }
   ↓
5. 浏览器访问这个 URL，Django 从 /app/media/ 读取文件返回
```

### ❌ 核心问题：Cloud Run 文件系统是临时的

**Cloud Run 特性**:
- 容器文件系统是**临时的（Ephemeral）**
- 每次以下情况文件都会丢失：
  - 容器重启（自动扩缩容）
  - 更新部署
  - 实例替换
  - 崩溃恢复

**举例**:
```
今天 10:00 - 你上传了 10 张图片 → 保存到 /app/media/
今天 12:00 - Cloud Run 自动重启容器
今天 12:01 - 所有 10 张图片都不见了！❌
```

**为什么会这样？**

Cloud Run 设计用于**无状态应用**：
- 容器可以随时启动/停止/替换
- 不应该依赖本地文件系统存储数据
- 应该使用外部存储服务

### ✅ 解决方案：使用 Google Cloud Storage (GCS)

**架构改为**:

```
Django Admin (上传文件)
    ↓
Google Cloud Storage Bucket
    ↓
前端直接访问 GCS URL
```

**流程**:

```
1. 你在 Django Admin 上传图片
   ↓
2. Django 通过 django-storages 上传到 GCS bucket
   ↓
3. GCS 返回公开 URL: https://storage.googleapis.com/bucket/story_pictures/image.jpg
   ↓
4. 数据库存这个 URL
   ↓
5. 前端通过 API 获取这个 URL
   ↓
6. 浏览器直接从 GCS 加载文件（不经过 Django）
```

**优点**:
- ✅ 文件永久保存，不会丢失
- ✅ 不占用 Cloud Run 容器空间
- ✅ CDN 加速，更快
- ✅ 免费额度：5 GB 存储 + 5000 次操作/月

**缺点**:
- ❌ 你刚删除了 `django-storages` 和 `boto3`！
- ❌ 需要配置 GCS bucket 和权限

### GitHub Pages 不存储媒体文件

**明确一点**:

```
❌ 错误理解：
GitHub Pages (前端) 存储图片/音频

✅ 正确架构：
GitHub Pages (前端代码) 
    → 调用 Cloud Run API 
    → 获取 GCS URL 
    → 浏览器从 GCS 加载媒体文件
```

**GitHub Pages 只托管**:
- HTML 文件
- CSS 文件
- JavaScript 文件
- React 编译后的静态文件

**不托管**:
- 故事图片
- BGM 音频
- 用户上传的内容

---

### 步骤 4: 前端访问 API

前端代码会调用这些 API：

```javascript
// 获取所有故事
fetch('https://maori-story-backend-tc2dttesfa-uc.a.run.app/api/stories/')
  .then(res => res.json())
  .then(stories => {
    // stories = [
    //   {
    //     id: 1,
    //     title: "故事标题",
    //     description: "故事描述",
    //     story_picture: "https://.../media/story_pictures/image.jpg",
    //     background_music: "https://.../media/bgm/music.mp3",
    //     paragraphs: [...]
    //   }
    // ]
  })

// 获取单个故事详情
fetch('https://maori-story-backend-tc2dttesfa-uc.a.run.app/api/stories/1/')
  .then(res => res.json())
  .then(story => {
    // 包含完整的段落、单词、填空信息
  })

// 获取应用配置（如菜单BGM）
fetch('https://maori-story-backend-tc2dttesfa-uc.a.run.app/api/config/')
  .then(res => res.json())
  .then(config => {
    // config = {
    //   menu_bgm_path: "/media/bgm/menu.mp3"
    // }
  })
```

---

## 需要解决的问题

### 1. ✅ 已完成
- GCP Artifact Registry 创建
- Cloud Run 服务部署
- Docker 镜像构建和推送
- 前端环境配置文件创建

### 2. ⚠️ 待解决 - 数据库迁移

**方案 A**: 通过 Cloud Run Jobs 运行迁移（推荐）

```bash
gcloud run jobs create migrate-db \
  --image=us-central1-docker.pkg.dev/jaskojothep/maori-story/backend:latest \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=你的Neon数据库URL,SECRET_KEY=你的密钥" \
  --command=python \
  --args="manage.py,migrate"

gcloud run jobs execute migrate-db --region=us-central1
```

**方案 B**: 检查为什么容器启动时迁移没有运行

Dockerfile CMD 是 `gunicorn ...`，没有在启动前运行 `migrate`。

**方案 C**: 本地连接 Neon 运行迁移

```bash
# 设置环境变量
export DATABASE_URL="你的Neon数据库URL"
export SECRET_KEY="你的密钥"

# 运行迁移
cd backend
python manage.py migrate
```

---

### 3. ⚠️ 待解决 - 创建超级用户

迁移完成后，需要创建管理员账号。

---

### 4. ❌ **致命问题** - 媒体文件持久化

**问题**: Cloud Run 容器重启后，上传的媒体文件会丢失。

**当前状态**: 
- 你删除了 `django-storages` 和 `boto3`
- Django 配置为本地存储: `MEDIA_ROOT = /app/media`
- Cloud Run 容器文件系统是临时的
- **结果**: 上传的文件会随机丢失

**解决方案 A - 使用 GCS（推荐）**:

1. 恢复依赖：
   ```bash
   # backend/requirements.txt
   django-storages==1.14.4
   google-cloud-storage==2.10.0  # 不是 boto3，用 GCS SDK
   ```

2. 创建 GCS bucket：
   ```bash
   gsutil mb -p jaskojothep -l us-central1 gs://maori-story-media/
   gsutil iam ch allUsers:objectViewer gs://maori-story-media/
   ```

3. 配置 Django:
   ```python
   # settings.py
   DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
   GS_BUCKET_NAME = 'maori-story-media'
   GS_DEFAULT_ACL = 'publicRead'
   MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
   ```

4. 更新 Terraform 添加环境变量

**解决方案 B - 接受临时存储（测试用）**:

- 仅用于开发/测试
- 生产环境**必须**使用 GCS
- 每次更新容器都需要重新上传所有文件

**解决方案 C - 使用 Cloud Run Volume（有限）**:

- Cloud Run 支持挂载 GCS bucket 作为 volume
- 但有性能限制，不推荐用于频繁读写

---

### 5. 🔜 前端部署

配置完成后：

```bash
cd frontend
npm install
npm run build
# 部署到 GitHub Pages
```

---

## 当前状态总结

| 组件 | 状态 | 说明 |
|------|------|------|
| GCP Artifact Registry | ✅ 完成 | 镜像仓库已创建 |
| Cloud Run 服务 | ✅ 运行中 | 但数据库未初始化 |
| Neon 数据库 | ⚠️ 空数据库 | 需要运行迁移 |
| Django Admin | ⚠️ 不可用 | 等待迁移和超级用户 |
| REST API | ❌ 报错 | 缺少数据库表 |
| 前端 | 🔜 未部署 | 等待后端就绪 |
| 媒体文件存储 | ⚠️ 临时的 | 容器重启会丢失 |

---

## 下一步行动

### 优先级排序

#### 🔥 P0 - 必须立即解决

1. **数据库迁移** - 没有表结构，API 完全无法工作
2. **媒体文件存储** - 决定是否添加 GCS 支持

#### ⚡ P1 - 迁移后立即执行

3. **创建超级用户** - 否则无法登录 Admin
4. **上传测试内容** - 验证整个流程

#### 📦 P2 - 功能就绪后

5. **部署前端** - 后端 API 正常后执行
6. **配置 CORS** - 确保前端能调用 API

### 推荐决策路径

**如果你想快速测试（不在乎文件丢失）**:
```
1. 运行数据库迁移
2. 创建超级用户
3. 接受文件临时存储的风险
4. 上传内容测试
5. 部署前端
```

**如果你要生产部署（推荐）**:
```
1. 恢复 django-storages 依赖
2. 配置 GCS bucket
3. 更新 Django 配置
4. 重新构建和部署镜像
5. 运行数据库迁移
6. 创建超级用户
7. 上传内容到 GCS
8. 部署前端
```

### 文件存储对比表

| 方案 | 优点 | 缺点 | 成本 |
|------|------|------|------|
| **本地存储** `/app/media/` | 简单，无需配置 | 文件会丢失！❌ | $0 |
| **GCS** | 持久化，CDN 加速，可靠 | 需要配置 | 免费额度内 $0 |
| **Cloud Run Volume** | 集成方便 | 性能限制，不适合媒体文件 | $0 |

### 我的建议

**现在立即做**:
1. 运行数据库迁移（让 API 能工作）
2. 创建超级用户

**短期（今天/明天）做**:
3. 决定是否添加 GCS 支持

**原因**: 
- 数据库迁移是阻塞性问题，API 完全不可用
- 文件存储可以后续迁移（虽然会重新上传文件）
- 先让系统跑起来，再优化架构

你想先解决哪个问题？我推荐先运行数据库迁移。
