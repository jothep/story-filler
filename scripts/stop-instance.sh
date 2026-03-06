#!/bin/bash

# ============================================
# 停止 EC2 实例脚本
# ============================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

echo -e "${YELLOW}🛑 准备停止 EC2 实例...${NC}"
echo "实例 ID: $INSTANCE_ID"
echo ""

# 确认操作
read -p "确定要停止实例吗？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ 操作已取消${NC}"
    exit 0
fi

# 停止实例
echo -e "${YELLOW}⏳ 停止实例中...${NC}"
aws ec2 stop-instances --instance-ids "$INSTANCE_ID"

# 等待实例停止
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"

echo -e "${GREEN}✅ 实例已停止！${NC}"
echo ""
echo -e "${GREEN}💰 成本节省:${NC}"
echo "  - EC2 计费已停止（节省约 $0.0208/小时）"
echo "  - EBS 存储继续计费（$2.40/月）"
echo "  - Elastic IP 保持绑定（免费）"
echo ""
echo -e "${YELLOW}💡 提示: 数据已保留在 EBS 卷，可随时重新启动${NC}"
echo ""
echo -e "${GREEN}🔄 重新启动命令:${NC}"
echo "  ./start-instance.sh"
echo "  或: aws ec2 start-instances --instance-ids $INSTANCE_ID"
