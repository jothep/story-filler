# Django Admin 管理指南

## Admin 界面概览

访问地址: https://maori-story-backend-tc2dttesfa-uc.a.run.app/admin/

登录信息: 
- 用户名: `jaskoadmin`
- 密码: (保存在 terraform.tfvars)

---

## CORE 部分详解

### 1. Application Configurations（应用配置）

**用途**: 存储全局应用设置（键值对）

**数据结构**:
```
Key (键名) | Value (值)
-----------|----------
menu_bgm_path | /media/bgm/menu_music.mp3
```

**使用场景**:
- 设置菜单背景音乐路径
- 可以添加其他全局配置（如主题颜色、默认语言等）

**前端调用**:
```javascript
// 通过 API 获取配置
fetch('/api/config/')
// 返回: { "menu_bgm_path": "/media/bgm/menu_music.mp3" }
```

**如何使用**:
1. 点击 "Add" 添加新配置
2. 输入 Key: `menu_bgm_path`
3. 输入 Value: 上传 BGM 后的路径（如 `/media/bgm/Schumann_Fantasy.mp3`）
4. 保存

---

### 2. Background Music Library（背景音乐库）

**用途**: 管理所有背景音乐文件

**数据结构**:
```
字段           | 说明
--------------|------------------
name          | 音乐名称（如 "Schumann Fantasy"）
audio_file    | 上传的音频文件 (.mp3, .wav)
created_at    | 创建时间（自动）
```

**使用场景**:
- 故事的背景音乐
- 菜单背景音乐
- 可以被多个故事共享

**关联关系**:
```
Background Music
    ↓ 一对多
Story（故事可以引用背景音乐）
```

**如何使用**:
1. 点击 "Add" 添加新音乐
2. 输入名称（如 "Adventure Theme"）
3. 点击 "Choose File" 上传音频文件
4. 保存
5. 文件自动上传到 GCS: `https://storage.googleapis.com/maori-story-media/bgm/filename.mp3`

**注意**:
- 支持格式: MP3, WAV, OGG
- 建议文件大小: < 10MB
- 音频会自动存储到 GCS bucket

---

### 3. Blank Links（填空关联）

**用途**: 将段落中的空白位置关联到单词

**数据结构**:
```
字段           | 说明
--------------|------------------
paragraph     | 所属段落
word          | 对应的单词
blank_index   | 空白位置索引（第几个空）
position      | 在段落中的位置
```

**使用场景**:
- 定义故事中哪些地方是填空
- 关联每个空对应的答案单词

**工作原理**:
```
段落: "The cat [___] on the mat."
       空白位置 0 ↑

Blank Link:
  - paragraph: 段落对象
  - word: "sat" (Word Bank 中的单词)
  - blank_index: 0
  - position: 8 (字符位置)
```

**如何使用**:
1. 先创建 Story, Paragraph, Word
2. 在段落中用 `[___]` 标记空白位置
3. 创建 Blank Link:
   - 选择 Paragraph
   - 选择 Word（正确答案）
   - 输入 blank_index（第几个空，从 0 开始）
4. 保存

**前端效果**:
- 空白位置显示为可拖拽区域
- 用户拖拽单词到空白处
- 系统验证是否为正确答案

---

### 4. Story Picture Library（故事图片库）

**用途**: 管理故事的封面图片

**数据结构**:
```
字段           | 说明
--------------|------------------
name          | 图片名称
image_file    | 上传的图片文件 (.jpg, .png)
created_at    | 创建时间
```

**使用场景**:
- 故事封面图
- 菜单中显示的故事预览图

**关联关系**:
```
Story Picture
    ↓ 一对多
Story（故事引用图片作为封面）
```

**如何使用**:
1. 点击 "Add" 添加新图片
2. 输入名称（如 "Forest Scene"）
3. 上传图片文件（推荐尺寸: 800x600px）
4. 保存
5. 图片自动上传到 GCS: `https://storage.googleapis.com/maori-story-media/story_pictures/filename.jpg`

