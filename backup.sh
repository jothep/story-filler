#!/bin/bash

# ============================================
# Maori Story Fill - 备份脚本
# ============================================
# 用途：备份数据库和媒体文件
# 使用方法：./backup.sh

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置
BACKUP_DIR="$HOME/maori-story-backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"
MEDIA_BACKUP_FILE="$BACKUP_DIR/media_backup_$DATE.tar.gz"

echo -e "${GREEN}🔄 开始备份...${NC}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 1. 备份数据库
echo -e "${YELLOW}📦 备份数据库...${NC}"
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U dbuser maori_story > "$DB_BACKUP_FILE"

echo -e "${GREEN}✅ 数据库备份完成: $DB_BACKUP_FILE${NC}"

# 2. 备份媒体文件
echo -e "${YELLOW}📦 备份媒体文件...${NC}"
MEDIA_VOLUME=$(docker volume inspect maori-story-fill_media_data --format '{{.Mountpoint}}' 2>/dev/null || echo "")

if [ -n "$MEDIA_VOLUME" ]; then
    sudo tar -czf "$MEDIA_BACKUP_FILE" -C "$MEDIA_VOLUME" .
    echo -e "${GREEN}✅ 媒体文件备份完成: $MEDIA_BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠️  未找到媒体文件卷，跳过...${NC}"
fi

# 3. 清理旧备份（保留最近7天）
echo -e "${YELLOW}🧹 清理旧备份（保留7天）...${NC}"
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

# 4. 显示备份大小
echo -e "\n${GREEN}📊 备份统计:${NC}"
ls -lh "$BACKUP_DIR" | tail -n 2

echo -e "\n${GREEN}✅ 备份完成！${NC}"
echo -e "${GREEN}备份位置: $BACKUP_DIR${NC}\n"
