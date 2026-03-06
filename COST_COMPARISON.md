# Maori Story Fill - 云部署成本对比

## 项目需求分析

### 资源需求评估
- **计算**: 前端(Nginx) + 后端(Django) - 估计 1-2GB RAM, 1-2 vCPU
- **数据库**: PostgreSQL - 估计 500MB-1GB RAM
- **存储**: 媒体文件（图片、音频） - 估计 5-20GB
- **流量**: 假设小型应用 - 50GB/月出站流量

---

## 方案对比总览

| 方案 | 月成本 (USD) | 适用场景 | 推荐指数 |
|------|-------------|---------|----------|
| **🏆 Oracle Cloud Free Tier** | **$0** | 永久免费，适合低流量 | ⭐⭐⭐⭐⭐ |
| **AWS Lightsail** | **$5-12** | 简单易用，固定价格 | ⭐⭐⭐⭐⭐ |
| **Hetzner VPS** | **€4.5 (~$5)** | 性价比最高 | ⭐⭐⭐⭐⭐ |
| **DigitalOcean Droplet** | **$6-12** | 开发者友好 | ⭐⭐⭐⭐ |
| **Railway (PaaS)** | **$5-10** | 零配置部署 | ⭐⭐⭐⭐ |
| **方案1: 单EC2 All-in-One** | **$15-25** | 完全控制 | ⭐⭐⭐ |
| **方案2: AWS ECS Fargate** | **$25-40** | 托管容器 | ⭐⭐ |
| **Render.com (PaaS)** | **$7-21** | 自动部署 | ⭐⭐⭐ |
| **Fly.io** | **$5-15** | 全球分发 | ⭐⭐⭐⭐ |

---

## 🥇 最佳方案：Oracle Cloud Free Tier（永久免费！）

### 配置
```
Oracle Cloud Always Free Tier:
├── 2x AMD Compute (Ampere A1)
│   ├── 4 OCPU (ARM64)
│   ├── 24 GB RAM（可分配给多个实例）
│   └── 永久免费
├── Block Storage: 200 GB（免费）
├── 出站流量: 10 TB/月（免费）
└── Object Storage: 20 GB（免费）
```

### 实际配置建议
```yaml
# 创建1个VM实例
Instance Type: VM.Standard.A1.Flex
- OCPU: 2 (ARM64)
- RAM: 12 GB
- Storage: 100 GB Block Volume
- OS: Ubuntu 22.04 ARM64

部署架构:
├── Docker Compose
│   ├── Frontend (Nginx) - 256MB RAM
│   ├── Backend (Gunicorn) - 512MB RAM
│   └── PostgreSQL - 1GB RAM
├── 文件存储: /opt/maori-story/media (本地存储)
└── Nginx 反向代理
```

### 💰 月成本
- **$0** （永久免费）
- 仅需支付域名费用（可选，~$12/年）

### 优点
✅ **完全免费**
✅ 性能强劲（24GB RAM可分配）
✅ ARM架构（能效高）
✅ 200GB存储足够媒体文件
✅ 10TB流量远超需求

### 缺点
❌ 注册需要信用卡验证
❌ ARM架构需要重新构建镜像
❌ 部分地区可能资源紧张
❌ UI相对复杂

### 部署步骤
```bash
# 1. Docker支持ARM的多架构构建
docker buildx create --use
docker buildx build --platform linux/arm64 -t maori-backend:arm64 ./backend
docker buildx build --platform linux/arm64 -t maori-frontend:arm64 ./frontend

# 2. 在Oracle VM上部署
ssh ubuntu@<oracle-vm-ip>
sudo apt update && sudo apt install docker.io docker-compose-v2 -y
git clone <your-repo>
cd maori-story-fill
docker-compose up -d
```

---

## 🥈 次佳方案：AWS Lightsail（简化版EC2）

### 配置
```
AWS Lightsail Instance:
├── Plan: $12/月
│   ├── 2 GB RAM
│   ├── 1 vCPU
│   ├── 60 GB SSD
│   └── 3 TB 流量
└── Managed PostgreSQL: $15/月（可选）
```

### 部署架构（推荐配置）
```yaml
选项A: All-in-One ($12/月)
├── Lightsail Instance: $12
│   ├── Frontend Container
│   ├── Backend Container
│   ├── PostgreSQL Container
│   └── 媒体文件存储（60GB SSD）
└── 总成本: $12/月

选项B: 分离数据库 ($27/月)
├── Lightsail Instance: $12
├── Lightsail Database (PostgreSQL): $15
└── 总成本: $27/月
```

### 💰 月成本
- **选项A (推荐): $12/月**
- 选项B: $27/月（数据库独立，更稳定）

### 优点
✅ **固定价格**，流量包含在内
✅ AWS生态系统，易于扩展
✅ 简单的UI和管理
✅ 自动快照备份
✅ 内置防火墙和监控

### 缺点
❌ 性能不如标准EC2
❌ 可定制性较低
❌ 扩展需要重建实例

