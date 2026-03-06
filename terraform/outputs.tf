# ============================================
# Maori Story Fill - Terraform Outputs
# ============================================

output "instance_details" {
  description = "EC2 实例详细信息"
  value = {
    instance_id   = aws_instance.maori_story.id
    instance_type = aws_instance.maori_story.instance_type
    ami_id        = aws_instance.maori_story.ami
    public_ip     = aws_eip.maori_story_eip.public_ip
    public_dns    = aws_instance.maori_story.public_dns
    availability_zone = aws_instance.maori_story.availability_zone
  }
}

output "network_details" {
  description = "网络配置信息"
  value = {
    security_group_id = aws_security_group.maori_story_sg.id
    elastic_ip        = aws_eip.maori_story_eip.public_ip
    vpc_id            = aws_security_group.maori_story_sg.vpc_id
  }
}

output "connection_info" {
  description = "连接信息"
  value = {
    ssh_command = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.maori_story_eip.public_ip}"
    web_url     = "http://${aws_eip.maori_story_eip.public_ip}"
    admin_url   = "http://${aws_eip.maori_story_eip.public_ip}/admin/"
    api_url     = "http://${aws_eip.maori_story_eip.public_ip}/api/stories/"
  }
}

output "cost_estimate" {
  description = "预估月度成本（USD）"
  value = {
    ec2_full_month       = "~$15.18 (730小时)"
    ec2_160_hours        = "~$3.33 (160小时/月)"
    ebs_storage          = "~$2.40 (30GB gp3)"
    elastic_ip_bound     = "$0 (绑定时免费)"
    estimated_total_160h = "~$7-10/月 (160小时使用)"
    estimated_total_full = "~$19-22/月 (全月运行)"
  }
}

output "management_commands" {
  description = "实例管理命令"
  value = {
    start = "aws ec2 start-instances --instance-ids ${aws_instance.maori_story.id}"
    stop  = "aws ec2 stop-instances --instance-ids ${aws_instance.maori_story.id}"
    status = "aws ec2 describe-instance-status --instance-ids ${aws_instance.maori_story.id}"
    ssh   = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.maori_story_eip.public_ip}"
  }
}

output "next_steps" {
  description = "部署后的后续步骤"
  value = <<-EOT

  ✅ Terraform 部署完成！

  📋 后续步骤：

  1️⃣  SSH 连接到实例：
     ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.maori_story_eip.public_ip}

  2️⃣  检查初始化状态（user-data 执行日志）：
     tail -f /var/log/cloud-init-output.log

  3️⃣  验证 Docker 安装：
     docker --version
     docker compose version

  4️⃣  检查应用状态：
     cd ~/maori-story-fill
     docker compose -f docker-compose.prod.yml ps

  5️⃣  访问应用：
     前端: http://${aws_eip.maori_story_eip.public_ip}
     API:  http://${aws_eip.maori_story_eip.public_ip}/api/stories/
     Admin: http://${aws_eip.maori_story_eip.public_ip}/admin/

  6️⃣  创建超级用户：
     docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

  💡 管理命令：
  - 启动实例: aws ec2 start-instances --instance-ids ${aws_instance.maori_story.id}
  - 停止实例: aws ec2 stop-instances --instance-ids ${aws_instance.maori_story.id}
  - 查看日志: docker compose -f docker-compose.prod.yml logs -f

  📊 成本优化：
  - 不使用时记得停止实例（节省 78% EC2 费用）
  - EBS 存储会持续计费（$2.40/月），即使实例停止
  - Elastic IP 保持绑定到实例（避免额外费用）

  EOT
}
