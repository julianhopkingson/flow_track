# [设计方案] SpinBox 箭头交互行为优化 (Hover 并显示)

## 1. 问题的本质分析 (First Principles)
当前 UI 中，时间输入框 (SpinBox) 的上下调节箭头始终显示，导致界面视觉元素过多（视觉噪点）。
**核心目标：**
- **极简主义交互**：仅在用户有交互意图（鼠标悬浮）时展示辅助控件（箭头）。
- **状态感知**：禁用状态下即使悬浮也不应显示箭头，避免产生可交互的错觉。
- **视觉稳定性**：交互过程中输入框的外边框必须保持恒定，避免界面跳动。

## 2. 多方案对比 (Trade-offs)

| 方案 | 技术路径 | 优点 | 缺点 |
| :--- | :--- | :--- | :--- |
| **方案 A (QSS 伪类控制)** | 通过 `QSpinBox:hover::up-button` 控制宽度与边框 | **原生支持**，性能最高，完全符合样式驱动理念。 | 若处理不当，宽度变化可能导致内部文字产生微调位移。 |
| **方案 B (QSS 透明度/颜色)** | 默认将按钮/箭头设为透明，hover 时恢复 | 切换平滑，无布局抖动风险。 | 按钮位点依然存在，垂直分割线处理较复杂。 |
| **方案 C (Python 事件过滤)** | 在 `enterEvent` 中动态设置 `buttonSymbols` | 逻辑最清晰，直接调用 Qt 内置行为。 | 涉及 Python 逻辑改动，相对于样式修改较重，且可能被现有 QSS 覆盖。 |

**结论：** 选用 **方案 B**。由于方案 A（宽度切换）可能引起布局抖动或渲染问题，方案 B 通过颜色和透明度控制视觉显隐，不仅能确保布局绝对稳定（按钮一直占位但看不见），还能更平滑地过渡。

---

## 3. 方案 B：详细技术实现路径 (Implementation Plan)

### 3.1 核心 QSS 策略
按钮区域和箭头始终保持占位（18px 宽度），但通过将边框、背景及箭头镜像设为“透明”来实现隐藏。

```css
/* 1. 默认状态：按钮几乎看不见 (配色与背景一致) */
QSpinBox::up-button, QSpinBox::down-button {
    width: 18px; 
    border-left: 1px solid transparent; /* 保持占位但不显示线 */
    background: transparent;
}

QSpinBox::up-arrow, QSpinBox::down-arrow {
    image: none; /* 或者使用透明色占位 */
}

/* 2. 悬浮状态：显示边框和箭头 */
QSpinBox:hover:!disabled::up-button, QSpinBox:hover:!disabled::down-button {
    border-left: 1px solid [[INPUT_BORDER]];
}

QSpinBox:hover:!disabled::up-arrow {
    image: url("[[ASSETS_PATH]]/spin_up.svg");
}

QSpinBox:hover:!disabled::down-arrow {
    image: url("[[ASSETS_PATH]]/spin_down.svg");
}

/* 3. 按钮内 hover：绿色高亮 */
QSpinBox::up-button:hover:!disabled { 
    background-color: [[BG_HOVER]];
    image: url("[[ASSETS_PATH]]/spin_up_green.svg");
}
```

### 3.2 保持外框可见
确保 `QSpinBox` 的基础样式中 `border` 始终存在：
```css
/* 已经存在的样式，需保持 */
QLineEdit, QSpinBox, QComboBox {
    border: 1px solid [[INPUT_BORDER]];
    border-radius: 8px;
}
```

---

## 4. 潜在风险评估 (Risk Assessment)

### 4.1 布局抖动 (Layout Jitter)
- **风险描述**：当 `up-button` 宽度从 `0px` 变更为 `18px` 时，若 SpinBox 宽度为 `auto`，会导致整个控件宽度变大。
- **应对策略**：目前 `timer_card.py` 中已为 SpinBox 设置了 `setFixedWidth(64)`（对应代码 135 行），这确保了父容器空间是固定的，箭头的出现仅会挤压内部 LineEdit 的显示区域，而不会改变控件总宽度。

### 4.2 禁用状态覆盖 (Disabled State Override)
- **风险描述**：Qt 的 QSS 优先级有时会产生难以预料的结果，特别是在多重伪类（`:hover:disabled`）组合时。
- **应对策略**：显式使用 `:!disabled` 排除方案。同时在全局禁用规则中强化 `border` 的表现。

### 4.3 渲染残留
- **风险描述**：某些机器上的渲染引擎可能在按钮快速切换时留下视觉残影。
- **应对策略**：建议在 `TimerCard` 的 `enterEvent`/`leaveEvent` 中调用 `self.update()` 强制重绘（如果发现 QSS 处理不彻底）。

---

## 5. 验证计划 (Verification Plan)

### 5.1 自动化验证
- 检查 `theme_template.qss` 语法正确性。

### 5.2 手动验证流程
1. **常规状态**：观察时间输入框，确认只有外边框和数字，无上下箭头。
2. **悬浮状态**：将鼠标移入 `HH`、`MM` 或 `SS` 的任意一个输入框内，确认右侧立即出现箭头及垂直分割线。
3. **按钮悬浮**：鼠标移入箭头按钮上方，确认箭头颜色变为绿色。
4. **禁用状态**：
   - 勾选“显示桌面”，此时时间输入框应变灰。
   - 鼠标再次移入时间输入框，确认**不显示**箭头。
5. **外框检查**：无论是否 hover，无论是否 disabled，输入框的圆角矩形边框始终清晰可见。

```markdown
📌 [SpinBox 交互优化] 设计方案总结
├── 🎯 核心需求 (Core Goal)
│   ├── 👁️ 仅在 Hover 时显示箭头
│   ├── 🚫 Disabled 状态下隐藏
│   └── 🖼️ 保持外框始终可见
├── 🏗️ 技术方案 (Technical Approach)
│   ├── 🎨 QSS 子控件动态宽度 (Width: 0 -> 18px)
│   ├── 🛡️ 利用 :!disabled 伪类过滤
│   └── 📍 固定控件宽度 (64px) 防止抖动
└── ⚠️ 风险防控 (Risk Mitigation)
    ├── 📏 布局稳定性校验
    └── 优先级覆盖验证
```
