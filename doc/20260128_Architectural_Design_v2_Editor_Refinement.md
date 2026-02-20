# 架构方案：文本编辑器视觉升级 (v16.0)

## 设计愿景
将简单的“文本框+按钮”弹窗，重塑为符合 **Flow Track** 整体极客美学的“模块化卡片（Raised Component）”。通过模拟光影层级，使编辑器具有空间感，并统一交互动效。

---

## 核心变更方案

### 1. 输入框 Card 化 (Visual Elevation)
- **模拟主界面 HeaderCard 视觉**：不再使用扁平化边框，转而使用 `border-top` 高亮与 `border-bottom` 阴影的组合。
- **立体阴影支持**：在代码层面为 `QPlainTextEdit` 容器添加 `QGraphicsDropShadowEffect`，实现平滑的外部阴影。
- **内边距优化**：调整文本内容的内边距 $(padding)$，确保文字在精致的卡片感中呼吸感十足。

### 2. 按钮组件重塑 (Action Button Repurposing)
- **风格复刻**：
    - **保存 (Save)**：完全复用主界面 `ActionButton[type="start"]` 的 Aurora Green 渐变与 3D 凸起效果。
    - **取消 (Cancel)**：完全复用主界面 `ActionButton:disabled` 或低饱和灰度风格，改造成具有 Raised 感的辅助按钮。
- **交互逻辑**：引入 `:pressed` 伪类响应，实现按下时的“物理下沉”位移感 $(margin-top: 2px)$。

### 3. 全局样式解耦 (Refactoring)
- **QSS 迁移**：将原来硬编码在 `notes_editor.py` 内部的 `setStyleSheet` 抽离，改由弹窗自身的 `setObjectName` 关联，由全局 `theme.qss` 统一调度。

---

## 详细修改计划

### 1. [MODIFY] [notes_editor.py](file:///e:/workspace_antigravity/flow_track/ui/components/notes_editor.py)
- 给 `self.editor` 外层嵌套一个 `QFrame` 作为主体卡片容纳器。
- 为该容器应用 `QGraphicsDropShadowEffect`。
- 将按钮的 `styleSheet` 彻底移除，改为 `self.btn_save.setObjectName("ActionButton")` 并设置 `type="start"`。

### 2. [MODIFY] [theme.qss](file:///e:/workspace_antigravity/flow_track/ui/styles/theme.qss)
- 新增 `#NotesEditorCard` 的特定样式，模仿 `#HeaderCard`。
- 增加对弹窗内按钮的精细微调，确保由于弹窗背景与主界面色差导致的视觉偏差得以修正。

---

## 风险评估
- **层级穿透 (Focus Ripple)**：`QPlainTextEdit` 在获得焦点时的 Border 动画可能会切碎外层阴影效果。*对策：在 QSS 中明确焦点状态的边框优先级。*
- **分辨率适配**：添加阴影后，500x350 的固定尺寸可能会因为边距溢出而出现切边。*对策：适当增加 Margins，并将 FixedSize 调整为动态适应或预留阴影冗余。*

---

## 验证计划
1. **视觉一致性**：确认弹窗开启后，保存按钮的颜色、阴影、圆角与主界面“开始”按钮 10px 颗粒度一致。
2. **逻辑验证**：确认换行符依然能够跨组件正确传递，且按 Tab 键能顺畅在“输入框 -> 保存 -> 取消”之间切换。

> [!IMPORTANT]
> **本方案目前仅为逻辑草案。在您输入“执行”之前，我不会修改任何项目代码。**
