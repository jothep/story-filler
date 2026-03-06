# Maori Story Fill - Oracle Cloud 免费部署指南

## 🎯 目标

使用 **Oracle Cloud Always Free Tier** 实现零成本部署，配置：
- 1个 VM 实例（ARM64）：2 OCPU + 12 GB RAM
- 100 GB 块存储（媒体文件 + 数据库）
- Docker Compose 运行所有服务

---

## 📋 前置准备

### 1. 注册 Oracle Cloud 账号
- URL: https://cloud.oracle.com/
- 需要信用卡验证（不会扣费）
- 选择 "Always Free" 资源

### 2. 创建 VM 实例

**实例配置**:
```yaml
Name: maori-story-vm
Image: Canonical Ubuntu 22.04 (ARM64)
Shape: VM.Standard.A1.Flex
  OCPU: 2
  Memory: 12 GB
Boot Volume: 100 GB
Virtual Cloud Network: 创建新的VCN（自动配置）
Public IP: 分配公网IP
SSH Keys: 上传你的公钥
```

**创建步骤**:
```bash
# 1. 登录 Oracle Cloud Console
# 2. 导航到: Compute > Instances > Create Instance
# 3. 选择 "Image and Shape"
#    - Image: Canonical Ubuntu 22.04 (aarch64)
#    - Shape: VM.Standard.A1.Flex
#    - OCPUs: 2, Memory: 12 GB
# 4. Networking
#    - 创建新VCN（默认配置）
#    - 分配公网IP: 是
# 5. Add SSH Keys
#    - 粘贴你的公钥内容（~/.ssh/id_rsa.pub）
# 6. Boot Volume
#    - Size: 100 GB
# 7. Create
```

### 3. 配置安全规则（Ingress Rules）

```bash
# 在VCN的Security List中添加规则:
允许端口:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS，未来用)
- 8000 (Django，调试用，生产可关闭)

具体配置:
Ingress Rule 1:
  Source CIDR: 0.0.0.0/0
  Protocol: TCP
  Destination Port: 22

Ingress Rule 2:
  Source CIDR: 0.0.0.0/0
  Protocol: TCP
  Destination Port: 80

Ingress Rule 3:
  Source CIDR: 0.0.0.0/0
  Protocol: TCP
  Destination Port: 443
```

---

## 🚀 部署步骤

### Step 1: 连接到 VM

```bash
# 获取公网IP（从Oracle Console）
export ORACLE_VM_IP="xxx.xxx.xxx.xxx"

# SSH连接
ssh ubuntu@$ORACLE_VM_IP

# 如果连接失败，检查：
# 1. 安全规则是否配置正确
# 2. 使用正确的私钥: ssh -i ~/.ssh/id_rsa ubuntu@$ORACLE_VM_IP
```

### Step 2: 安装 Docker

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker（官方脚本）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户加入docker组
sudo usermod -aG docker ubuntu

# 安装 Docker Compose
sudo apt install docker-compose-v2 -y

# 退出并重新登录使权限生效
exit
ssh ubuntu@$ORACLE_VM_IP

# 验证安装
docker --version
docker compose version
```

### Step 3: 配置防火墙（Ubuntu）

```bash
# Oracle Cloud默认使用iptables阻止端口，需要额外配置
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# 持久化规则
sudo netfilter-persistent save

# 或者直接禁用 Oracle 的防火墙（简单但不推荐生产环境）
# sudo iptables -F
```

### Step 4: 克隆项目代码

```bash
# 安装 Git
sudo apt install git -y

# 克隆仓库（替换为你的仓库地址）
git clone https://github.com/your-username/maori-story-fill.git
cd maori-story-fill
```

### Step 5: 构建 ARM64 镜像

**重要**: Oracle Cloud 使用 ARM64 架构，需要重新构建镜像。

#### 方案A: 在本地构建并推送（推荐）

```bash
# 在本地Mac/Linux机器上：

# 1. 安装buildx（如果没有）
docker buildx create --use

# 2. 构建并推送ARM64镜像到Docker Hub
cd backend
docker buildx build --platform linux/arm64 \
  -t your-dockerhub-username/maori-backend:arm64 \
  --push .

cd ../frontend
docker buildx build --platform linux/arm64 \
  -t your-dockerhub-username/maori-frontend:arm64 \
  --push .
```

#### 方案B: 在VM上直接构建（较慢）

```bash
# 在Oracle VM上构建
cd maori-story-fill/backend
docker build -t maori-backend:latest .

