# Cloud Run URL 稳定性说明

## 两种 URL 格式

Cloud Run 为每个服务提供两种 URL：

### 格式 1：基于项目 ID ⭐ **推荐使用**

```
https://[SERVICE_NAME]-[PROJECT_NUMBER].[REGION].run.app
```

**示例**：
```
https://maori-story-backend-454222894238.us-central1.run.app
```

**组成部分**：
- `maori-story-backend` - 服务名
- `454222894238` - 项目编号（Project Number）
- `us-central1` - 区域

**稳定性**：✅ **非常稳定**
- ✅ 项目编号永不改变
- ✅ 服务名不变，URL 就不变
- ✅ 重新部署不影响
- ✅ 更新镜像不影响
- ✅ 修改环境变量不影响
- ⚠️ **只有删除服务后重新创建同名服务才会保持不变**
- ❌ 修改服务名会改变 URL
- ❌ 迁移到不同区域会改变 URL

### 格式 2：内部标识符

```
https://[SERVICE_NAME]-[HASH]-[REGION_CODE].a.run.app
```

**示例**：
```
https://maori-story-backend-tc2dttesfa-uc.a.run.app
```

**组成部分**：
- `maori-story-backend` - 服务名
- `tc2dttesfa` - Cloud Run 内部生成的唯一标识符
- `uc` - 区域代码简写（us-central）
- `.a.run.app` - 内部域名

**稳定性**：⚠️ **相对稳定**
- ✅ 在服务生命周期内固定
- ✅ 重新部署不影响
- ✅ 更新镜像不影响
- ✅ 修改环境变量不影响
- ❌ **删除服务后重新创建会生成新的 hash**
- ❌ 修改服务名会改变 URL
- ❌ 迁移到不同区域会改变 URL

## 查看当前使用的 URL

### 方法 1：GCP Console（显示格式 1）
1. 访问：https://console.cloud.google.com/run?project=jaskojothep
2. 点击 `maori-story-backend` 服务
3. 查看 URL 字段

### 方法 2：gcloud 命令（显示格式 2）
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="value(status.url)"
```

### 方法 3：同时查看两个 URL
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="value(status.url,status.address.url)"
```

## 当前配置

### 前端配置（GitHub Secret）
**位置**：GitHub Settings → Secrets → Actions → `CLOUD_RUN_URL`

**当前值**（推荐）：
```
https://maori-story-backend-454222894238.us-central1.run.app
```

### 后端 CORS 配置
**位置**：`env-vars.yaml` → `CORS_ALLOWED_ORIGINS`

**当前值**：
```yaml
CORS_ALLOWED_ORIGINS: "http://localhost:5173,http://localhost:8080,https://jothep.github.io"
```

## 如何获取项目编号（Project Number）

如果将来需要重新构建 URL：

### 方法 1：gcloud 命令
```bash
gcloud projects describe jaskojothep --format="value(projectNumber)"
```

### 方法 2：GCP Console
1. 访问：https://console.cloud.google.com/home/dashboard?project=jaskojothep
2. 查看左上角项目信息
3. 项目编号显示在项目名称下方

### 方法 3：通过 Cloud Run 服务
```bash
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="value(metadata.labels)"
```

## URL 会改变的情况

### 格式 1 会改变的情况
1. ❌ 修改服务名（如 `maori-story-backend` → `maori-backend`）
2. ❌ 迁移到不同区域（如 `us-central1` → `us-east1`）
3. ❌ 迁移到不同项目

### 格式 2 会改变的情况
1. ❌ 修改服务名
2. ❌ 迁移到不同区域
3. ❌ **删除服务后重新创建**（即使服务名相同）
4. ❌ 迁移到不同项目

## 最佳实践

### ✅ 推荐做法
1. **使用格式 1（基于项目 ID）** - 最稳定
2. **在所有配置中使用同一个 URL**：
   - GitHub Secret `CLOUD_RUN_URL`
   - 文档中的示例
   - 环境变量文件
3. **不要在代码中硬编码 URL** - 使用环境变量
4. **定期备份配置** - 记录在文档中

### ⚠️ 注意事项
1. **永远不要删除 Cloud Run 服务**，除非必要
   - 删除会改变格式 2 的 URL
   - 格式 1 的 URL 在重新创建同名服务后仍然有效
2. **服务名是 URL 的一部分**
   - 修改服务名 = 改变 URL
   - 重命名服务实际上是删除旧服务、创建新服务
3. **区域选择很重要**
   - 迁移区域 = 改变 URL
   - 建议一开始就选对区域

## 验证 URL 稳定性

你可以运行这个命令来确认服务信息：

```bash
# 显示服务详细信息
gcloud run services describe maori-story-backend \
  --region=us-central1 \
  --format="yaml(metadata.name,metadata.creationTimestamp,status.url)"
```

**预期输出**：
```yaml
metadata:
  creationTimestamp: '2026-04-25T01:14:23.944299Z'
  name: maori-story-backend
status:
  url: https://maori-story-backend-tc2dttesfa-uc.a.run.app
```

创建时间戳（`creationTimestamp`）不变，说明服务从未被删除重建。

## 如果 URL 意外改变

### 诊断步骤
1. 检查服务是否被删除重建：
   ```bash
   gcloud run services describe maori-story-backend \
     --region=us-central1 \
     --format="value(metadata.creationTimestamp)"
   ```

2. 检查服务名是否改变：
   ```bash
   gcloud run services list --region=us-central1
   ```

3. 检查区域是否正确：
   ```bash
   gcloud run services list --filter="name:maori-story-backend"
   ```

### 修复步骤
1. 更新 GitHub Secret `CLOUD_RUN_URL`
2. 触发前端重新部署（推送代码到 `main` 分支）
3. 更新文档中的 URL
4. 更新后端 `CORS_ALLOWED_ORIGINS`（如果需要）

## 总结

| URL 格式 | 稳定性 | 使用建议 | 当前配置 |
|---------|--------|---------|---------|
| 格式 1（项目 ID） | ⭐⭐⭐⭐⭐ | **强烈推荐** | ✅ 前端使用 |
| 格式 2（内部 hash） | ⭐⭐⭐ | 可用但不推荐 | ❌ 不使用 |

**当前项目使用的是最稳定的格式 1** ✅

---

**最后更新**: 2026-04-29  
**当前服务创建时间**: 2026-04-25  
**项目 ID**: jaskojothep  
**项目编号**: 454222894238  
**服务名**: maori-story-backend  
**区域**: us-central1