**注意**:
- 支持格式: JPG, PNG, GIF
- 自动压缩: 超过 1920x1080 会自动缩小
- 质量优化: 自动调整为 85% 质量

---

### 5. Storys（故事）

**用途**: 管理所有故事内容（核心数据模型）

**数据结构**:
```
字段              | 说明
-----------------|------------------
title            | 故事标题（如 "The Lost Kitten"）
description      | 故事描述/简介
story_picture    | 关联的封面图片（外键 → Story Picture Library）
background_music | 关联的背景音乐（外键 → Background Music Library）
word_bank        | 单词库（多对多 → Word Bank）
created_at       | 创建时间
updated_at       | 更新时间
```

**关联关系**:
```
Story
  ├── story_picture (一对一) → Story Picture Library
  ├── background_music (一对一) → Background Music Library
  ├── paragraphs (一对多) → Paragraphs
  └── word_bank (多对多) → Word Bank
```

**如何使用**:

#### 创建新故事（完整流程）

**步骤 1: 准备素材**
1. 上传封面图片到 "Story Picture Library"
2. 上传背景音乐到 "Background Music Library"
3. 创建单词到 "Word Bank"

**步骤 2: 创建故事**
1. 点击 "Storys" → "Add"
2. 填写：
   - Title: "The Adventure"
   - Description: "A story about..."
   - Story picture: 选择已上传的图片
   - Background music: 选择已上传的音乐
   - Word bank: 勾选这个故事会用到的单词
3. 保存

**步骤 3: 添加段落**
1. 保存故事后，点击 "Add another Paragraph"
2. 或者去 "Paragraphs" 创建新段落
3. 关联到这个故事

**步骤 4: 添加填空**
1. 在段落中标记 `[___]`
2. 创建 Blank Links 关联单词

**前端效果**:
- 菜单显示故事列表（标题 + 封面图）
- 点击进入游戏界面
- 播放背景音乐
- 显示段落和填空

---

### 6. Word Bank（单词库）

**用途**: 存储所有可填空的单词及其媒体资源

**数据结构**:
```
字段              | 说明
-----------------|------------------
word_text        | 单词文本（如 "cat"）
word_translation | 单词翻译（如 "猫"）
image            | 单词图片（帮助理解，可选）
audio_file       | 单词发音音频（可选）
created_at       | 创建时间
```

**使用场景**:
- 存储所有游戏中会用到的单词
- 提供图片和音频辅助学习
- 可以被多个故事共享

**关联关系**:
```
Word Bank
  ├── (多对多) ← Storys（哪些故事用到这个单词）
  └── (一对多) ← Blank Links（这个单词在哪些空白中）
```

**如何使用**:
1. 点击 "Add" 添加新单词
2. 填写：
   - Word text: `cat`
   - Word translation: `猫` (可选)
   - Image: 上传猫的图片 (可选)
   - Audio file: 上传 "cat" 发音 (可选)
3. 保存

**前端效果**:
- 单词显示在屏幕侧边
- 点击单词播放发音
- 鼠标悬停显示图片
- 用户拖拽单词到空白处

**注意**:
- 图片会自动压缩到 800x600px
- 音频格式支持: MP3, WAV, OGG

---

## 数据关系图

```
Application Configurations（全局配置）
  - 独立存在
  - 被前端读取

Background Music Library（背景音乐库）
  ↓ 被引用
Story（故事）
  ↓ 包含
Paragraphs（段落）
  ↓ 标记空白
Blank Links（填空关联）
  ↓ 关联
Word Bank（单词库）

Story Picture Library（图片库）
  ↓ 被引用
Story（故事）
```

---

## 完整创建流程示例

### 目标：创建一个名为 "The Cat Story" 的故事

#### 第 1 步：上传媒体资源

1. **上传背景音乐**
   - 进入 "Background Music Library"
   - 点击 "Add"
   - Name: `Gentle Piano`
   - Audio file: 上传 `gentle_piano.mp3`
   - 保存

