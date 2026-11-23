# 变更日志 - 2026年4月30日

## 概述
更新主菜单Logo为单行版本，优化页面布局，清理冗余资源文件。

---

## 主要变更

### 1. Logo更新

**背景**：
- 原Logo显示"STORY"和"FILLER"分两行堆叠
- 用户希望改为单行显示，使Logo更宽、更大

**实现**：
- 使用新的单行木板Logo设计（`story-filler-logo-single-line.png`）
- 尺寸：840×158px（宽度保持840px，高度从467px降至158px）
- 透明背景处理：去除白色背景，保留木板纹理和藤蔓装饰
- 文件大小：248KB

**技术细节**：
- 使用PIL/Pillow处理图像透明度
- 算法：识别高亮度（>240）且低色彩方差（<15）的像素设为透明
- 保留木板内部所有细节，仅处理边缘背景

### 2. 布局调整

**Menu页面间距优化**：
```javascript
// frontend/src/pages/Menu.jsx
const titleContainerStyles = {
  marginBottom: '0.5rem',  // 从 2rem 减小到 0.5rem
  // ... 其他属性
};
```

**Logo尺寸调整**：
```javascript
<img
  src={logoImage}
  alt="Story Filler"
  style={{
    width: '700px',  // 从 500px 增加到 700px
    height: 'auto',
  }}
/>
```

**效果**：
- Logo与故事列表按钮距离从约32px减少至约8px
- Logo显示尺寸增加40%
- 页面视觉重心更集中

### 3. 资源清理

**删除的冗余文件**（共约7.5MB）：
- `title-logo.png` (5.3MB) - 最早的logo文件
- `story-filler-logo.png` (266KB) - 初始两行版本
- `story-filler-logo-final.png` (266KB) - 处理后的两行版本
- `story-filler-logo-large.png` (287KB) - 放大的两行版本
- `story-filler-logo-wide.png` (196KB) - 拉伸测试版本
- `story-filler-logo-optimized.png` (418KB) - 优化尝试版本
- `logo-clean.png` (266KB) - 清理背景版本
- `newlogo-tmp.jpeg` (71KB) - 临时上传文件
- `final-wood-tmp.png` (305KB) - 临时上传文件

**删除的临时文件**：
- `VERIFICATION_CHECKLIST.md` (5.1KB) - 部署验证清单
- `backend/core/test_gcs.py` - GCS测试脚本

**保留的必要文件**：
- `story-filler-logo-single-line.png` (248KB) - 当前使用的Logo
- `cloud.png`, `mountain.png`, `grass.png`, `flower.png` - 背景动画资源
- `question_mark.png` (842KB) - UI提示图标

### 4. 配置更新

**`.gitignore` 新增规则**：
```gitignore
# Environments
.env.production

# Temporary/test files
*_tmp.*
*-tmp.*
test_*.py
VERIFICATION_CHECKLIST.md

# Backup directories
volume-backup-*/
```

**用途**：
- 忽略GitHub Actions生成的生产环境配置
- 自动忽略临时文件和测试文件
- 排除数据库备份目录

---

## 提交记录

```
76e7bd1 - Update logo and clean up assets
d960da2 - Replace logo with single-line version
91cb9d5 - Increase logo size and reduce spacing
```

---

## 技术实现细节

### 图像处理流程

1. **加载原始图像**：
   ```python
   img = Image.open('final-wood-tmp.png').convert('RGBA')
   data = np.array(img)
   ```

2. **背景检测算法**：
   ```python
   brightness = (r + g + b) / 3
   color_variance = np.std([r, g, b], axis=0)
   is_white = (brightness > 240) & (color_variance < 15)
   ```

3. **应用透明度**：
   ```python
   data[:,:,3] = np.where(is_white, 0, data[:,:,3])
   ```

4. **调整尺寸**：
   ```python
   target_width = 840
   target_height = int(target_width * img.height / img.width)
   result = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
   ```

### 迭代过程

**问题1**：透明度过度处理
- **现象**：木板内部出现透明空洞
- **原因**：阈值过于宽松（brightness > 180）
- **解决**：提高阈值到240，只处理纯白背景

**问题2**：边缘残留
- **现象**：Logo周围有白色或黑色碎片
- **原因**：JPEG压缩伪影和颜色渐变
- **解决**：结合亮度和色彩方差双重条件过滤

**问题3**：毛边和横线
- **现象**：Logo边缘不平滑，顶部有横线
- **原因**：原始图像包含这些瑕疵
- **解决**：使用更干净的源图像（final-wood-tmp.png）

---

## 工作流程改进

### 新的部署流程

**建立的规范**：
1. 代码修改后先在本地测试（`npm run dev`）
2. 用户确认效果满意
3. 提交代码并推送到生产环境

**记录位置**：
- 已保存到项目记忆：`memory/feedback_deployment_workflow.md`
- 类型：feedback
- 应用场景：所有未来的前端修改

---

## 影响评估

### 性能影响
- **减少**：约7.5MB冗余资源文件
- **构建时间**：无明显变化
- **页面加载**：Logo文件从287KB降至248KB（减少13.6%）

### 视觉影响
- **Logo可见性**：显著提升（尺寸增加40%）
- **页面布局**：更紧凑，视觉焦点更集中
- **用户体验**：Logo与内容关联更明显

### 维护影响
- **代码清晰度**：提升（删除未使用的导入和文件）
- **Git历史**：减少仓库大小
- **未来修改**：更容易定位当前使用的资源

---

## 部署信息

- **部署时间**：2026年4月30日
- **部署方式**：GitHub Actions自动部署
- **生产URL**：https://jothep.github.io/maori-story-fill/
- **部署状态**：✅ 成功

---

## 验证清单

- [x] Logo在生产环境正确显示
- [x] 透明背景正常工作（无白色边框）
- [x] Logo与故事按钮间距符合预期
- [x] 背景动画（云、山、草、花）正常运行
- [x] BGM功能正常
- [x] 移动端响应式布局正常
- [x] 旧Logo文件已从仓库删除
- [x] .gitignore规则生效

---

## 相关文件

### 修改的文件
- `frontend/src/pages/Menu.jsx` - Logo导入和样式
- `frontend/src/assets/story-filler-logo-single-line.png` - 新Logo
- `.gitignore` - 忽略规则

### 删除的文件
- 9个旧Logo文件
- 2个临时文件

### 配置文件
- `memory/feedback_deployment_workflow.md` - 工作流程记忆

---

## 后续建议

1. **监控**：关注生产环境Logo加载性能
2. **备份**：保留最终Logo源文件（PSD/AI格式）以便未来修改
3. **文档**：如需修改Logo，参考本文档的图像处理流程
4. **优化**：考虑使用WebP格式进一步减小文件大小（可选）

---

## 联系信息

- **执行者**：Claude Code
- **审核者**：Xiang
- **项目**：Maori Story Filler
- **仓库**：https://github.com/jothep/maori-story-fill
