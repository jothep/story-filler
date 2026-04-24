#!/bin/bash
# Docker Volume 恢复脚本
set -e

if [ -z "$1" ]; then
    echo "用法: ./restore-volumes.sh <备份目录>"
    echo "示例: ./restore-volumes.sh ./volume-backup-20260412-140000"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 错误: 备份目录 $BACKUP_DIR 不存在"
    exit 1
fi

if [ ! -f "$BACKUP_DIR/postgres_data.tar.gz" ] || [ ! -f "$BACKUP_DIR/media_data.tar.gz" ]; then
    echo "❌ 错误: 备份文件不完整"
    echo "需要: postgres_data.tar.gz 和 media_data.tar.gz"
    exit 1
fi

echo "=== Docker Volume 恢复工具 ==="
echo "📁 备份目录: $BACKUP_DIR"
echo ""

# 检查Volume是否存在
echo "🔍 检查目标Volumes..."
if docker volume inspect maori-story-fill_postgres_dev_data &>/dev/null; then
    echo "⚠️  警告: postgres_dev_data 已存在"
    read -p "是否覆盖？这将删除现有数据！(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ 操作取消"
        exit 1
    fi
    docker volume rm maori-story-fill_postgres_dev_data
fi

if docker volume inspect maori-story-fill_media_dev_data &>/dev/null; then
    echo "⚠️  警告: media_dev_data 已存在"
    read -p "是否覆盖？这将删除现有数据！(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ 操作取消"
        exit 1
    fi
    docker volume rm maori-story-fill_media_dev_data
fi

# 创建新Volumes
echo ""
echo "📦 创建新Volumes..."
docker volume create maori-story-fill_postgres_dev_data
docker volume create maori-story-fill_media_dev_data
echo "✅ Volumes创建完成"

# 恢复数据库Volume
echo ""
echo "📦 恢复数据库 Volume..."
docker run --rm \
  -v maori-story-fill_postgres_dev_data:/target \
  -v "$(pwd)/$BACKUP_DIR":/backup:ro \
  alpine \
  tar xzf /backup/postgres_data.tar.gz -C /target

echo "✅ 数据库恢复完成"

# 恢复媒体文件Volume
echo ""
echo "📦 恢复媒体文件 Volume..."
docker run --rm \
  -v maori-story-fill_media_dev_data:/target \
  -v "$(pwd)/$BACKUP_DIR":/backup:ro \
  alpine \
  tar xzf /backup/media_data.tar.gz -C /target

echo "✅ 媒体文件恢复完成"

echo ""
echo "🎉 Volume恢复完成！"
echo ""
echo "下一步: 启动容器"
echo "docker-compose -f docker-compose.dev.yml up -d"
