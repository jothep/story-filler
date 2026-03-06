#!/bin/bash

# ============================================
# 查看 EC2 实例状态脚本
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

echo -e "${GREEN}📊 EC2 实例状态${NC}"
echo "================================"
echo ""

# 获取实例详细信息
INSTANCE_INFO=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --output json)

# 提取关键信息
STATE=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].State.Name')
INSTANCE_TYPE=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].InstanceType')
PUBLIC_IP=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].PublicIpAddress // "N/A"')
LAUNCH_TIME=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].LaunchTime')
AZ=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].Placement.AvailabilityZone')

# 显示状态（带颜色）
echo -n "状态: "
case $STATE in
    "running")
        echo -e "${GREEN}$STATE ✅${NC}"
        ;;
    "stopped")
        echo -e "${RED}$STATE 🛑${NC}"
        ;;
    "pending"|"stopping")
        echo -e "${YELLOW}$STATE ⏳${NC}"
        ;;
    *)
        echo "$STATE"
        ;;
esac

echo "实例 ID: $INSTANCE_ID"
echo "实例类型: $INSTANCE_TYPE"
echo "公网 IP: $PUBLIC_IP"
echo "可用区: $AZ"
echo "启动时间: $LAUNCH_TIME"
echo ""

# 如果实例正在运行，显示访问信息
if [ "$STATE" = "running" ]; then
    echo -e "${GREEN}🔗 访问信息:${NC}"
    echo "  网站: http://$PUBLIC_IP"
    echo "  API: http://$PUBLIC_IP/api/stories/"
    echo "  Admin: http://$PUBLIC_IP/admin/"
    echo "  SSH: ssh -i ~/.ssh/your-key.pem ubuntu@$PUBLIC_IP"
    echo ""

    # 计算运行时长
    CURRENT_TIME=$(date -u +%s)
    LAUNCH_TIME_UNIX=$(date -d "$LAUNCH_TIME" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "${LAUNCH_TIME%.*}" +%s 2>/dev/null || echo "0")

    if [ "$LAUNCH_TIME_UNIX" != "0" ]; then
        RUNNING_SECONDS=$((CURRENT_TIME - LAUNCH_TIME_UNIX))
        RUNNING_HOURS=$((RUNNING_SECONDS / 3600))
        RUNNING_MINUTES=$(((RUNNING_SECONDS % 3600) / 60))

        echo -e "${YELLOW}⏱️  运行时长: ${RUNNING_HOURS}小时 ${RUNNING_MINUTES}分钟${NC}"

        # 估算当前成本
        HOURLY_RATE=0.0208
        CURRENT_COST=$(echo "$RUNNING_HOURS * $HOURLY_RATE" | bc)
        echo -e "${YELLOW}💰 本次运行成本: \$${CURRENT_COST}${NC}"
    fi
    echo ""
fi

# 显示操作命令
echo -e "${GREEN}🔧 管理命令:${NC}"
if [ "$STATE" = "running" ]; then
    echo "  停止实例: ./stop-instance.sh"
elif [ "$STATE" = "stopped" ]; then
    echo "  启动实例: ./start-instance.sh"
fi
echo "  查看日志: ssh ubuntu@$PUBLIC_IP 'cd ~/maori-story-fill && docker compose -f docker-compose.prod.yml logs -f'"
echo ""