### 部署步骤
```bash
# 1. 创建Lightsail实例
aws lightsail create-instances \
  --instance-names maori-story \
  --availability-zone us-east-1a \
  --blueprint ubuntu_22_04 \
  --bundle-id medium_2_0

# 2. SSH连接并部署
ssh ubuntu@<lightsail-ip>
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
git clone <your-repo>
cd maori-story-fill
docker-compose up -d
```

---

## 🥉 性价比之王：Hetzner VPS

### 配置
```
Hetzner Cloud CX21:
├── 价格: €4.51/月 (~$5 USD)
├── 2 vCPU (AMD)
├── 4 GB RAM
├── 40 GB SSD
└── 20 TB 流量
```

### 💰 月成本
- **€4.51 (~$5 USD)**

### 优点
✅ **极致性价比**（4GB RAM仅$5）
✅ 欧洲数据中心（德国、芬兰）
✅ 流量超大（20TB）
✅ 简单易用
✅ 支持快照和自动备份（+€0.90/月）

### 缺点
❌ 数据中心仅在欧洲（亚太延迟高）
❌ 不支持中文客服
❌ 支付需要信用卡/PayPal

---

## 方案1: 单EC2 All-in-One（标准AWS EC2）

### 配置
```
AWS EC2 t3.small:
├── 实例费用: $15.18/月
│   ├── 2 vCPU
│   ├── 2 GB RAM
│   └── EBS: 30 GB gp3 ($2.40/月)
├── 数据传输: 50GB 出站 ($4.50/月)
└── Elastic IP: $0（使用中免费）
```

### 部署架构
```yaml
EC2 Instance (t3.small):
├── Docker Compose
│   ├── Frontend (Nginx)
│   ├── Backend (Gunicorn)
│   └── PostgreSQL (容器)
├── 存储: EBS 30GB (系统 + DB + 媒体文件)
└── Nginx 反向代理 :80
```

### 💰 月成本
- **$22-25/月**

### 优点
✅ 完全控制系统
✅ 可扩展到更大实例
✅ AWS全球CDN可选
✅ 与其他AWS服务集成

### 缺点
❌ 比Lightsail贵近2倍
❌ 需要手动配置安全组、IAM等
❌ 流量按量计费（不可预测）
❌ EBS需要单独管理

### 部署步骤
```bash
# 1. 启动EC2实例
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.small \
  --key-name my-key \
  --security-group-ids sg-xxx \
  --block-device-mappings '[
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 30,
        "VolumeType": "gp3"
      }
    }
  ]'

# 2. 部署应用
ssh -i my-key.pem ec2-user@<ec2-ip>
sudo yum install docker -y
sudo systemctl start docker
sudo usermod -aG docker ec2-user
# ... 部署步骤同上
```

---

## 方案2: AWS ECS Fargate

### 配置
```
AWS ECS Fargate:
├── Frontend Task
│   ├── 0.25 vCPU, 512 MB RAM
│   └── 费用: ~$9/月
├── Backend Task
│   ├── 0.5 vCPU, 1 GB RAM
│   └── 费用: ~$18/月
├── Application Load Balancer: $16/月
├── EFS (媒体存储): 5GB = $1.50/月
└── 数据传输: $4/月
```

### 💰 月成本
- **$48-55/月**（太贵！）

### 优点
✅ 完全托管，无需维护服务器
✅ 自动扩展
✅ 高可用性
✅ 与AWS服务深度集成

### 缺点
❌ **成本最高**
❌ 需要学习ECS概念
❌ ALB必须使用（$16/月固定成本）
❌ EFS性能一般且按量计费
❌ 冷启动时间较长

### 不推荐原因
对于小型应用，Fargate的成本远高于VPS方案，且复杂度更高。

---

## 🌟 PaaS方案对比

### Railway.app
```yaml
配置:
├── Hobby Plan: $5/月
├── 资源: $5 免费额度 + 超出按量
│   ├── RAM: 512MB 起
│   ├── CPU: 共享
│   └── 存储: 5GB
└── PostgreSQL插件: $5/月起
```

**月成本**: $5-10/月（小流量免费）

**优点**:
✅ 零配置部署（连接GitHub自动部署）
✅ 内置PostgreSQL
✅ 自动HTTPS证书
✅ 简单的UI

**缺点**:
❌ 资源限制（超出需付费）
❌ 不适合大文件存储
❌ 美国数据中心（延迟）

### Render.com
```yaml
配置:
├── Web Service (Starter): $7/月
├── PostgreSQL (Starter): $7/月
├── 存储: 不支持持久化（需外部S3）
└── 总成本: $14/月 + S3费用
```

**月成本**: $14-20/月

**优点**:
✅ 自动部署和HTTPS
✅ 内置CI/CD
✅ Docker原生支持

**缺点**:
❌ 不支持容器内持久化存储
❌ 需要单独配置S3（增加成本）
❌ 数据库较贵

