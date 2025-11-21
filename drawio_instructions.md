# Draw.io 绘制指南

## 方法 1: 使用 Mermaid 代码（推荐）

### 在线预览 Mermaid 图表
1. 访问 https://mermaid.live/
2. 复制 `sacs_main_flowchart.mmd` 文件中的代码（去掉 ```mermaid 和 ```）
3. 粘贴到编辑器中
4. 可以导出为 PNG/SVG，然后导入到 Draw.io

### 或者使用 GitHub
1. 在 GitHub 仓库中创建 `.md` 文件
2. 粘贴 Mermaid 代码
3. GitHub 会自动渲染
4. 截图或导出

---

## 方法 2: 在 Draw.io 中手动绘制

### 步骤 1: 创建基本框架

#### 1.1 添加开始节点
- **形状**: 圆角矩形（Rounded Rectangle）
- **位置**: 顶部居中
- **文本**: "Start"
- **样式**:
  - 填充: #90EE90 (浅绿色)
  - 描边: #52C41A (绿色), 3px
  - 文字: 深绿色, 加粗, 14pt

#### 1.2 添加流程框（按顺序）
1. **Load Configuration**
   - 文本: "Load Configuration\nConfig YAML"
   - 填充: #E6F3FF (浅蓝色)
   - 描边: #4A90E2 (蓝色), 2px

2. **Generate Initial Population**
   - 文本: "Generate Initial Population\nFrom SACS file or seeds"
   - 填充: #E6F3FF
   - 描边: #4A90E2, 2px

3. **Evaluate Initial Population**
   - 文本: "Evaluate Initial Population"
   - 填充: #FFF4E6 (浅橙色)
   - 描边: #FF8C42 (橙色), 2px

#### 1.3 添加决策框
- **形状**: 菱形（Diamond）
- **文本**: "Budget > 0?"
- **填充**: #FFD700 (金色)
- **描边**: #E67E22 (深橙色), 3px

#### 1.4 添加循环体（三个并行框）
1. **Select Parents**
   - 文本: "Select Parents\nNSGA-II Selection"
   - 填充: #E6F3FF
   - 描边: #4A90E2, 2px
   - 位置: 左侧

2. **LLM Generate**
   - 文本: "LLM Generate\nMutation/Crossover\nGemini-2.5-Flash"
   - 填充: #E6F3FF
   - 描边: #4A90E2, 2px
   - 位置: 中间

3. **Parse Candidate**
   - 文本: "Parse Candidate\nExtract code blocks"
   - 填充: #E6F3FF
   - 描边: #4A90E2, 2px
   - 位置: 右侧

#### 1.5 添加评估步骤（汇聚）
1. **Modify SACS File**
   - 文本: "Modify SACS File\nReplace GRUP/PGRUP or JOINT"
   - 填充: #FFF4E6
   - 描边: #FF8C42, 2px

2. **Run SACS Analysis**
   - 文本: "Run SACS Analysis\nWSL Environment"
   - 填充: #FFF4E6
   - 描边: #FF8C42, 2px

3. **Extract Results**
   - 文本: "Extract Results\nWeight, UC values"
   - 填充: #FFF4E6
   - 描边: #FF8C42, 2px

4. **Calculate Objectives**
   - 文本: "Calculate Objectives\nWeight, Axial_UC_max, Bending_UC_max"
   - 填充: #FFF4E6
   - 描边: #FF8C42, 2px

5. **Update Population**
   - 文本: "Update Population\nNSGA-II"
   - 填充: #E6F3FF
   - 描边: #4A90E2, 2px

#### 1.6 添加输出和结束
1. **Save Results**
   - 文本: "Save Results\nPKL, JSON, Model Files"
   - 填充: #E6F9E6 (浅绿色)
   - 描边: #52C41A (绿色), 2px

2. **End**
   - 形状: 圆角矩形
   - 文本: "End"
   - 填充: #FFE6E6 (浅红色)
   - 描边: #FF4D4F (红色), 3px