2. **上传故事封面**
   - 进入 "Story Picture Library"
   - 点击 "Add"
   - Name: `Cat Cover`
   - Image file: 上传 `cat_cover.jpg`
   - 保存

3. **创建单词**
   - 进入 "Word Bank"
   - 添加单词 1:
     - Word text: `cat`
     - Word translation: `猫`
     - Image: 上传 cat.jpg
     - Audio file: 上传 cat.mp3
   - 添加单词 2:
     - Word text: `mat`
     - Word translation: `垫子`
     - Image: 上传 mat.jpg
   - 添加单词 3:
     - Word text: `sat`
     - Word translation: `坐`
   - 保存所有

#### 第 2 步：创建故事

1. 进入 "Storys" → "Add"
2. 填写：
   ```
   Title: The Cat Story
   Description: A simple story about a cat
   Story picture: Cat Cover (选择刚才上传的)
   Background music: Gentle Piano (选择刚才上传的)
   Word bank: 勾选 cat, mat, sat
   ```
3. 保存

#### 第 3 步：添加段落

**方法 A: 在故事编辑页面添加**
1. 保存故事后，页面底部显示 "Paragraphs"
2. 点击 "Add another Paragraph"
3. 填写：
   ```
   Content: "The [___] [___] on the [___]."
   Order: 1
   ```
4. 保存

**方法 B: 单独创建段落**
1. 返回首页 → (会看到 "Paragraphs" 选项)
2. 点击 "Add"
3. 选择 Story: "The Cat Story"
4. 填写 Content 和 Order
5. 保存

#### 第 4 步：创建填空关联

1. 进入 "Blank Links" → "Add"
2. 创建第一个空（cat）:
   ```
   Paragraph: 选择刚才创建的段落
   Word: cat
   Blank index: 0
   Position: 4
   ```
3. 创建第二个空（sat）:
   ```
   Paragraph: 同上
   Word: sat
   Blank index: 1
   Position: 9
   ```
4. 创建第三个空（mat）:
   ```
   Paragraph: 同上
   Word: mat
   Blank index: 2
   Position: 18
   ```
5. 保存所有

#### 第 5 步：配置菜单 BGM（可选）

1. 进入 "Application Configurations" → "Add"
2. 填写：
   ```
   Key: menu_bgm_path
   Value: /media/bgm/gentle_piano.mp3
   ```
   (从 Background Music Library 复制路径)
3. 保存

#### 第 6 步：测试

1. 访问前端: https://jothep.github.io (部署后)
2. 应该看到：
   - 菜单显示 "The Cat Story" + 封面图
   - 背景播放 Gentle Piano
   - 点击进入故事
   - 看到段落: "The ___ ___ on the ___."
   - 侧边显示: cat, mat, sat（带图片和发音）
   - 拖拽单词到空白处
   - 完成后显示 "Story Complete!"

---

## 常见问题

### Q1: 为什么要分开 "Background Music Library" 和直接在 Story 里上传？

**A**: 
- **复用**: 多个故事可以共享同一首音乐
- **管理方便**: 统一查看所有音频资源
- **存储优化**: 不会重复存储相同文件

### Q2: Blank Links 的 blank_index 和 position 有什么区别？

**A**:
- `blank_index`: 第几个空（0, 1, 2...）
- `position`: 在文本中的字符位置（用于前端定位）

示例:
```
"The [___] is [___]."
     ↑ 0        ↑ 1      ← blank_index
     ↑ 4        ↑ 13     ← position
```

### Q3: Word Bank 的图片和音频是必填吗？

**A**: 
- **不必填**，但强烈建议添加
- 图片: 帮助用户理解单词含义（尤其是学习新语言）
- 音频: 教授正确发音

### Q4: 如何修改已发布的故事？

**A**:
1. 进入 "Storys" → 点击故事名称
2. 修改任何字段
3. 保存
4. 前端会立即看到更新（API 实时读取）

### Q5: 删除 Story 会删除关联的 Paragraph 吗？

**A**:
- **会** - 段落会被删除（级联删除）
- **不会** - Word Bank 不会被删除（多对多关系）
- **不会** - 图片和音乐不会被删除（可能被其他故事使用）

