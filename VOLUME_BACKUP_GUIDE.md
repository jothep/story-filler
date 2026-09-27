> **Historical implementation note — September 2026 review:** This document retains an earlier design, estimate, procedure or plan. It is not the current deployment specification, and its performance, cost, security and recovery claims have not all been revalidated. Use the [architecture index](docs/ARCHITECTURE.md) and [dated verification record](docs/verification.md) for current scope and evidence.

# Docker Volume 备份迁移指南

使用Docker Volume备份是最简单、最完整的迁移方式 - 它会完整复制整个数据库和媒体文件。

## 为什么用Volume备份？

| 对比 | Volume备份 | pg_dump + 媒体打包 |
|------|-----------|------------------|
| **操作** | 一键备份/恢复 | 需要分别操作数据库和文件 |
| **完整性** | 100%完整 | 需要确保两者同步 |
| **速度** | 快（直接复制） | 慢（需要dump和restore） |
| **简单度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 步骤1：本地创建测试数据

### 1.1 登录Django Admin

访问：http://localhost/admin

- 用户名：`admin`
- 密码：使用此前私下设置的管理员密码；如已遗忘，运行 `python manage.py changepassword admin` 并按隐藏输入提示重置。

### 1.2 创建测试内容

**添加BGM：**
1. 点击 "Background musics" → "ADD BACKGROUND MUSIC"
2. 上传MP3文件（例如：`test-bgm.mp3`）
3. 设置标题：`测试背景音乐`
4. 保存

**添加故事：**
1. 点击 "Stories" → "ADD STORY"
2. 填写标题和内容
3. 上传图片
4. 保存

**配置应用：**
1. 点击 "App configs" → "ADD APP CONFIG"
2. Key: `menu_bgm_path`
3. Value: `bgm/test-bgm.mp3`
4. 保存

### 1.3 验证数据

```bash
# 检查数据库记录
docker exec maori-dev-backend python manage.py shell -c "
from core.models import Story, BackgroundMusic
print(f'故事数量: {Story.objects.count()}')
print(f'BGM数量: {BackgroundMusic.objects.count()}')
"

# 检查媒体文件
docker exec maori-dev-backend ls -lh /app/media/bgm/
docker exec maori-dev-backend ls -lh /app/media/story_pictures/
```

---

## 步骤2：本地备份Volumes

### 2.1 运行备份脚本

```bash
cd /Users/zhuxiang/Documents/maori-story-fill
./scripts/backup-volumes.sh
```

**输出示例：**
```
=== Docker Volume 备份工具 ===
📁 备份目录: ./volume-backup-20260412-143000

📦 备份数据库 Volume...
✅ 数据库备份完成: postgres_data.tar.gz (45M)

📦 备份媒体文件 Volume...
✅ 媒体文件备份完成: media_data.tar.gz (12M)

✅ 备份完成！
📁 备份位置: ./volume-backup-20260412-143000
```

### 2.2 备份内容

```bash
# 查看备份文件
ls -lh volume-backup-20260412-143000/

# 输出：
# -rw-r--r--  postgres_data.tar.gz  (45MB - 完整的PostgreSQL数据)
# -rw-r--r--  media_data.tar.gz     (12MB - 所有上传的文件)
# -rw-r--r--  backup-info.txt       (备份信息)
```

---

## 步骤3：上传到EC2

### 方法1：使用SCP

```bash
# 打包备份目录
tar czf volume-backup.tar.gz volume-backup-20260412-143000/

# 上传到EC2
scp volume-backup.tar.gz ec2-user@your-ec2-ip:/home/ec2-user/

# 在EC2上解压
ssh ec2-user@your-ec2-ip
cd /home/ec2-user
tar xzf volume-backup.tar.gz
```

### 方法2：通过S3中转（推荐大文件）

```bash
# 本地上传到S3
aws s3 cp volume-backup-20260412-143000/ \
  s3://your-bucket/backups/volume-backup-20260412-143000/ \
  --recursive

# EC2下载
ssh ec2-user@your-ec2-ip
aws s3 cp s3://your-bucket/backups/volume-backup-20260412-143000/ \
  ./volume-backup-20260412-143000/ \
  --recursive
```

---

## 步骤4：EC2恢复Volumes

### 4.1 准备EC2环境

```bash
# SSH到EC2
ssh ec2-user@your-ec2-ip

# 进入项目目录
cd /home/ec2-user/maori-story-fill

# 确保docker-compose文件存在
ls -la docker-compose.prod.yml
```

### 4.2 运行恢复脚本

```bash
# 恢复volumes
./scripts/restore-volumes-ec2.sh ~/volume-backup-20260412-143000
```

**执行过程：**
```
=== EC2 生产环境 Volume 恢复 ===
📁 备份目录: /home/ec2-user/volume-backup-20260412-143000

⏸️  停止服务...
✅ 服务已停止

📦 准备Volumes...

📦 恢复数据库 Volume...
✅ 数据库恢复完成

📦 恢复媒体文件 Volume...
✅ 媒体文件恢复完成

🚀 启动服务...
✅ 服务已启动

🎉 恢复完成！
```

### 4.3 验证恢复

```bash
# 检查容器状态
docker-compose -f docker-compose.prod.yml ps

# 检查数据库数据
docker exec maori-backend python manage.py shell -c "
from core.models import Story, BackgroundMusic
print(f'故事数量: {Story.objects.count()}')
print(f'BGM数量: {BackgroundMusic.objects.count()}')
"

# 检查媒体文件
docker exec maori-backend ls -lh /app/media/bgm/
docker exec maori-backend ls -lh /app/media/story_pictures/
```

### 4.4 访问应用

浏览器访问：`http://your-ec2-ip`

