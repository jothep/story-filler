#!/bin/bash
# 数据导入脚本（在EC2上运行）
set -e

if [ -z "$1" ]; then
    echo "用法: ./import-data.sh <导出目录>"
    echo "示例: ./import-data.sh ./data-export-20260412-140000"
    exit 1
fi

IMPORT_DIR="$1"

if [ ! -d "$IMPORT_DIR" ]; then
    echo "❌ 错误: 目录 $IMPORT_DIR 不存在"
    exit 1
fi

echo "=== 开始数据导入 ==="
echo "📁 导入目录: $IMPORT_DIR"

# 检查文件存在
if [ ! -f "$IMPORT_DIR/database.sql" ]; then
    echo "❌ 错误: database.sql 不存在"
    exit 1
fi

if [ ! -f "$IMPORT_DIR/media.tar.gz" ]; then
    echo "❌ 错误: media.tar.gz 不存在"
    exit 1
fi

# 1. 导入数据库
echo ""
echo "📦 导入数据库..."
docker exec -i maori-backend sh -c 'PGPASSWORD=$DB_PASSWORD psql -h db -U dbuser maori_story' < "$IMPORT_DIR/database.sql"
echo "✅ 数据库导入完成"

# 2. 导入媒体文件
echo ""
echo "📦 导入媒体文件..."
docker cp "$IMPORT_DIR/media.tar.gz" maori-backend:/tmp/
docker exec maori-backend tar xzf /tmp/media.tar.gz -C /app
docker exec maori-backend rm /tmp/media.tar.gz
docker exec maori-backend chown -R app:app /app/media
echo "✅ 媒体文件导入完成"

# 3. 重启后端
echo ""
echo "🔄 重启后端服务..."
docker restart maori-backend
sleep 3
echo "✅ 后端服务已重启"

echo ""
echo "🎉 数据导入完成！"
echo "🌐 访问: http://$(curl -s ifconfig.me)"
