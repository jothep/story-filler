#!/bin/bash
# 数据导出脚本
set -e

EXPORT_DIR="./data-export-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$EXPORT_DIR"

echo "=== 开始数据导出 ==="

# 1. 导出数据库
echo "📦 导出数据库..."
docker exec maori-dev-db pg_dump -U devuser maori_story_dev > "$EXPORT_DIR/database.sql"
echo "✅ 数据库导出完成: $EXPORT_DIR/database.sql"

# 2. 导出媒体文件
echo "📦 导出媒体文件..."
docker exec maori-dev-backend tar czf /tmp/media.tar.gz -C /app media/
docker cp maori-dev-backend:/tmp/media.tar.gz "$EXPORT_DIR/media.tar.gz"
docker exec maori-dev-backend rm /tmp/media.tar.gz
echo "✅ 媒体文件导出完成: $EXPORT_DIR/media.tar.gz"

# 3. 生成导入说明
cat > "$EXPORT_DIR/README.md" << 'EOF'
# 数据导入说明

## 在EC2上导入数据

### 1. 上传文件到EC2
```bash
scp -r data-export-* ec2-user@your-ec2-ip:/home/ec2-user/
```

### 2. 导入数据库
```bash
# 进入项目目录
cd /path/to/maori-story-fill

# 确保容器运行
docker-compose -f docker-compose.prod.yml up -d db

# 导入数据库
docker exec -i maori-db psql -U dbuser maori_story < database.sql
```

### 3. 导入媒体文件
```bash
# 解压媒体文件
docker cp media.tar.gz maori-backend:/tmp/
docker exec maori-backend tar xzf /tmp/media.tar.gz -C /app
docker exec maori-backend rm /tmp/media.tar.gz
docker exec maori-backend chown -R app:app /app/media
```

### 4. 重启服务
```bash
docker-compose -f docker-compose.prod.yml restart backend
```
EOF

echo ""
echo "✅ 导出完成！"
echo "📁 导出目录: $EXPORT_DIR"
echo "📖 查看导入说明: $EXPORT_DIR/README.md"
