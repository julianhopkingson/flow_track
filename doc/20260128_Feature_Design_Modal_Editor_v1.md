# 模态备注编辑器方案设计 (Feature Design: Modal Note Editor)

**版本**: v1.0  
**日期**: 2026-01-28  
**作者**: Lead Architect (Antigravity)  
**状态**: [待审核]

---

## 1. 需求概述 (Overview)

当前用户在 `TimerCard` 组件编辑备注（Notes）时，只能通过主界面有限宽度的单行输入框（`QLineEdit`）进行操作。这在处理长文本备注时体验不佳。

**核心需求**：
1.  **双重输入模式**：保留主界面直接输入能力，新增点击图标弹出模态窗口编辑的能力。
2.  **输入体验优化**：弹窗中使用多行文本框 (`QTextEdit/QPlainTextEdit`) 提供更大的编辑视野。
3.  **一致性体验**：弹窗需包含“取消/保存”按钮，支持包括中文在内的多语言，且 UI 风格遵循现有的绿色品牌调性。

---

## 2. 架构设计 (Architecture Design)

### 2.1 新增组件：`NotesEditorDialog`

我们将创建一个独立的 `QDialog` 子类，专门处理文本编辑交互。

*   **位置**: `ui/components/notes_editor.py` (新增文件)
*   **职责**:
    *   接收初始文本。
    *   提供多行编辑区域。
    *   返回编辑后的最终文本。
    *   处理多语言标签 (`Save`, `Cancel`, `Edit Note`)。

### 2.2 现有组件变更：`TimerCard` (`ui/components/timer_card.py`)

*   **交互升级**:
    *   将原本仅用于显示的 `lbl_notes_icon` (QLabel) 升级为交互触发器。
    *   这可以通过两种方式实现：
        1.  **方案 A (保守)**: 为 QLabel 安装 `EventFilter` 或重写 `mousePressEvent`。
        2.  **方案 B (推荐)**: 将 QLabel 替换为 `QPushButton` (Flat Style)，这样天然支持 Click 信号和 Hover 态，且与之前的代码重构兼容性好。
    *   *决策*: 采用 **方案 B**，将 `lbl_notes_icon` 重构为 `btn_notes_edit` (QPushButton)，这样与右侧的 "Copy" 按钮逻辑更加一致。

### 2.3 多语言扩展 (`assets/language.ini`)

需要新增以下键值对以支持弹窗界面：

```ini
[EN]
...
title_edit_note=Edit Note
btn_save=Save
btn_cancel=Cancel

[CN]
...
title_edit_note=编辑备注
btn_save=保存
btn_cancel=取消
```

---

## 3. 详细设计 (Detailed Design)

### 3.1 UI 布局图示

```text
+--------------------------------------------------+
|  编辑备注 (Edit Note)                        [X] |  <- Window Title
+--------------------------------------------------+
|                                                  |
|  [                                            ]  |
|  [        QPlainTextEdit (多行输入区域)         ]  |
|  [        自动换行，支持长文本                  ]  |
|  [                                            ]  |
|                                                  |
+--------------------------------------------------+
|         [ Cancel/取消 ]    [ Save/保存 ]         |  <- Button Box
+--------------------------------------------------+
```

### 3.2 交互逻辑流程

1.  **触发**：
    *   用户只有在 **"非显示桌面"** 模式下（即处于编辑态），点击右侧的“编辑图标”按钮。
    *   若处于“显示桌面”模式，按钮应被禁用或点击无响应（与现有逻辑一致）。

2.  **数据传输** (In):
    *   获取主界面 `edit_notes` 当前的内容。
    *   实例化 Dialog，传入内容。

3.  **编辑**：
    *   用户在弹窗中修改文本。
    *   支持回车换行（但在保存时需处理，详见风险部分）。

4.  **保存** (Out):
    *   用户点击 "Save"。
    *   Dialog 关闭并返回 `Accepted`。
    *   `TimerCard` 获取 Dialog 的文本。
    *   **关键处理**：由于主界面 `edit_notes` 是单行 `QLineEdit`，我们需要决定如何处理换行符。
        *   *策略*: 将所有换行符 `\n` 替换为 `空格`。这样保证主界面显示整洁，同时逻辑上 Flow Track 的单步备注通常不包含复杂段落。

---

## 4. 风险评估与对策 (Risks & Mitigations)

| 风险点 | 描述 | 解决方案/对策 |
| :--- | :--- | :--- |
| **R1: 换行符丢失** | 用户在弹窗精心分段的文本，保存回主界面变成一行，再次打开弹窗也没了格式。 | **接受现状**。Flow Track 的定位是轻量级自动化，`task.md` 或自动化脚本通常不支持单元格内的多行文本。我们将明确视备注为“单行长文本”。弹窗仅用于方便阅读和编辑一长串文字。 |
| **R2: 样式不一致** | 新弹窗使用系统原生边框，显得格格不入。 | 在 `NotesEditorDialog` 初始化时，显式加载 `theme.qss`，并确保 Save/Cancel 按钮使用了项目中统一的 `QPushButton` 样式类（如绿色主按钮）。 |
| **R3: 图标替换副作用** | 将 `QLabel` 换成 `QPushButton` 可能会破坏现有的 `update_icon_states` 颜色逻辑。 | 现有的 `update_icon_states` 已经有处理 Button 图标变色的辅助函数 `set_solid_icon`。我们只需将原来处理 `lbl_notes_icon` 的代码改为调用 `set_solid_icon` 处理 `btn_notes_edit` 即可。这甚至简化了代码一致性。 |

---

## 5. 实施计划 (Implementation Steps)

1.  **配置更新**: 修改 `assets/language.ini` 添加双语字段。
2.  **创建弹窗类**: 新建 `ui/components/notes_editor.py`，实现 UI 和逻辑。
3.  **重构 TimerCard**:
    *   将 `self.lbl_notes_icon` 替换为 `self.btn_notes_edit`。
    *   连接 Click 信号槽函数 `open_notes_editor`。
    *   更新 `update_icon_states` 适配按钮变色逻辑。
4.  **样式微调**: 确保弹窗按钮样式符合 Theme。
5.  **验证**: 
    *   验证弹窗是否能正确读取和回写数据。
    *   验证中英切换。
    *   验证“显示桌面”锁定模式下不可编辑。