### Q6: 如何批量导入单词？

**A**: 
目前只能手动添加。未来可以考虑：
1. 通过 Django 管理命令导入 CSV
2. 使用 Django REST API 批量创建

---

## 字段验证规则

### Story Picture & Background Music
- **文件大小**: 
  - 图片: 最大 10MB
  - 音频: 最大 20MB
- **格式**:
  - 图片: JPG, PNG, GIF
  - 音频: MP3, WAV, OGG

### Word Bank
- **图片**: 最大 10MB, 自动压缩到 800x600px
- **音频**: 最大 20MB

### Story
- **Title**: 最大 200 字符, 必填
- **Description**: 无限制, 可选

### Paragraph
- **Content**: 无限制, 必填
- **Order**: 数字, 决定段落顺序

---

## 最佳实践

### 1. 命名规范

**推荐**:
```
Background Music: "gentle-piano", "adventure-theme"
Story Picture: "forest-scene", "ocean-cover"
Word: 小写单词本身 "cat", "dog"
```

**避免**:
```
Background Music: "bgm1", "music"
Story Picture: "img001", "pic"
Word: "Word1", "WORD"
```

### 2. 文件组织

**建议结构**:
```
GCS Bucket: maori-story-media/
├── bgm/
│   ├── gentle-piano.mp3
│   └── adventure-theme.mp3
├── story_pictures/
│   ├── forest-scene.jpg
│   └── ocean-cover.jpg
└── word_images/
    ├── cat.jpg
    └── dog.jpg
```

### 3. 内容创建顺序

1. ✅ 先创建 Word Bank（单词库）
2. ✅ 上传 Background Music & Story Pictures
3. ✅ 创建 Story
4. ✅ 添加 Paragraphs
5. ✅ 最后创建 Blank Links

**为什么**？因为后续步骤依赖前面的资源。

### 4. 测试流程

每次创建新故事后：
1. 检查 API: `curl https://.../api/stories/`
2. 验证数据完整（title, picture, music 都有）
3. 检查 Word Bank 是否正确关联
4. 在前端测试游戏流程

---

## 数据备份建议

定期备份数据库内容：

```bash
# 导出所有数据
python manage.py dumpdata core > backup_$(date +%Y%m%d).json

# 仅导出故事
python manage.py dumpdata core.Story > stories_backup.json

# 恢复数据
python manage.py loaddata backup.json
```

**注意**: 备份不包含媒体文件（图片/音频），需要单独备份 GCS bucket：

```bash
gsutil -m cp -r gs://maori-story-media/* ./media_backup/
```

---

## 权限管理

### 超级用户 (Superuser)
- 可以访问所有功能
- 可以添加/删除其他用户
- 当前账号: `jaskoadmin`

### 普通管理员 (Staff)
可以创建普通管理员账号：
1. 进入 "Users" → "Add"
2. 勾选 "Staff status"
3. 设置权限（哪些模型可以增删改查）

### 权限建议
- **内容编辑**: 只给 Story, Paragraph, Word Bank 权限
- **媒体管理**: 只给 Picture, Music 权限
- **系统配置**: 只有超级用户

---

## 总结

### 核心模型关系
```
Story（故事）
  ├─ 引用 Story Picture（封面）
  ├─ 引用 Background Music（BGM）
  ├─ 包含多个 Paragraph（段落）
  └─ 关联多个 Word（单词库）

Paragraph（段落）
  └─ 通过 Blank Link 关联 Word（填空）

Application Configuration（全局配置）
  └─ 独立配置项（如菜单BGM）
```

### 最小可用内容
要让应用工作，至少需要：
1. ✅ 1 个 Story（带 title 和 description）
2. ✅ 1 个 Paragraph（带内容和 `[___]` 标记）
3. ✅ 1 个 Word（对应答案）
4. ✅ 1 个 Blank Link（关联空白和单词）

图片、音频、配置都是**可选的**，但会提升用户体验。
