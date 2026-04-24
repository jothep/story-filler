#!/bin/bash
# Docker Volume 备份脚本
set -e

BACKUP_DIR="./volume-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=== Docker Volume 备份工具 ==="
echo "📁 备份目录: $BACKUP_DIR"
echo ""

# 备份数据库Volume
echo "📦 备份数据库 Volume..."
docker run --rm \
  -v maori-story-fill_postgres_dev_data:/source:ro \
  -v "$(pwd)/$BACKUP_DIR":/backup \
  alpine \
  tar czf /backup/postgres_data.tar.gz -C /source .

POSTGRES_SIZE=$(du -h "$BACKUP_DIR/postgres_data.tar.gz" | cut -f1)
echo "✅ 数据库备份完成: postgres_data.tar.gz ($POSTGRES_SIZE)"

# 备份媒体文件Volume
echo ""
echo "📦 备份媒体文件 Volume..."
docker run --rm \
  -v maori-story-fill_media_dev_data:/source:ro \
  -v "$(pwd)/$BACKUP_DIR":/backup \
  alpine \
  tar czf /backup/media_data.tar.gz -C /source .

MEDIA_SIZE=$(du -h "$BACKUP_DIR/media_data.tar.gz" | cut -f1)
echo "✅ 媒体文件备份完成: media_data.tar.gz ($MEDIA_SIZE)"

# 生成备份清单
cat > "$BACKUP_DIR/backup-info.txt" << EOF
=== Docker Volume 备份信息 ===

备份时间: $(date)
备份来源: maori-story-fill 开发环境

Volumes:
- postgres_dev_data → postgres_data.tar.gz ($POSTGRES_SIZE)
- media_dev_data → media_data.tar.gz ($MEDIA_SIZE)

恢复方法:
./scripts/restore-volumes.sh $BACKUP_DIR
EOF

echo ""
echo "✅ 备份完成！"
echo "📁 备份位置: $BACKUP_DIR"
echo ""
echo "备份内容:"
ls -lh "$BACKUP_DIR"
