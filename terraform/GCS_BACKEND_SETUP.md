# GCS Backend 配置指南

本项目使用 Google Cloud Storage (GCS) 存储 Terraform 状态文件。

## 配置信息

- **存储桶名称**: `jaskojothep-terraform-state`
- **状态文件路径**: `terraform/state/maori-story-fill`
- **完整GCS路径**: `gs://jaskojothep-terraform-state/terraform/state/maori-story-fill`

## 功能特性

✅ **版本控制**: 自动保存状态文件的历史版本  
✅ **自动备份**: 防止状态文件丢失  
✅ **并发锁定**: 防止多人同时修改  
✅ **团队协作**: 多人共享同一状态文件  

---

## 首次使用（初始化）

### 前置条件

1. **安装 Google Cloud SDK**
   ```bash
   # macOS
   brew install --cask google-cloud-sdk
   
   # 或者下载安装：https://cloud.google.com/sdk/docs/install
   ```

2. **认证到 Google Cloud**
   ```bash
   # 登录（会打开浏览器）
   gcloud auth login
   
   # 设置应用默认凭据（Terraform需要）
   gcloud auth application-default login
   ```

3. **验证权限**
   ```bash
   # 检查是否能访问存储桶
   gsutil ls gs://jaskojothep-terraform-state/
   ```

---

## 初始化 Terraform

### 情况1：全新项目（没有本地状态）

```bash
cd terraform/

# 初始化并配置 GCS backend
terraform init

# 输出示例：
# Initializing the backend...
# Successfully configured the backend "gcs"!
```

### 情况2：已有本地状态文件（迁移）

如果你之前使用本地状态（有 `terraform.tfstate` 文件）：

```bash
cd terraform/

# 备份现有状态
cp terraform.tfstate terraform.tfstate.backup

# 重新初始化（会提示是否迁移状态）
terraform init

# 选择 "yes" 迁移状态到 GCS
```

**Terraform 会询问：**
```
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend to the
  newly configured "gcs" backend. No existing state was found in the newly
  configured "gcs" backend. Do you want to copy this state to the new "gcs"
  backend? Enter "yes" to copy and "no" to start with an empty state.

  Enter a value: yes
```

---

## 验证配置

### 检查状态文件位置

```bash
# 查看 Terraform 配置
terraform show

# 检查 GCS 中的状态文件
gsutil ls gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/
```

### 验证状态内容

```bash
# 下载状态文件查看（只读）
gsutil cat gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/default.tfstate | jq '.'
```

---

## 日常使用

配置完成后，Terraform 命令正常使用：

```bash
# 查看计划
terraform plan

# 应用变更
terraform apply

# 查看状态
terraform show

# 销毁资源
terraform destroy
```

**所有操作自动使用 GCS 状态文件，无需额外配置！**

---

## 团队协作

### 多人使用同一状态

团队成员只需：

1. 认证到 Google Cloud（见上文）
2. 克隆项目代码
3. 运行 `terraform init`

**Terraform 自动：**
- 从 GCS 下载最新状态
- 执行操作前自动锁定
- 操作完成后自动上传新状态
- 操作完成后自动解锁

### 状态锁定

当有人正在运行 `terraform apply` 时：

```bash
# 其他人运行时会看到：
Error: Error acquiring the state lock

Error message: lock is already acquired
```

等待锁定释放后重试即可。

---

## 状态文件版本管理

### 查看历史版本

```bash
# 列出所有版本
gsutil ls -a gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/

# 输出示例：
# gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/default.tfstate#1713000000000000
# gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/default.tfstate#1713086400000000
# gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/default.tfstate#1713172800000000
```

### 恢复旧版本（紧急情况）

```bash
# 下载特定版本
gsutil cp gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/default.tfstate#VERSION ./terraform.tfstate

# 覆盖 GCS 中的当前版本
gsutil cp ./terraform.tfstate gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/default.tfstate
```

---

## 故障排查

### 问题1：认证失败

```bash
Error: google: could not find default credentials
```

**解决：**
```bash
gcloud auth application-default login
```

### 问题2：权限不足

