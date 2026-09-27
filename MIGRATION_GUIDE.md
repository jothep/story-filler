> **Historical implementation note — September 2026 review:** This document retains an earlier design, estimate, procedure or plan. It is not the current deployment specification, and its performance, cost, security and recovery claims have not all been revalidated. Use the [architecture index](docs/ARCHITECTURE.md) and [dated verification record](docs/verification.md) for current scope and evidence.

# 数据迁移指南

本指南说明如何将数据从本地开发环境迁移到AWS EC2生产环境。

## 目录

- [方案1：手动导出/导入（快速迁移）](#方案1手动导出导入)
- [方案2：使用S3存储（推荐生产环境）](#方案2使用s3存储推荐)
- [方案3：增量迁移（持续更新）](#方案3增量迁移)

---

## 方案1：手动导出/导入

适合：**一次性迁移，数据量小（< 10GB）**

### 本地环境：导出数据

```bash
# 运行导出脚本
./scripts/export-data.sh

# 输出示例：
# ✅ 导出完成！
# 📁 导出目录: ./data-export-20260412-140530
```

### 上传到EC2

```bash
# 方法1：使用scp
scp -r data-export-20260412-140530/ ec2-user@your-ec2-ip:/home/ec2-user/

# 方法2：使用rsync（支持断点续传）
rsync -avz --progress data-export-20260412-140530/ ec2-user@your-ec2-ip:/home/ec2-user/

# 方法3：通过S3中转（推荐大文件）
aws s3 cp data-export-20260412-140530/ s3://your-bucket/migration/ --recursive
# 在EC2上下载
aws s3 cp s3://your-bucket/migration/ ./ --recursive
```

### EC2环境：导入数据

```bash
# 进入项目目录
cd /path/to/maori-story-fill

# 启动数据库
docker-compose -f docker-compose.prod.yml up -d db

# 等待数据库就绪
sleep 10

# 运行导入脚本
./scripts/import-data.sh ~/data-export-20260412-140530

# 启动完整服务
docker-compose -f docker-compose.prod.yml up -d
```

---

## 方案2：使用S3存储（推荐）

适合：**生产环境，需要持久化、备份、CDN加速**

### 为什么推荐S3？

| 传统本地存储 | S3存储 |
|------------|--------|
| ❌ 容器重建后文件可能丢失 | ✅ 文件永久保存在S3 |
| ❌ 多容器环境需要共享存储 | ✅ 所有容器共享S3桶 |
| ❌ 需要手动备份 | ✅ S3自动备份和版本控制 |
| ❌ 迁移需要拷贝文件 | ✅ 只需配置环境变量 |
| ❌ 无CDN加速 | ✅ 可配置CloudFront CDN |

### S3迁移步骤

#### 1. 在AWS创建S3桶

```bash
# 使用AWS CLI创建桶
aws s3 mb s3://maori-story-media --region ap-southeast-2

# 设置桶策略（允许公开读取）
aws s3api put-bucket-policy --bucket maori-story-media --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::maori-story-media/*"
  }]
}'
```

#### 2. 上传本地媒体文件到S3

```bash
# 从本地导出媒体文件
docker exec maori-dev-backend tar czf /tmp/media.tar.gz -C /app media/
docker cp maori-dev-backend:/tmp/media.tar.gz ./

# 解压并上传到S3
tar xzf media.tar.gz
aws s3 sync ./media/ s3://maori-story-media/ --region ap-southeast-2

# 验证上传
aws s3 ls s3://maori-story-media/ --recursive
```

#### 3. 在EC2配置S3存储

编辑 `.env` 文件（或环境变量）：

```bash
# S3配置
USE_S3=true
# AWS_ACCESS_KEY_ID: set privately via environment or an untracked local configuration.
# AWS_SECRET_ACCESS_KEY: set privately via environment or an untracked local configuration.
AWS_STORAGE_BUCKET_NAME=maori-story-media
AWS_S3_REGION_NAME=ap-southeast-2
```

#### 4. 导入数据库（只需一次）

```bash
# 导出本地数据库
docker exec maori-dev-db pg_dump -U devuser maori_story_dev > database.sql

# 上传到EC2并导入
scp database.sql ec2-user@your-ec2-ip:/tmp/
ssh ec2-user@your-ec2-ip
docker exec -i maori-backend sh -c 'PGPASSWORD=$DB_PASSWORD psql -h db -U dbuser maori_story' < /tmp/database.sql
```

#### 5. 启动生产环境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### S3配置后的优势

**自动处理：**
- 所有新上传的文件自动保存到S3
- 文件URL自动生成：`https://maori-story-media.s3.ap-southeast-2.amazonaws.com/bgm/song.mp3`
- 无需手动迁移媒体文件

**数据迁移简化：**
```bash
# 本地开发 → EC2生产
# 只需迁移数据库！媒体文件已在S3
pg_dump → scp → psql
```

---

## 方案3：增量迁移

适合：**持续开发，定期同步测试数据**

### 自动同步脚本

创建 `scripts/sync-to-ec2.sh`：

```bash
#!/bin/bash
# 增量同步到EC2

EC2_HOST="ec2-user@your-ec2-ip"
EC2_PATH="/home/ec2-user/maori-story-fill"

# 1. 同步代码
echo "📦 同步代码..."
rsync -avz --exclude 'node_modules' --exclude '.git' \
  ./ $EC2_HOST:$EC2_PATH/

# 2. 同步数据库（仅新增数据）
echo "📦 导出数据库增量..."
docker exec maori-dev-db pg_dump -U devuser maori_story_dev > /tmp/db.sql
scp /tmp/db.sql $EC2_HOST:/tmp/

ssh $EC2_HOST << 'EOF'
cd /home/ec2-user/maori-story-fill
docker exec -i maori-backend sh -c 'PGPASSWORD=$DB_PASSWORD psql -h db -U dbuser maori_story' < /tmp/db.sql
docker-compose -f docker-compose.prod.yml restart backend
EOF

echo "✅ 同步完成！"
```

---

## 数据库迁移最佳实践

### 使用Django数据迁移

```bash
# 本地：生成迁移文件
docker exec maori-dev-backend python manage.py makemigrations

# 提交到git
git add backend/core/migrations/
git commit -m "Add database migration"
git push

# EC2：拉取代码并执行迁移
git pull
docker exec maori-backend python manage.py migrate
```

### 数据备份策略

**本地环境（开发）：**
```bash
# 每天自动备份
0 2 * * * /path/to/export-data.sh
```

**EC2环境（生产）：**
```bash
# 使用AWS Backup或定期快照
# 数据库：RDS自动备份
# 媒体文件：S3版本控制 + 生命周期策略
```

---

## 故障排查

### 问题1：数据库导入失败

```bash
# 错误：role "devuser" does not exist
# 解决：确保用户名匹配
docker exec -i maori-backend sh -c 'PGPASSWORD=$DB_PASSWORD psql -h db -U dbuser maori_story' < database.sql
```

### 问题2：媒体文件权限错误

```bash
# 修复权限
docker exec maori-backend chown -R app:app /app/media
```

### 问题3：S3访问被拒绝

```bash
# 检查IAM权限
aws s3 ls s3://maori-story-media/

# 确保桶策略正确
aws s3api get-bucket-policy --bucket maori-story-media
```

---

## 快速参考

### 完整迁移清单

**本地准备：**
- [ ] 运行 `./scripts/export-data.sh`
- [ ] 上传文件到EC2或S3
- [ ] 提交代码到git

**EC2部署：**
- [ ] 克隆代码：`git clone ...`
- [ ] 配置环境变量：编辑 `.env`
- [ ] 导入数据库：`./scripts/import-data.sh`
- [ ] 启动服务：`docker-compose -f docker-compose.prod.yml up -d`
- [ ] 验证服务：访问 `http://your-ec2-ip`

**推荐生产配置：**
- [ ] 使用S3存储媒体文件
- [ ] 使用RDS托管数据库（可选）
- [ ] 配置CloudFront CDN（可选）
- [ ] 设置自动备份策略

---

## 成本估算（AWS）

### 方案1：本地存储（EC2卷）

| 项目 | 规格 | 月费用 |
|------|------|--------|
| EBS卷 | 100GB gp3 | ~$8 USD |
| 备份快照 | 100GB/月 | ~$5 USD |
| **总计** | | **~$13 USD/月** |

### 方案2：S3存储（推荐）

| 项目 | 用量 | 月费用 |
|------|------|--------|
| S3存储 | 100GB | ~$2.30 USD |
| S3请求 | 10万GET | ~$0.04 USD |
| 数据传输 | 100GB出站 | ~$9 USD |
| **总计** | | **~$11.34 USD/月** |

**S3优势：**
- ✅ 更便宜
- ✅ 无限扩展
- ✅ 自动备份
- ✅ 99.999999999% 持久性

---

## 下一步

1. **测试环境验证：** 先在测试EC2实例上完整走一遍流程
2. **生产环境部署：** 使用S3存储 + RDS数据库
3. **监控配置：** CloudWatch告警、日志收集
4. **CI/CD集成：** GitHub Actions自动部署

详细配置请参考：
- [S3_STORAGE_GUIDE.md](./S3_STORAGE_GUIDE.md) - S3存储详细配置
- [docker-compose.prod.yml](./docker-compose.prod.yml) - 生产环境配置
- [CHANGELOG.md](./CHANGELOG.md) - 版本更新记录
