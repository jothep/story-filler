#!/bin/bash
# ============================================
# Maori Story Fill - EC2 User Data Script
# ============================================
# 此脚本在 EC2 实例首次启动时自动执行
# 用于安装 Docker、克隆代码、部署应用

set -e  # 遇到错误立即退出

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a /var/log/maori-story-init.log
}

log "=========================================="
log "开始初始化 Maori Story Fill EC2 实例"
log "=========================================="

# ----------------------
# 1. 系统更新
# ----------------------
log "步骤 1: 更新系统包..."
apt-get update -y
apt-get upgrade -y

# ----------------------
# 2. 安装依赖
# ----------------------
log "步骤 2: 安装基础依赖..."
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release

# ----------------------
# 3. 安装 Docker
# ----------------------
log "步骤 3: 安装 Docker..."

# 添加 Docker 官方 GPG 密钥
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动 Docker 服务
systemctl start docker
systemctl enable docker

# 将 ubuntu 用户加入 docker 组
usermod -aG docker ubuntu

log "Docker 安装完成: $(docker --version)"

# ----------------------
# 4. 克隆项目代码
# ----------------------
log "步骤 4: 克隆项目代码..."

# 切换到 ubuntu 用户的主目录
cd /home/ubuntu

# 克隆仓库（使用 sudo -u ubuntu 以 ubuntu 用户身份执行）
sudo -u ubuntu git clone ${git_repo_url} maori-story-fill || {
    log "Git clone 失败，可能仓库已存在或URL错误"
    exit 1
}

cd maori-story-fill
sudo -u ubuntu git checkout ${git_branch}

log "代码克隆完成"

# ----------------------
# 5. 配置环境变量
# ----------------------
log "步骤 5: 配置环境变量..."

cat > .env << EOF
# 数据库配置
DB_PASSWORD=${db_password}

# Django 配置
DJANGO_SECRET_KEY=${django_secret_key}
DJANGO_DEBUG=False
ALLOWED_HOSTS=*

# 应用配置
MEDIA_ROOT=/app/media
STATIC_ROOT=/app/staticfiles
EOF

chown ubuntu:ubuntu .env
chmod 600 .env

log "环境变量配置完成"

# ----------------------
# 6. 构建并启动容器
# ----------------------
log "步骤 6: 构建并启动 Docker 容器..."

# 使用 ubuntu 用户执行 Docker 命令
cd /home/ubuntu/maori-story-fill

# 构建镜像
sudo -u ubuntu docker compose -f docker-compose.prod.yml build

# 启动容器
sudo -u ubuntu docker compose -f docker-compose.prod.yml up -d

log "等待容器启动..."
sleep 15

# ----------------------
# 7. 初始化数据库
# ----------------------
log "步骤 7: 初始化数据库..."

# 运行数据库迁移
sudo -u ubuntu docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

# 收集静态文件
sudo -u ubuntu docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

log "数据库初始化完成"

# ----------------------
# 8. 配置自动启动
# ----------------------
log "步骤 8: 配置系统重启后自动启动..."

# 创建 systemd 服务
cat > /etc/systemd/system/maori-story.service << 'EOF'
[Unit]
Description=Maori Story Fill Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/maori-story-fill
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
systemctl daemon-reload
systemctl enable maori-story.service

log "自动启动配置完成"

# ----------------------
# 9. 设置防火墙（可选）
# ----------------------
log "步骤 9: 配置 UFW 防火墙..."

ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload

log "防火墙配置完成"

# ----------------------
# 10. 健康检查
# ----------------------
log "步骤 10: 健康检查..."

sleep 5

# 检查容器状态
log "容器状态:"
sudo -u ubuntu docker compose -f /home/ubuntu/maori-story-fill/docker-compose.prod.yml ps

# 测试 HTTP 访问
if curl -f http://localhost/health > /dev/null 2>&1; then
    log "✅ 健康检查通过"
else
    log "⚠️  健康检查失败，请手动检查"
fi

# ----------------------
# 完成
# ----------------------
log "=========================================="
log "✅ 初始化完成！"
log "=========================================="
log ""
log "📋 后续步骤："
log "1. SSH 连接: ssh -i ~/.ssh/${key_pair_name}.pem ubuntu@$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
log "2. 创建超级用户: cd ~/maori-story-fill && docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
log "3. 访问网站: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
log ""
log "💾 备份命令: /home/ubuntu/maori-story-fill/backup.sh"
log "📊 查看日志: docker compose -f /home/ubuntu/maori-story-fill/docker-compose.prod.yml logs -f"
log ""

# 创建完成标记文件
touch /var/log/maori-story-init-complete
log "初始化标记文件已创建: /var/log/maori-story-init-complete"