登录Admin：`http://your-ec2-ip/admin`
- 用户名：`admin`（从备份恢复）
- 密码：使用此前私下设置的管理员密码；如已遗忘，运行 `python manage.py changepassword admin` 并按隐藏输入提示重置。

---

## 工作原理

### Volume备份原理

```bash
# 备份命令
docker run --rm \
  -v maori-story-fill_postgres_dev_data:/source:ro \  # 挂载源volume（只读）
  -v $(pwd)/backup:/backup \                          # 挂载备份目录
  alpine \                                            # 使用alpine临时容器
  tar czf /backup/postgres_data.tar.gz -C /source .  # 打包volume内容
```

**过程：**
1. 创建临时Alpine容器
2. 挂载Volume到容器的 `/source` 目录
3. 用tar打包 `/source` 的内容
4. 保存到本地的备份目录
5. 容器自动删除（--rm）

### Volume恢复原理

```bash
# 恢复命令
docker run --rm \
  -v maori-story-fill_postgres_data:/target \        # 挂载目标volume（可写）
  -v $(pwd)/backup:/backup:ro \                      # 挂载备份目录（只读）
  alpine \                                           # 使用alpine临时容器
  tar xzf /backup/postgres_data.tar.gz -C /target   # 解压到volume
```

---

## 对比：Volume备份 vs pg_dump

### Volume备份方式（本指南）

**优点：**
- ✅ 一次性完整备份（数据库+文件）
- ✅ 操作简单（一键备份/恢复）
- ✅ 100%数据完整性
- ✅ 快速（直接文件复制）
- ✅ 包含所有PostgreSQL配置

**缺点：**
- ❌ 备份文件较大（包含整个数据库）
- ❌ PostgreSQL版本必须完全一致
- ❌ 不支持跨数据库迁移（例如PostgreSQL → MySQL）

### pg_dump方式

**优点：**
- ✅ 备份文件较小（SQL文本）
- ✅ 跨版本兼容性好
- ✅ 可编辑SQL文件
- ✅ 支持选择性导入（单表、schema等）

**缺点：**
- ❌ 需要分别处理数据库和媒体文件
- ❌ 恢复速度慢（需要执行SQL）
- ❌ 操作复杂（多个步骤）

---

## 最佳实践

### 开发环境 → 生产环境（首次部署）

**推荐：Volume备份**
```bash
# 本地
./scripts/backup-volumes.sh

# 上传到EC2
scp -r volume-backup-* ec2-user@your-ec2-ip:/home/ec2-user/

# EC2恢复
./scripts/restore-volumes-ec2.sh ~/volume-backup-*
```

### 生产环境定期备份

**推荐：自动化备份**
```bash
# 每天凌晨2点自动备份
0 2 * * * /path/to/backup-volumes.sh && \
  aws s3 cp volume-backup-$(date +\%Y\%m\%d)/ \
  s3://your-bucket/daily-backups/ --recursive
```

### 灾难恢复

**推荐：S3 + Volume备份组合**
- 数据库：Volume备份存储在S3
- 媒体文件：直接使用S3存储（USE_S3=true）
- 好处：媒体文件不需要备份，只需备份数据库

---

## 故障排查

### 问题1：恢复后数据为空

**原因：**Volume未完全清空

**解决：**
```bash
# 完全删除旧volume
docker volume rm maori-story-fill_postgres_data
docker volume rm maori-story-fill_media_data

# 重新恢复
./scripts/restore-volumes-ec2.sh ~/volume-backup-*
```

### 问题2：Permission denied

**原因：**文件权限不正确

**解决：**
```bash
# 修复权限
docker exec maori-backend chown -R app:app /app/media
docker exec maori-backend chmod -R 755 /app/media
```

### 问题3：PostgreSQL版本不匹配

**症状：**
```
FATAL: database files are incompatible with server
```

**解决：**
- 确保本地和EC2使用相同的PostgreSQL版本
- 本地：`postgres:16-alpine`
- EC2：也必须是 `postgres:16-alpine`

### 问题4：备份文件过大

**解决：**
```bash
# 使用更高压缩率
docker run --rm \
  -v maori-story-fill_postgres_dev_data:/source:ro \
  -v $(pwd)/backup:/backup \
  alpine \
  tar czf /backup/postgres_data.tar.gz -C /source . --use-compress-program=pigz
```

---

## 快速参考

### 本地备份
```bash
./scripts/backup-volumes.sh
```

### 上传到EC2
```bash
scp -r volume-backup-* ec2-user@your-ec2-ip:/home/ec2-user/
```

### EC2恢复
```bash
./scripts/restore-volumes-ec2.sh ~/volume-backup-*
```

### 验证
```bash
docker-compose -f docker-compose.prod.yml ps
docker exec maori-backend python manage.py shell -c "from core.models import Story; print(Story.objects.count())"
```

---

## 进阶：增量备份

Volume备份是全量备份。如果需要增量备份：

```bash
# 使用rsync增量同步
docker run --rm \
  -v maori-story-fill_postgres_dev_data:/source:ro \
  -v $(pwd)/incremental-backup:/backup \
  alpine \
  rsync -av --delete /source/ /backup/
```

但对于生产环境，推荐使用：
- **AWS RDS** - 自动备份和时间点恢复
- **S3存储** - 媒体文件直接存储在S3，无需备份

---

## 下一步

1. ✅ 本地测试备份和恢复
2. ✅ 在测试EC2实例验证完整流程
3. ✅ 配置自动化备份（cron + S3）
4. ✅ 生产环境部署时使用Volume恢复

有问题参考：
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - 其他迁移方案
- [S3_STORAGE_GUIDE.md](./S3_STORAGE_GUIDE.md) - S3存储配置