### Fly.io
```yaml
配置:
├── Shared CPU (256MB): $1.94/月
├── 每月免费额度: $5
├── PostgreSQL (Starter): $10/月
├── 存储卷: 1GB 免费，之后 $0.15/GB/月
└── 总成本: ~$8-15/月
```

**月成本**: $8-15/月

**优点**:
✅ 全球边缘网络（低延迟）
✅ 支持持久化存储卷
✅ 每月$5免费额度
✅ Docker原生

**缺点**:
❌ 配置相对复杂
❌ 文档不够详细
❌ 存储卷按量计费

---

## 其他值得考虑的方案

### DigitalOcean App Platform
- **成本**: $12/月（Basic）
- **优点**: 简单易用，自动部署
- **缺点**: 持久化存储需要额外配置Spaces（S3兼容，$5/月）

### DigitalOcean Droplet (VPS)
- **成本**: $6/月（1GB RAM）或 $12/月（2GB RAM）
- **优点**: 类似Lightsail，固定价格包含流量
- **缺点**: 性能不如Hetzner

### Vultr VPS
- **成本**: $6/月（1GB RAM）
- **优点**: 全球数据中心（包括亚洲）
- **缺点**: 流量限制（1TB/月）

---

## 📊 最终推荐方案对比

### 按成本排序

| 排名 | 方案 | 月成本 | 适用场景 |
|-----|------|--------|---------|
| 🥇 | Oracle Cloud Free Tier | **$0** | 永久免费项目，愿意折腾 |
| 🥈 | Hetzner VPS CX21 | **$5** | 欧洲用户，性价比最高 |
| 🥉 | Railway (小流量) | **$5-10** | 快速原型，零配置 |
| 4 | AWS Lightsail | **$12** | AWS生态，简单部署 |
| 5 | Fly.io | **$8-15** | 全球用户，低延迟 |
| 6 | 单EC2 (t3.small) | **$22-25** | 完全控制，AWS深度集成 |
| 7 | Render.com | **$14-20** | 开发者友好 |
| 8 | DigitalOcean Droplet | **$12** | 平衡选择 |
| 9 | AWS ECS Fargate | **$48-55** | 企业级，不差钱 |

---

## 🎯 我的最终推荐

### 如果你想要完全免费 → **Oracle Cloud Always Free**
- 永久0成本
- 需要一次性配置ARM架构
- 性能足够（24GB RAM可用）

### 如果你想要最简单 → **AWS Lightsail $12/月**
- 一键部署，固定价格
- AWS生态便于学习和扩展
- 流量包含（3TB）

### 如果你想要最便宜（付费） → **Hetzner VPS $5/月**
- 性价比无敌（4GB RAM）
- 适合欧洲用户或延迟不敏感场景

### 如果你想要零配置 → **Railway $5-10/月**
- 推送代码自动部署
- 内置数据库和HTTPS
- 适合快速上线

---

## ⚠️ 不推荐的方案

❌ **AWS ECS Fargate** - 成本是VPS的4-5倍
❌ **标准EC2** - 比Lightsail贵，配置复杂
❌ **Render.com** - 不支持持久化存储，需额外S3

---

## 🚀 快速决策流程图

```
开始
  ↓
是否愿意折腾（配置ARM架构）？
  ├─ 是 → Oracle Cloud Free Tier ($0)
  └─ 否 ↓
      ↓
是否需要全球低延迟？
  ├─ 是 → Fly.io ($8-15/月)
  └─ 否 ↓
      ↓
是否在欧洲或延迟不敏感？
  ├─ 是 → Hetzner VPS ($5/月)
  └─ 否 ↓
      ↓
是否需要零配置自动部署？
  ├─ 是 → Railway ($5-10/月)
  └─ 否 ↓
      ↓
是否希望使用AWS生态？
  ├─ 是 → AWS Lightsail ($12/月)
  └─ 否 ↓
      ↓
默认选择 → DigitalOcean Droplet ($12/月)
```

---

## 📋 下一步行动

1. **测试Oracle Cloud注册**（免费方案优先）
2. **如果Oracle不可用**，选择Lightsail或Hetzner
3. **准备ARM架构的Docker镜像**（如果选择Oracle）
4. **修改docker-compose配置**适配单机部署
5. **设置自动备份脚本**

---

## 成本节省技巧

1. **使用Cloudflare免费CDN**（加速+节省流量）
2. **媒体文件压缩**（减少存储空间）
3. **启用Gzip/Brotli压缩**（减少带宽）
4. **使用Reserved Instances**（AWS 1年期节省30%）
5. **监控资源使用**（避免超额费用）

---

## 总结

**最便宜方案**: Oracle Cloud Always Free Tier (**$0/月**)
**最简单方案**: AWS Lightsail (**$12/月**)
**性价比方案**: Hetzner VPS (**$5/月**)

建议先尝试Oracle Cloud，如果注册困难或资源紧张，再选择Lightsail或Hetzner作为备选。