cd ../frontend
docker build -t maori-frontend:latest .
```

### Step 6: 创建 Docker Compose 配置

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: maori-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: maori_story
      POSTGRES_USER: dbuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dbuser"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - maori-network

  backend:
    image: your-dockerhub-username/maori-backend:arm64
    container_name: maori-backend
    restart: unless-stopped
    command: gunicorn maori_story_project.wsgi:application --bind 0.0.0.0:8000 --workers 3 --worker-class gevent
    environment:
      - DATABASE_URL=postgresql://dbuser:${DB_PASSWORD}@db:5432/maori_story
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DJANGO_DEBUG=False
      - ALLOWED_HOSTS=*
      - MEDIA_ROOT=/app/media
      - STATIC_ROOT=/app/staticfiles
    volumes:
      - media_data:/app/media
      - static_data:/app/staticfiles
    depends_on:
      db:
        condition: service_healthy
    networks:
      - maori-network

  frontend:
    image: your-dockerhub-username/maori-frontend:arm64
    container_name: maori-frontend
    restart: unless-stopped
    networks:
      - maori-network

  nginx:
    image: nginx:alpine
    container_name: maori-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - media_data:/usr/share/nginx/media:ro
      - static_data:/usr/share/nginx/static:ro
    depends_on:
      - backend
      - frontend
    networks:
      - maori-network

volumes:
  postgres_data:
    driver: local
  media_data:
    driver: local
  static_data:
    driver: local

networks:
  maori-network:
    driver: bridge
```

### Step 7: 创建 Nginx 配置

创建 `nginx.prod.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name _;

        client_max_body_size 50M;

        # 媒体文件（从volume挂载）
        location /media/ {
            alias /usr/share/nginx/media/;
            expires 7d;
            add_header Cache-Control "public, immutable";
        }

        # 静态文件
        location /static/ {
            alias /usr/share/nginx/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # API请求
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Admin后台
        location /admin/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # 前端SPA
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### Step 8: 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
# 数据库密码（请修改为强密码）
DB_PASSWORD=your_strong_password_here

# Django密钥（运行下面命令生成）
DJANGO_SECRET_KEY=your_django_secret_key_here

# 其他配置
DJANGO_DEBUG=False
EOF

# 生成Django密钥
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# 将输出复制到 .env 文件的 DJANGO_SECRET_KEY
```

### Step 9: 启动服务

```bash
# 拉取镜像
docker compose -f docker-compose.prod.yml pull

# 启动所有服务
docker compose -f docker-compose.prod.yml up -d

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 等待数据库启动（约10秒）
sleep 10

# 运行数据库迁移
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 创建超级用户
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 收集静态文件
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### Step 10: 验证部署

```bash
# 检查所有容器状态
docker compose -f docker-compose.prod.yml ps

# 测试API
curl http://localhost/api/stories/

# 测试前端（在浏览器访问）
# http://<ORACLE_VM_IP>
```

---

## 📊 资源使用监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 查看Docker卷
docker volume ls
du -sh /var/lib/docker/volumes/*
```

---

## 🔧 日常运维

### 备份数据库

```bash
# 创建备份目录
mkdir -p ~/backups

# 备份数据库
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U dbuser maori_story > ~/backups/db_backup_$(date +%Y%m%d).sql

# 备份媒体文件
sudo tar -czf ~/backups/media_backup_$(date +%Y%m%d).tar.gz \
  /var/lib/docker/volumes/maori-story-fill_media_data
```

### 恢复数据库

```bash
# 停止backend（避免写入冲突）
docker compose -f docker-compose.prod.yml stop backend

# 恢复数据库
cat ~/backups/db_backup_20241201.sql | \
  docker compose -f docker-compose.prod.yml exec -T db \
  psql -U dbuser maori_story

# 重启backend
docker compose -f docker-compose.prod.yml start backend
```

### 更新应用

```bash
# 拉取最新代码
cd ~/maori-story-fill
git pull origin main

# 重新构建并部署
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# 运行迁移
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### 查看日志

```bash
# 实时查看所有日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f backend

