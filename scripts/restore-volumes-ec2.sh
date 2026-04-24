#!/bin/bash
# EC2生产环境 Volume 恢复脚本
set -e

if [ -z "$1" ]; then
    echo "用法: ./restore-volumes-ec2.sh <备份目录>"
    echo "示例: ./restore-volumes-ec2.sh ./volume-backup-20260412-140000"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 错误: 备份目录 $BACKUP_DIR 不存在"
    exit 1
fi

echo "=== EC2 生产环境 Volume 恢复 ==="
echo "📁 备份目录: $BACKUP_DIR"
echo ""

# 注意：生产环境的volume名称可能不同
POSTGRES_VOLUME="maori-story-fill_postgres_data"  # 生产环境volume名
MEDIA_VOLUME="maori-story-fill_media_data"        # 生产环境volume名

# 停止服务（避免数据冲突）
echo "⏸️  停止服务..."
docker-compose -f docker-compose.prod.yml down
echo "✅ 服务已停止"

# 检查并创建Volumes
echo ""
echo "📦 准备Volumes..."
docker volume create $POSTGRES_VOLUME 2>/dev/null || true
docker volume create $MEDIA_VOLUME 2>/dev/null || true

# 恢复数据库Volume
echo ""
echo "📦 恢复数据库 Volume..."
docker run --rm \
  -v $POSTGRES_VOLUME:/target \
  -v "$(pwd)/$BACKUP_DIR":/backup:ro \
  alpine \
  sh -c "rm -rf /target/* /target/..?* /target/.[!.]* 2>/dev/null || true; tar xzf /backup/postgres_data.tar.gz -C /target"

echo "✅ 数据库恢复完成"

# 恢复媒体文件Volume
echo ""
echo "📦 恢复媒体文件 Volume..."
docker run --rm \
  -v $MEDIA_VOLUME:/target \
  -v "$(pwd)/$BACKUP_DIR":/backup:ro \
  alpine \
  sh -c "rm -rf /target/* /target/..?* /target/.[!.]* 2>/dev/null || true; tar xzf /backup/media_data.tar.gz -C /target"

echo "✅ 媒体文件恢复完成"

# 启动服务
echo ""
echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "🎉 恢复完成！"
echo ""
echo "检查服务状态:"
echo "docker-compose -f docker-compose.prod.yml ps"
