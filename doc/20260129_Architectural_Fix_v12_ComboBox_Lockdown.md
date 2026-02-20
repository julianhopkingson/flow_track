# 架构设计方案：QComboBox 运行态交互锁定 (v1.0)

## 1. 问题背景
在应用程序进入“运行”状态后，UI 大部分组件（如开始按钮、定时器卡片编辑区）已成功禁用。然而，用户发现顶部标题栏的 **“语言选择”** 和 **“复制次数”** 两个下拉框在变灰后依然可以点击并弹出列表，这允许用户在程序运行时修改核心配置，可能导致逻辑冲突或不一致。

## 2. 根本原因分析
经过代码审计（[main_window.py](file:///e:/workspace_antigravity/flow_track/ui/main_window.py)），确定了两个核心问题点：

### 2.1 事件过滤器逻辑缺陷
为了实现下拉框文字居中，系统将 `QComboBox` 设置为 `setEditable(True)` 并通过 `LineEditClickFilter` 拦截了内部 `lineEdit` 的点击事件。
但在 `LineEditClickFilter.eventFilter` 实现中，**未对 `combo.isEnabled()` 进行判断**。
```python
# 缺陷代码片段
def eventFilter(self, obj, event):
    if event.type() == QEvent.MouseButtonRelease:
        if self.combo.view().isVisible():
            self.combo.hidePopup()
        else:
            self.combo.showPopup() # 无论是否被禁用，强制显示弹窗
        return True
```

### 2.2 视觉反馈一致性
虽然 `set_ui_locked` 调用了 `setEnabled(False)`，但由于自定义 QSS 样式可能未完全覆盖禁用态的所有子部件（如 `::drop-down` 和内部 `lineEdit`），导致禁用态的视觉对比度不够强烈，诱使客户尝试点击。

---

## 3. 设计解决方案

### 3.1 核心修复：事件过滤器状态感知
修改 `LineEditClickFilter` 类，在拦截事件时必须检查父级容器的可用状态。

**设计目标**：
- 当 `self.combo` 处于禁用状态时，事件过滤器应直接透传事件或不做任何弹窗操作。

### 3.2 逻辑增强：显式锁定内部部件
在 `MainWindow.set_ui_locked` 方法中，不仅对 `QComboBox` 容器进行常规 `setEnabled` 操作，同时确保内部 `lineEdit` 的 `readOnly` 状态保持同步。

### 3.3 样式优化（UI/UX 增强）
更新 `theme_template.qss`，强化 `QComboBox:disabled` 及其子部件（`::drop-down`, `lineEdit`）的样式表现：
- **背景色**：更深的灰色。
- **文字颜色**：低对比度灰色。

---

## 4. 详细实施步骤

### 第一阶段：逻辑修复
1. 修改 `ui/main_window.py` 中的 `LineEditClickFilter.eventFilter`：
   - 添加 `if not self.combo.isEnabled(): return False`。

### 第二阶段：样式加固
1. 修改 `ui/styles/theme_template.qss`：
   - 为 `QComboBox:disabled` 添加背景颜色映射 `@CONTAINER_BG_ALT`。

---

## 5. 风险评估与规避建议

| 风险点 | 严重程度 | 规避措施 |
| :--- | :--- | :--- |
| **事件链断裂** | 中 | 确保 `eventFilter` 在返回 `False` 时调用 `super().eventFilter`。 |
| **样式覆盖失效** | 低 | 检查 QSS 选择器优先级，确保 `:disabled` 伪类正确定义。 |
| **异步状态同步** | 低 | 确保 `stop_timers` 能够正确恢复 UI 状态。 |

---
> [!IMPORTANT]
> **结论**：通过在该过滤器中引入“状态感知”机制，即可在不影响组件居中对齐功能的前提下，实现完美的运行时锁定。