# 查看最近100行日志
docker compose -f docker-compose.prod.yml logs --tail=100
```

---

## 🛡️ 安全加固

### 1. 配置 HTTPS（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书（需要域名指向VM）
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 2. 配置防火墙

```bash
# 使用UFW（推荐）
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 检查状态
sudo ufw status
```

### 3. 禁用Django DEBUG模式

确保 `.env` 文件中：
```bash
DJANGO_DEBUG=False
```

### 4. 限制Admin访问

在 `nginx.prod.conf` 中添加IP白名单：
```nginx
location /admin/ {
    allow YOUR_IP_ADDRESS;
    deny all;
    proxy_pass http://backend;
}
```

---

## 🔄 CI/CD 自动化

### 使用 GitHub Actions 自动部署

创建 `.github/workflows/deploy-oracle.yml`:

```yaml
name: Deploy to Oracle Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and Push ARM64 Images
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin

          docker buildx create --use

          cd backend
          docker buildx build --platform linux/arm64 \
            -t ${{ secrets.DOCKER_USERNAME }}/maori-backend:arm64 \
            --push .

          cd ../frontend
          docker buildx build --platform linux/arm64 \
            -t ${{ secrets.DOCKER_USERNAME }}/maori-frontend:arm64 \
            --push .

      - name: Deploy to Oracle VM
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.ORACLE_VM_IP }}
          username: ubuntu
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            cd ~/maori-story-fill
            git pull origin main
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d
            docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate
            docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput
```

**需要配置的GitHub Secrets**:
- `DOCKER_USERNAME`: Docker Hub用户名
- `DOCKER_PASSWORD`: Docker Hub密码
- `ORACLE_VM_IP`: Oracle VM公网IP
- `ORACLE_SSH_KEY`: SSH私钥（~/.ssh/id_rsa的内容）

---

## 📈 性能优化

### 1. 数据库连接池

在 `backend/maori_story_project/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'maori_story',
        'USER': 'dbuser',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'db',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # 连接池
    }
}
```

### 2. Nginx缓存

在 `nginx.prod.conf` 添加：
```nginx
http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

    server {
        location /api/stories/ {
            proxy_cache api_cache;
            proxy_cache_valid 200 5m;
            proxy_pass http://backend;
        }
    }
}
```

### 3. 启用Gzip压缩

```nginx
http {
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
```

---

## ❓ 故障排查

### 问题1: 无法访问网站

```bash
# 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 检查Nginx日志
docker compose -f docker-compose.prod.yml logs nginx

# 检查防火墙
sudo iptables -L -n | grep 80
sudo ufw status

# 检查Oracle Cloud安全规则（在Console中）
```

### 问题2: 数据库连接失败

```bash
# 检查数据库容器
docker compose -f docker-compose.prod.yml logs db

# 手动测试连接
docker compose -f docker-compose.prod.yml exec db psql -U dbuser -d maori_story

# 检查环境变量
docker compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

### 问题3: 媒体文件无法加载

```bash
# 检查volume挂载
docker volume inspect maori-story-fill_media_data

# 检查文件权限
docker compose -f docker-compose.prod.yml exec backend ls -la /app/media

# 检查Nginx配置
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

---

## 💡 成本优化建议

虽然Oracle Cloud是免费的，但仍可以优化资源使用：

1. **镜像优化**
   - 使用Alpine基础镜像
   - 多阶段构建减小镜像大小
   - 定期清理未使用的镜像：`docker system prune -a`

2. **日志管理**
   - 限制Docker日志大小：`docker-compose.yml` 中添加
     ```yaml
     logging:
       options:
         max-size: "10m"
         max-file: "3"
     ```

3. **存储清理**
   - 定期清理旧备份
   - 压缩媒体文件
   - 删除未使用的Docker卷

---

## 🎉 完成检查清单

- [ ] Oracle Cloud账号注册成功
- [ ] VM实例创建并运行
- [ ] 安全规则配置正确（端口22, 80, 443）
- [ ] Docker和Docker Compose安装
- [ ] ARM64镜像构建并推送
- [ ] Docker Compose配置文件创建
- [ ] 环境变量配置
- [ ] 所有容器启动成功
- [ ] 数据库迁移完成
- [ ] 超级用户创建
- [ ] 网站可访问（http://<VM-IP>）
- [ ] API正常响应
- [ ] 媒体文件可加载
- [ ] 备份脚本配置
- [ ] （可选）域名和HTTPS配置

---

## 📚 参考资源

- Oracle Cloud文档: https://docs.oracle.com/en-us/iaas/
- Docker Compose文档: https://docs.docker.com/compose/
- Django部署检查清单: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- Let's Encrypt: https://letsencrypt.org/

---

## 🆘 需要帮助？

如果遇到问题，请提供以下信息：
1. 错误日志：`docker compose logs`
2. 容器状态：`docker compose ps`
3. 系统资源：`docker stats`
4. 具体错误信息

祝部署顺利！🚀
