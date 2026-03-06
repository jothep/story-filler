# Maori Story Fill - 重构计划

## 项目概述
将当前 Kubernetes 部署的架构简化为 EC2 + RDS + S3，降低 80% 运营成本（从 $150-200/月 降至 $32-35/月）

---

## 当前架构 vs 目标架构

### 当前架构（Kubernetes）
```
Kubernetes Cluster
├── Frontend Pod (React + Node)
├── Backend Pod (Django + Gunicorn)
├── PostgreSQL StatefulSet
├── Ingress Controller + Load Balancer
└── Persistent Volume (Media Storage)

月成本: $150-200
复杂度: 12个 manifest 文件
```

### 目标架构（EC2 + RDS + S3）
```
EC2 Instance (t3.small)
├── Docker Compose
│   ├── Frontend Container
│   ├── Backend Container
│   └── Nginx Reverse Proxy
├── RDS PostgreSQL (db.t3.micro)
└── S3 Bucket (Media Storage) + CloudFront CDN

月成本: $32-35
复杂度: 1个 docker-compose.yml
```

---

## Phase 1: 代码重构与优化 (1周)

### 1.1 后端改进
- [ ] 添加 S3 存储支持 (django-storages)
- [ ] 优化数据库查询（select_related, prefetch_related）
- [ ] 添加 API 错误处理和日志
- [ ] 实现媒体文件自动压缩
- [ ] 添加文件上传验证器
- [ ] 增加单元测试覆盖率（目标 60%+）

### 1.2 前端改进
- [ ] 添加 API 调用错误处理
- [ ] 实现 Loading 和 Error 状态
- [ ] 添加 React Error Boundary
- [ ] 优化打包配置（减小 bundle 大小）
- [ ] 移除硬编码的 BGM 路径
- [ ] 添加环境变量配置（.env）

### 1.3 配置文件准备
- [ ] 创建 docker-compose.yml（本地开发）
- [ ] 创建 docker-compose.prod.yml（生产部署）
- [ ] 创建 nginx.conf（反向代理配置）
- [ ] 创建 .env.example（环境变量模板）
- [ ] 创建 deploy.sh（EC2 部署脚本）
- [ ] 更新 README.md（新的部署说明）

---

## Phase 2: AWS 基础设施准备 (3天)

### 2.1 AWS 账户设置
- [ ] 创建 IAM 用户（EC2、RDS、S3 权限）
- [ ] 创建 S3 Bucket: `maori-story-media`
- [ ] 配置 S3 CORS 策略
- [ ] 设置 S3 生命周期策略（降低成本）
- [ ] （可选）创建 CloudFront Distribution

### 2.2 RDS 数据库
- [ ] 创建 RDS PostgreSQL 实例
  - Engine: PostgreSQL 16
  - Instance: db.t3.micro
  - Storage: 20GB gp3
  - Backup: 7天自动备份
  - Single-AZ（降低成本）
- [ ] 配置安全组（仅允许 EC2 访问）
- [ ] 测试数据库连接
- [ ] 导出当前 K8s 数据库数据（pg_dump）

### 2.3 EC2 实例
- [ ] 创建 EC2 实例
  - AMI: Amazon Linux 2023
  - Instance: t3.small
  - Storage: 30GB gp3
  - Security Group: 允许 80, 443, 22
- [ ] 安装 Docker 和 Docker Compose
- [ ] 配置 SSH 密钥
- [ ] 设置 Elastic IP（固定 IP）
- [ ] 配置 CloudWatch 告警

---

## Phase 3: 数据迁移 (2天)

### 3.1 数据库迁移
```bash
# 1. 从 K8s 导出数据
kubectl exec -n story-fill postgres-statefulset-0 -- \
  pg_dump -U dbuser maori_story > backup.sql

# 2. 导入到 RDS
psql -h <rds-endpoint> -U dbuser -d maori_story < backup.sql

# 3. 验证数据完整性
python manage.py check
python manage.py showmigrations
```

### 3.2 媒体文件迁移
```bash
# 1. 从 K8s PVC 复制媒体文件
kubectl cp story-fill/backend-pod:/app/media ./media_backup

# 2. 上传到 S3
aws s3 sync ./media_backup s3://maori-story-media/ \
  --storage-class INTELLIGENT_TIERING

# 3. 验证 S3 文件
aws s3 ls s3://maori-story-media/ --recursive | wc -l
```

### 3.3 DNS 切换准备
- [ ] 准备域名（如果有）
- [ ] 创建 A 记录指向 Elastic IP
- [ ] 配置 SSL 证书（Let's Encrypt）

---

## Phase 4: 部署与测试 (3天)

