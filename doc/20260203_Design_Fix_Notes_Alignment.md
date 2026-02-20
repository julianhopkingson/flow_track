# 文本框对齐与焦点行为修复方案 (Notes Alignment & Focus Fix)

## 1. 问题分析
用户需求：“文本文档，当focus no on也就是focus off时，得靠左显示”。

**现状**：
`QLineEdit` 的默认行为是：当文本超过显示区域时，显示内容跟随光标位置。
- 如果用户编辑或查看到文本末尾，然后点击其他地方失去焦点（Focus Out），`QLineEdit` **会保持显示末尾的内容**，而不会自动滚动回开头。
- 这导致长文本在“查看模式”下看起来像是“右对齐”或截断了开头。

**根本原因**：
缺少 `FocusOut` 时的自动归位（Auto-Home）机制。

## 2. 解决方案 (Auto-Home Strategy)
我们需要监听 `edit_notes` 的 `FocusOut` 事件，并在此时强制将光标移动到位置 0（文本开头）。

### 2.1 实现方式
使用 Qt 的 `eventFilter` 机制。我们可以复用现有的 filter 结构或新建一个简单的 Filter 类。

**逻辑流**：
1.  用户在文本框内操作（光标可能在任意位置）。
2.  用户点击外部（触发 `QEvent.FocusOut`）。
3.  Filter 捕获该事件。
4.  执行 `lineEdit.setCursorPosition(0)`。
5.  结果：文本框内容滚动回最左侧，符合“靠左显示”的视觉预期。

### 2.2 代码设计 (timer_card.py)

```python
class NotesFocusFilter(QObject):
    """
    Auto-scroll to start when focus is lost.
    Ensures long text is displayed from the beginning ("Left Aligned" view) 
    when not actively editing.
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            # 必须调用父类处理，保证正常的 FocusOut 逻辑（如样式变化）先执行或后执行
            # 这里我们在处理完内置逻辑后，强制归位
            # 但为了安全，先调用 standard processing? 
            # 通常 return False 让 Qt 继续处理即可，我们只是 side-effect。
            
            # 强制视口回到左侧
            obj.setCursorPosition(0) # 将光标置于开头，视口自动跟随
            
            # 如果不想改变用户的光标记忆，可以使用 setSelection(0, 0) 但 setCursorPosition 最稳
            
        return super().eventFilter(obj, event)
```

**集成点**：
在 `TimerCard.__init__` 中实例化并安装此 Filter。

```python
    self.notes_focus_filter = NotesFocusFilter(self)
    self.edit_notes.installEventFilter(self.notes_focus_filter)
```

## 3. 验证计划
1.  **手动测试**：
    - 输入一段超长文本（超过显示宽度）。
    - 将光标移到末尾（显示右侧内容）。
    - 点击界面其他空白处使文本框失焦。
    - **预期**：文本框内容立即滚动回开头，“靠左显示”。