```bash
Error: Error loading state: storage.googleapis.com/storage/v1/b/jaskojothep-terraform-state/o/terraform%2Fstate%2Fmaori-story-fill%2Fdefault.tfstate?alt=json: googleapi: Error 403: Forbidden
```

**解决：**
联系管理员添加存储桶权限：
- `Storage Object Admin` 或
- `Storage Object Creator` + `Storage Object Viewer`

### 问题3：状态锁卡住

如果操作被中断（Ctrl+C），锁可能没释放：

```bash
# 强制解锁（⚠️ 确保没有其他人正在操作）
terraform force-unlock LOCK_ID

# LOCK_ID 在错误信息中会显示
```

### 问题4：初始化失败

```bash
Error: Failed to get existing workspaces: querying Cloud Storage failed: Get "https://storage.googleapis.com/storage/v1/b/jaskojothep-terraform-state/o?alt=json&delimiter=%2F&pageToken=&prefix=terraform%2Fstate%2Fmaori-story-fill%2F&projection=full&versions=false": context deadline exceeded
```

**可能原因：**
- 网络问题
- GCP API 未启用

**解决：**
```bash
# 启用 Cloud Storage API
gcloud services enable storage-api.googleapis.com

# 检查网络连接
curl -I https://storage.googleapis.com
```

---

## 最佳实践

### ✅ 推荐做法

1. **每次操作前先 pull 最新代码**
   ```bash
   git pull
   terraform plan  # 自动获取最新状态
   ```

2. **小步提交**
   - 避免一次性大规模变更
   - 每次 apply 前先 plan

3. **使用 Workspace 隔离环境**
   ```bash
   # 开发环境
   terraform workspace new dev
   terraform workspace select dev
   
   # 生产环境
   terraform workspace new prod
   terraform workspace select prod
   ```

### ❌ 避免做法

1. **不要手动编辑 GCS 中的状态文件**
2. **不要在多个位置同时运行 terraform apply**
3. **不要跳过 `terraform plan`**
4. **不要删除 GCS 存储桶中的状态文件**

---

## 状态文件结构

```
gs://jaskojothep-terraform-state/
└── terraform/
    └── state/
        └── maori-story-fill/           # 本项目
            └── default.tfstate         # 默认 workspace 的状态
            └── env:dev/                # dev workspace（如果创建）
                └── default.tfstate
            └── env:prod/               # prod workspace（如果创建）
                └── default.tfstate
```

---

## 安全性

### 状态文件包含敏感信息

Terraform 状态文件包含：
- 资源 ID
- IP 地址
- **可能包含密码、密钥等敏感数据**

**GCS 提供的安全保障：**
- ✅ 传输加密（HTTPS）
- ✅ 静态加密（默认启用）
- ✅ IAM 权限控制
- ✅ 审计日志

### 权限最小化

团队成员权限建议：
- **开发人员**: `Storage Object Viewer` (只读)
- **DevOps**: `Storage Object Admin` (读写)
- **CI/CD**: 使用 Service Account，仅授予必要权限

---

## 与其他项目共享存储桶

同一存储桶可用于多个项目，通过 `prefix` 隔离：

```hcl
# 项目A
backend "gcs" {
  bucket = "jaskojothep-terraform-state"
  prefix = "terraform/state/project-a"
}

# 项目B
backend "gcs" {
  bucket = "jaskojothep-terraform-state"
  prefix = "terraform/state/project-b"
}
```

**本项目使用：**
```hcl
prefix = "terraform/state/maori-story-fill"
```

---

## 参考文档

- [Terraform GCS Backend 官方文档](https://www.terraform.io/language/settings/backends/gcs)
- [Google Cloud Storage 文档](https://cloud.google.com/storage/docs)
- [gsutil 工具文档](https://cloud.google.com/storage/docs/gsutil)

---

## 快速参考

```bash
# 认证
gcloud auth application-default login

# 初始化
terraform init

# 检查状态
gsutil ls gs://jaskojothep-terraform-state/terraform/state/maori-story-fill/

# 日常使用
terraform plan
terraform apply

# 切换环境（可选）
terraform workspace list
terraform workspace select prod
```

---

**下一步：** 运行 `terraform init` 开始使用！
