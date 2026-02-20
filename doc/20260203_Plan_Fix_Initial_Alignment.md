# 初始文本对齐修复方案 (Fix Initial Text Alignment)

## 1. 问题分析
用户反馈：“初期显示或者读取 config.ini 的值时，即使没有 focus on，还是没变，这时候其实也应该靠左显示”。

**根本原因**：
`TimerCard.set_values` 方法用于从配置文件加载数据。它直接调用了 `edit_notes.setText(...)`。
与用户手动输入不同，程序化的 `setText` 不会触发 Focus 事件，且 `QLineEdit` 默认可能将视口停留在文本末尾（取决于内部实现或之前的状态）。

`NotesFocusFilter` 仅在 `FocusOut` 时生效，无法捕获这种程序初始化时的状态。

## 2. 解决方案
在 `set_values` 方法中，在设置完文本后，显式调用 `setCursorPosition(0)`。这将强制将光标及视口移动到文本开头。

### 2.1 代码变更 (`ui/components/timer_card.py`)

```python
    def set_values(self, data):
        # ... (现有代码)
        self.edit_notes.setText(str(data.get("paste_text", "")))
        
        # [NEW] 强制初始化时的对齐
        self.edit_notes.setCursorPosition(0)
        
        # ... (现有代码)
```

## 3. 验证计划
1.  **手动测试**：
    - 在 `flow_track` 中找一个 Timer Card。
    - 输入一段很长的文本。
    - 退出程序（保存到 config.ini）。
    - 重新打开程序。
    - **观察**：该长文本是否从第一个字开始显示（靠左显示）。