### 4.1 首次部署
```bash
# 1. SSH 到 EC2
ssh -i key.pem ec2-user@<elastic-ip>

# 2. 克隆代码
git clone https://github.com/your-repo/maori-story-fill.git
cd maori-story-fill

# 3. 配置环境变量
cp .env.example .env
vim .env  # 填写 RDS、S3 凭证

# 4. 启动容器
./deploy.sh
```

### 4.2 功能测试
- [ ] 测试故事列表 API: `/api/stories/`
- [ ] 测试故事详情 API: `/api/stories/1/`
- [ ] 测试前端路由（Menu → StoryPlayer → Congratulations）
- [ ] 测试媒体文件加载（图片、音频）
- [ ] 测试拖拽功能（DnD）
- [ ] 测试 Admin 后台
- [ ] 性能测试（响应时间 < 2s）

### 4.3 监控与日志
- [ ] 配置 CloudWatch Logs
- [ ] 设置 CPU/内存告警（>80%）
- [ ] 设置数据库连接数告警
- [ ] 配置错误日志聚合
- [ ] 设置每日备份验证

---

## Phase 5: CI/CD 更新 (2天)

### 5.1 更新 GitHub Actions

**新的 workflow: `.github/workflows/deploy-ec2.yml`**
```yaml
name: Deploy to EC2

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ec2-user
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ec2-user/maori-story-fill
            git pull origin main
            ./deploy.sh
```

### 5.2 清理 K8s 资源
- [ ] 备份所有 K8s manifest（存档）
- [ ] 停止 CD workflow
- [ ] 删除 Docker Hub 旧镜像（可选）
- [ ] 更新 README（移除 K8s 说明）

---

## Phase 6: 优化与监控 (持续)

### 6.1 性能优化
- [ ] 启用 CloudFront CDN（如果全球用户）
- [ ] 添加 Redis 缓存（可选，+$5/月）
- [ ] 优化前端 bundle（代码分割）
- [ ] 添加数据库索引
- [ ] 实现 API 响应缓存

### 6.2 成本优化
- [ ] 使用 S3 Intelligent-Tiering（自动降级）
- [ ] 设置 CloudWatch 日志保留期（7天）
- [ ] 删除未使用的快照
- [ ] 考虑 EC2 Reserved Instance（1年期，节省 30%）

### 6.3 安全加固
- [ ] 实施 API 速率限制
- [ ] 添加 WAF 规则（可选）
- [ ] 启用 S3 存储桶加密
- [ ] 配置自动安全更新
- [ ] 定期漏洞扫描

---

## 成本对比

| 项目 | K8s 成本 | EC2 成本 | 节省 |
|------|----------|----------|------|
| 计算资源 | $90-120 | $15 | 75% |
| 数据库 | $30-40 | $12 | 60% |
| 存储 | $5-10 | $3.50 | 50% |
| 负载均衡 | $20-30 | $0 | 100% |
| **总计** | **$150-200** | **$32-35** | **82%** |

---

## 回滚计划

如果迁移失败，可以快速回滚：

1. **K8s 环境保留 7 天**（不立即删除）
2. **数据库备份**每天自动执行
3. **DNS 快速切换**（TTL 设置为 300秒）
4. **媒体文件双写**（过渡期同时写 PVC 和 S3）

---

## 验收标准

- ✅ 所有 API 端点正常响应
- ✅ 前端功能完整可用
- ✅ 媒体文件加载速度 < 3秒
- ✅ 数据库查询延迟 < 100ms
- ✅ 月成本 < $40
- ✅ 系统可用性 > 99%
- ✅ 备份恢复测试通过

---

## 时间线

| 阶段 | 工作量 | 完成日期 |
|------|--------|---------|
| Phase 1: 代码重构 | 3-5天 | Week 1 |
| Phase 2: AWS 准备 | 2-3天 | Week 1 |
| Phase 3: 数据迁移 | 1-2天 | Week 2 |
| Phase 4: 部署测试 | 2-3天 | Week 2 |
| Phase 5: CI/CD 更新 | 1-2天 | Week 2 |
| Phase 6: 优化监控 | 持续 | Ongoing |

**总计: 2-3周完成主体迁移**

---

## 下一步行动

1. **立即开始**: 创建 S3 bucket 和 RDS 实例（可与代码重构并行）
2. **本周内**: 完成 Phase 1 代码改进
3. **下周内**: 完成数据迁移和首次部署

---

## 联系与支持

- 技术问题: 查看新的 README.md 部署指南
- AWS 资源: 使用 Terraform/CloudFormation 自动化（下一阶段）
- 监控告警: CloudWatch Dashboard 链接（部署后提供）
