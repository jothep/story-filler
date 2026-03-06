#!/bin/bash

# ============================================
# Maori Story Fill - 部署脚本
# ============================================
# 用途：自动化部署到 Oracle Cloud 或其他服务器
# 使用方法：./deploy.sh

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🚀 Maori Story Fill 部署脚本${NC}"
echo -e "${GREEN}================================${NC}"

# 检查是否在正确的目录
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  警告: 未找到 .env 文件${NC}"
    echo -e "${YELLOW}   正在从 .env.example 复制...${NC}"
    cp .env.example .env
    echo -e "${RED}❌ 请先编辑 .env 文件，填写必要的配置！${NC}"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker 未安装${NC}"
    exit 1
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker Compose 未安装${NC}"
    exit 1
fi

# 1. 拉取最新代码（如果是 git 仓库）
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 拉取最新代码...${NC}"
    git pull origin main || echo -e "${YELLOW}⚠️  Git pull 失败，跳过...${NC}"
fi

# 2. 停止旧容器
echo -e "${YELLOW}🛑 停止旧容器...${NC}"
docker compose -f docker-compose.prod.yml down || true

# 3. 拉取最新镜像（如果使用远程镜像）
# echo -e "${YELLOW}📦 拉取最新镜像...${NC}"
# docker compose -f docker-compose.prod.yml pull

# 4. 构建镜像
echo -e "${YELLOW}🔨 构建 Docker 镜像...${NC}"
docker compose -f docker-compose.prod.yml build --no-cache

# 5. 启动容器
echo -e "${YELLOW}▶️  启动容器...${NC}"
docker compose -f docker-compose.prod.yml up -d

# 6. 等待数据库启动
echo -e "${YELLOW}⏳ 等待数据库启动...${NC}"
sleep 10

# 7. 运行数据库迁移
echo -e "${YELLOW}🔄 运行数据库迁移...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

# 8. 收集静态文件
echo -e "${YELLOW}📦 收集静态文件...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

# 9. 创建超级用户（可选，首次部署时）
# echo -e "${YELLOW}👤 创建超级用户（如果需要）...${NC}"
# docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 10. 健康检查
echo -e "${YELLOW}🏥 健康检查...${NC}"
sleep 5

# 检查所有容器状态
echo -e "\n${YELLOW}📊 容器状态:${NC}"
docker compose -f docker-compose.prod.yml ps

# 测试 API 端点
echo -e "\n${YELLOW}🔍 测试 API 端点...${NC}"
if curl -f -s http://localhost/health > /dev/null; then
    echo -e "${GREEN}✅ Nginx 健康检查通过${NC}"
else
    echo -e "${RED}❌ Nginx 健康检查失败${NC}"
fi

if curl -f -s http://localhost/api/stories/ > /dev/null; then
    echo -e "${GREEN}✅ API 端点正常${NC}"
else
    echo -e "${YELLOW}⚠️  API 端点可能需要初始化数据${NC}"
fi

# 11. 显示日志（最后20行）
echo -e "\n${YELLOW}📝 最近日志:${NC}"
docker compose -f docker-compose.prod.yml logs --tail=20

# 12. 完成
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "\n${GREEN}🌐 访问地址:${NC}"
echo -e "   - 前端: http://localhost"
echo -e "   - API: http://localhost/api/stories/"
echo -e "   - Admin: http://localhost/admin/"
echo -e "\n${YELLOW}💡 常用命令:${NC}"
echo -e "   - 查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo -e "   - 重启服务: docker compose -f docker-compose.prod.yml restart"
echo -e "   - 停止服务: docker compose -f docker-compose.prod.yml down"
echo -e "   - 查看状态: docker compose -f docker-compose.prod.yml ps"
echo -e "\n${GREEN}🎉 祝使用愉快！${NC}\n"
