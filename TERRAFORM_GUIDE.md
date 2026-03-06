# 🏗️ Maori Story Fill - Terraform 部署指南

## 📋 目录

1. [前置准备](#前置准备)
2. [快速开始](#快速开始)
3. [详细步骤](#详细步骤)
4. [成本估算](#成本估算)
5. [实例管理](#实例管理)
6. [故障排查](#故障排查)

---

## 前置准备

### 1. 安装必要工具

#### Terraform
```bash
# macOS (使用 Homebrew)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# 验证安装
terraform --version
```

#### AWS CLI
```bash
# macOS
brew install awscli

# 配置 AWS CLI
aws configure
# 输入: AWS Access Key ID
#      AWS Secret Access Key
#      Default region: us-east-1
#      Default output format: json
```

### 2. 创建 SSH 密钥对

```bash
# 在 AWS 中创建密钥对
aws ec2 create-key-pair \
  --key-name maori-story-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/maori-story-key.pem

# 设置正确的权限
chmod 400 ~/.ssh/maori-story-key.pem

# 或者在 AWS Console 创建：
# EC2 > Network & Security > Key Pairs > Create key pair
```

### 3. 准备配置文件

```bash
cd terraform

# 复制变量模板
cp terraform.tfvars.example terraform.tfvars

# 编辑配置文件
vim terraform.tfvars
```

**必须修改的配置**：
- `key_pair_name`: 你的 SSH 密钥对名称
- `db_password`: 数据库密码（强密码）
- `django_secret_key`: Django 密钥（50+ 字符）
- `git_repo_url`: 你的 Git 仓库地址

**生成 Django 密钥**：
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 快速开始

### 一键部署（5分钟）

```bash
# 1. 进入 terraform 目录
cd terraform

# 2. 初始化 Terraform
terraform init

# 3. 预览将要创建的资源
terraform plan

# 4. 应用配置（创建资源）
terraform apply

# 输入 'yes' 确认
```

### 部署完成后

Terraform 会输出所有重要信息：

```
Outputs:

connection_info = {
  ssh_command = "ssh -i ~/.ssh/maori-story-key.pem ubuntu@<PUBLIC_IP>"
  web_url     = "http://<PUBLIC_IP>"
  admin_url   = "http://<PUBLIC_IP>/admin/"
  api_url     = "http://<PUBLIC_IP>/api/stories/"
}

instance_details = {
  instance_id   = "i-xxxxxxxxx"
  instance_type = "t3.small"
  public_ip     = "<PUBLIC_IP>"
  ...
}

management_commands = {
  start  = "aws ec2 start-instances --instance-ids i-xxxxxxxxx"
  stop   = "aws ec2 stop-instances --instance-ids i-xxxxxxxxx"
  status = "aws ec2 describe-instance-status --instance-ids i-xxxxxxxxx"
}

cost_estimate = {
  estimated_total_160h = "~$7-10/月 (160小时使用)"
  estimated_total_full = "~$19-22/月 (全月运行)"
}
```

---

## 详细步骤

### Step 1: 初始化 Terraform

```bash
cd terraform
terraform init
```

这会：
- 下载 AWS provider 插件
- 初始化后端配置
- 创建 `.terraform` 目录

### Step 2: 验证配置

```bash
# 检查语法
terraform validate

# 格式化代码
terraform fmt

# 预览将要创建的资源
terraform plan
```

输出示例：
```
Plan: 7 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + instance_details = {
      + instance_id   = (known after apply)
      + instance_type = "t3.small"
      + public_ip     = (known after apply)
    }
```

### Step 3: 应用配置

```bash
terraform apply

# 或者跳过确认（自动化部署）
terraform apply -auto-approve
```

**创建的资源**：
1. ✅ Security Group（安全组）
2. ✅ EC2 Instance（t3.small）
3. ✅ EBS Volume（30GB gp3）
4. ✅ Elastic IP（固定公网IP）
5. ✅ IAM Role（可选，用于 CloudWatch）
6. ✅ CloudWatch Alarms（可选）

### Step 4: 等待初始化完成

实例启动后，`user-data.sh` 会自动执行：
- 安装 Docker
- 克隆代码
- 构建镜像
- 启动容器
- 初始化数据库

**监控进度**：
```bash
# SSH 连接
ssh -i ~/.ssh/maori-story-key.pem ubuntu@<PUBLIC_IP>

# 查看初始化日志
tail -f /var/log/cloud-init-output.log

# 检查完成标记
ls -la /var/log/maori-story-init-complete
```

初始化时间约：**5-10分钟**

### Step 5: 验证部署

```bash
# 1. 检查容器状态
ssh ubuntu@<PUBLIC_IP> 'docker compose -f ~/maori-story-fill/docker-compose.prod.yml ps'

# 2. 测试 API
curl http://<PUBLIC_IP>/api/stories/

# 3. 访问前端
open http://<PUBLIC_IP>
```

### Step 6: 创建管理员账号

```bash
ssh ubuntu@<PUBLIC_IP>
cd ~/maori-story-fill
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

---

## 成本估算

### 按使用时长计费

| 使用场景 | 月使用时长 | EC2 成本 | EBS 成本 | 总成本 |
|---------|----------|---------|---------|--------|
| **测试环境** | 40小时 | $0.83 | $2.40 | **$4.73** |
| **兼职项目** | 160小时 | $3.33 | $2.40 | **$7.23** |
| **半时使用** | 365小时 | $7.59 | $2.40 | **$11.49** |
| **全天运行** | 730小时 | $15.18 | $2.40 | **$19.08** |

### 成本优化建议

1. **不使用时停止实例**
   ```bash
   # 停止实例（节省 78% EC2 费用）
   aws ec2 stop-instances --instance-ids <INSTANCE_ID>
   ```

2. **使用 gp3 而非 gp2**
   - 已在 Terraform 中配置
   - 节省 20% 存储成本

3. **选择 us-east-1 区域**
   - 全球最便宜的区域
   - 已在配置中默认

4. **Elastic IP 保持绑定**
   - 绑定时免费
   - 未绑定：$3.65/月
   - 已在 Terraform 中自动绑定

---

## 实例管理

### 启动实例

```bash
# 方法 1: 使用脚本
cd scripts
./start-instance.sh

# 方法 2: 使用 AWS CLI
aws ec2 start-instances --instance-ids <INSTANCE_ID>

# 方法 3: 从 Terraform 输出获取命令
cd terraform
terraform output -raw management_commands | jq -r '.start' | bash
```

### 停止实例

```bash
# 方法 1: 使用脚本（带确认）
cd scripts
./stop-instance.sh

# 方法 2: 使用 AWS CLI
aws ec2 stop-instances --instance-ids <INSTANCE_ID>
```

### 查看实例状态

```bash
# 使用脚本（推荐）
cd scripts
./instance-status.sh

# 使用 AWS CLI
aws ec2 describe-instances --instance-ids <INSTANCE_ID> \
  --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
  --output table
```

### 重启实例

```bash
aws ec2 reboot-instances --instance-ids <INSTANCE_ID>
```

### 终止实例（危险！）

```bash
# 使用 Terraform 销毁所有资源
cd terraform
terraform destroy

# 或者手动终止（不推荐）
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>
```

---

## Terraform 常用命令

### 查看输出

```bash
# 查看所有输出
terraform output

# 查看特定输出
terraform output instance_id
terraform output instance_public_ip

# 以 JSON 格式输出
terraform output -json
```

### 更新基础设施

```bash
# 1. 修改 terraform.tfvars 或 main.tf

# 2. 预览变更
terraform plan

# 3. 应用变更
terraform apply
```

### 导入现有资源

```bash
# 如果你已经手动创建了 EC2 实例，可以导入到 Terraform
terraform import aws_instance.maori_story i-xxxxxxxxx
```

### 查看状态

```bash
# 列出所有资源
terraform state list

# 查看特定资源详情
terraform state show aws_instance.maori_story

# 查看当前状态
terraform show
```

### 刷新状态

```bash
# 从 AWS 同步最新状态
terraform refresh
```

---

## 故障排查

### 问题 1: Terraform init 失败

**错误**：`Error: Failed to download provider`

**解决**：
```bash
# 清理缓存
rm -rf .terraform .terraform.lock.hcl

# 重新初始化
terraform init
```

### 问题 2: SSH 密钥对不存在

**错误**：`InvalidKeyPair.NotFound`

**解决**：
```bash
# 检查密钥对是否存在
aws ec2 describe-key-pairs

# 创建密钥对
aws ec2 create-key-pair --key-name maori-story-key \
  --query 'KeyMaterial' --output text > ~/.ssh/maori-story-key.pem
chmod 400 ~/.ssh/maori-story-key.pem

# 更新 terraform.tfvars
key_pair_name = "maori-story-key"
```

### 问题 3: VPC 或 Subnet 不存在

**错误**：`InvalidSubnetID.NotFound`

**解决**：
```bash
# 查看默认 VPC
aws ec2 describe-vpcs --filters "Name=is-default,Values=true"

# 查看子网
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<VPC_ID>"

# 在 terraform.tfvars 中留空使用默认值
vpc_id = ""
subnet_id = ""
```

### 问题 4: 无法访问网站

**检查清单**：

1. **实例是否运行**
   ```bash
   aws ec2 describe-instance-status --instance-ids <INSTANCE_ID>
   ```

2. **安全组规则是否正确**
   ```bash
   aws ec2 describe-security-groups --group-ids <SG_ID>
   ```

3. **初始化是否完成**
   ```bash
   ssh ubuntu@<PUBLIC_IP> 'ls -la /var/log/maori-story-init-complete'
   ```

4. **容器是否运行**
   ```bash
   ssh ubuntu@<PUBLIC_IP> 'docker compose -f ~/maori-story-fill/docker-compose.prod.yml ps'
   ```

5. **查看日志**
   ```bash
   ssh ubuntu@<PUBLIC_IP> 'tail -100 /var/log/cloud-init-output.log'
   ```

### 问题 5: Terraform 状态锁定

**错误**：`Error: Error acquiring the state lock`

**解决**：
```bash
# 强制解锁（谨慎使用）
terraform force-unlock <LOCK_ID>
```

---

## 高级配置

### 使用 S3 后端存储状态

编辑 `main.tf`：

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "maori-story/terraform.tfstate"
    region = "us-east-1"

    # 启用状态锁定
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

创建 S3 bucket：
```bash
aws s3 mb s3://your-terraform-state-bucket
```

### 启用 CloudWatch 告警

在 `terraform.tfvars` 中：
```hcl
enable_cloudwatch_alarms = true

# 可选：创建 SNS Topic 接收告警
# alarm_sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:maori-story-alerts"
```

### 多环境部署

```bash
# 创建工作空间
terraform workspace new prod
terraform workspace new staging

# 切换工作空间
terraform workspace select prod

# 应用配置
terraform apply
```

---

## 安全最佳实践

### 1. 限制 SSH 访问

在 `terraform.tfvars` 中：
```hcl
# 只允许你的 IP 访问
allowed_ssh_cidrs = ["YOUR_IP/32"]

# 查看你的公网 IP
curl ifconfig.me
```

### 2. 启用 HTTPS

部署后配置 Let's Encrypt：
```bash
ssh ubuntu@<PUBLIC_IP>
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 定期更新系统

```bash
ssh ubuntu@<PUBLIC_IP>
sudo apt update && sudo apt upgrade -y
```

### 4. 启用 EBS 加密

已在 Terraform 中默认启用：
```hcl
root_block_device {
  encrypted = true
}
```

---

## 清理资源

### 销毁所有资源

```bash
cd terraform

# 预览将要删除的资源
terraform plan -destroy

# 销毁资源
terraform destroy

# 或者自动确认
terraform destroy -auto-approve
```

**注意**：
- 这会删除 EC2 实例、安全组、Elastic IP 等所有资源
- EBS 卷配置为 `delete_on_termination = false`，需要手动删除
- 确保已备份重要数据！

---

## 常见问题

**Q: 停止实例后还会产生费用吗？**
A: 是的，EBS 存储会继续计费（$2.40/月），但 EC2 计算费用会停止。

**Q: 如何更换实例类型？**
A: 修改 `terraform.tfvars` 中的 `instance_type`，然后运行 `terraform apply`。

**Q: 数据会丢失吗？**
A: 不会。EBS 卷配置为实例终止时不删除，数据永久保存。

**Q: 如何备份数据？**
A: SSH 到实例后运行 `~/maori-story-fill/backup.sh`。

**Q: 可以在其他区域部署吗？**
A: 可以，修改 `aws_region` 变量，但成本可能更高。

---

## 下一步

✅ **Terraform 部署完成后**：

1. 访问网站测试功能
2. 创建超级用户并登录 Admin
3. 上传测试故事和素材
4. 配置定期备份（cron）
5. （可选）配置域名和 HTTPS
6. （可选）设置 CloudWatch 监控

**祝使用愉快！🎉**
