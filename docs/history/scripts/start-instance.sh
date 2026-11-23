#!/bin/bash

# ============================================
# 启动 EC2 实例脚本
# ============================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 从 Terraform 输出获取实例 ID
INSTANCE_ID=$(cd ../terraform && terraform output -raw instance_id 2>/dev/null)

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${YELLOW}⚠️  无法从 Terraform 获取实例 ID${NC}"
    echo "请手动指定实例 ID："
    echo "用法: $0 <instance-id>"

    if [ -n "$1" ]; then
        INSTANCE_ID=$1
    else
        exit 1
    fi
fi

echo -e "${GREEN}🚀 启动 EC2 实例...${NC}"
echo "实例 ID: $INSTANCE_ID"

# 启动实例
aws ec2 start-instances --instance-ids "$INSTANCE_ID"

echo -e "${YELLOW}⏳ 等待实例启动...${NC}"

# 等待实例运行
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# 获取公网 IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo -e "${GREEN}✅ 实例启动成功！${NC}"
echo ""
echo -e "${GREEN}📊 实例信息:${NC}"
echo "  实例 ID: $INSTANCE_ID"
echo "  公网 IP: $PUBLIC_IP"
echo ""
echo -e "${GREEN}🔗 访问地址:${NC}"
echo "  网站: http://$PUBLIC_IP"
echo "  SSH:  ssh -i ~/.ssh/your-key.pem ubuntu@$PUBLIC_IP"
echo ""
echo -e "${YELLOW}💡 提示: 实例启动后，Docker 容器会自动启动（约需30秒）${NC}"