### 步骤 2: 添加连接线

#### 2.1 主流程连接（从上到下）
- Start → Load Configuration
- Load Configuration → Generate Initial Population
- Generate Initial Population → Evaluate Initial Population
- Evaluate Initial Population → Budget > 0?

#### 2.2 循环分支连接
- Budget > 0? (Yes) → Select Parents
- Select Parents → LLM Generate
- LLM Generate → Parse Candidate
- Parse Candidate → Modify SACS File

#### 2.3 评估流程连接
- Modify SACS File → Run SACS Analysis
- Run SACS Analysis → Extract Results
- Extract Results → Calculate Objectives
- Calculate Objectives → Update Population
- Update Population → Budget > 0? (循环返回)

#### 2.4 结束连接
- Budget > 0? (No) → Save Results
- Save Results → End

#### 2.5 循环返回箭头
- 从 "Update Population" 左侧添加一个返回箭头到 "Budget > 0?"
- 样式: 虚线, 红色, 2px
- 标签: "Continue"

### 步骤 3: 添加图标（可选）

Draw.io 支持添加图标：
1. 点击形状
2. 选择 "Edit" → "Insert" → "Image"
3. 或者使用 Draw.io 的图标库：
   - 点击左侧 "More Shapes"
   - 搜索 "AWS", "Azure", "GCP" 等图标库
   - 或者使用 "General" → "Icons"

#### 推荐的图标映射
- **LLM/模型**: 机器人图标 (robot, bot)
- **SACS分析**: 齿轮图标 (gear, settings)
- **数据库**: 数据库图标 (database)
- **图表**: 图表图标 (chart, graph)
- **文件**: 文档图标 (document, file)
- **优化**: 大脑图标 (brain) 或齿轮图标

### 步骤 4: 美化

#### 4.1 添加阴影（可选）
1. 选择形状
2. 右侧面板 → "Effects" → "Shadow"
3. 设置: 偏移 2-3px, 模糊 3-5px, 透明度 10-20%

#### 4.2 调整字体
- 标题: 14-16pt, 加粗
- 描述: 12pt, 常规
- 颜色: 深灰色 (#333333)

#### 4.3 统一间距
- 水平间距: 30-40px
- 垂直间距: 40-50px
- 使用 "Arrange" → "Distribute" 自动对齐

### 步骤 5: 导出

1. **File** → **Export as** → **PNG**
   - 分辨率: 300 DPI (用于论文)
   - 背景: 透明或白色

2. **File** → **Export as** → **PDF**
   - 矢量格式，适合论文

3. **File** → **Export as** → **SVG**
   - 矢量格式，可编辑

---

## 快速参考：颜色代码

| 用途 | 填充色 | 描边色 | 描边宽度 |
|------|--------|--------|----------|
| 开始 | #90EE90 | #52C41A | 3px |
| 结束 | #FFE6E6 | #FF4D4F | 3px |
| 处理步骤 | #E6F3FF | #4A90E2 | 2px |
| 评估步骤 | #FFF4E6 | #FF8C42 | 2px |
| 决策点 | #FFD700 | #E67E22 | 3px |
| 输出 | #E6F9E6 | #52C41A | 2px |

---

## Draw.io 快捷键

- **Ctrl+D**: 复制并粘贴
- **Ctrl+Shift+D**: 克隆
- **Ctrl+G**: 组合
- **Ctrl+Shift+G**: 取消组合
- **Ctrl+L**: 锁定/解锁
- **Ctrl+Shift+Arrow**: 对齐
- **Space**: 平移画布
- **Ctrl+Mouse Wheel**: 缩放

---

## 提示

1. **使用图层**: 将不同模块放在不同图层，便于管理
2. **使用样式**: 创建样式模板，统一应用
3. **使用网格**: 启用网格对齐，保持整洁
4. **保存模板**: 保存为模板，方便后续使用

























