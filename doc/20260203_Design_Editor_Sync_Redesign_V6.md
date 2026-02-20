# 编辑器同步与交互重构方案 V6 (The "Interference Removal" Strategy)

## 1. 深度复盘：为什么之前越修越慢？
回顾之前的失败，我们一直专注于“如何更快地刷新”，却忽略了“是什么在阻碍刷新”。

经过对 `timer_card.py` 的再次审查，发现了一个**隐形性能杀手**：
**`TimerCard.enterEvent` 中的 `self.raise_()` 和样式刷新。**

当模态对话框关闭时：
1.  Dialog 消失。
2.  鼠标瞬间“重新进入”了底下的 `TimerCard` 区域。
3.  触发 `enterEvent`。
4.  **灾难发生**：`self.raise_()` 被调用。在 Qt 的 Layout 系统中，调整 Z-Order 可能会触发整个列表的 `Layout` 重排 (Invalidate Layout)。
5.  与此同时，我们正在试图 `setText()` 和 `repaint()`。
6.  **结果**：Layout 计算、样式重算 (`polish`)、阴影动画 (`QPropertyAnimation`) 和文本更新撞车，导致了显著的 UI 冻结（即“延时”）。

而 V5 的 `recover_from_editing` 此时去 `activateWindow`，可能在 Layout 还没稳定时抢夺焦点，导致操作系统层面的输入法状态错乱（即“不可编辑”）。

## 2. V6 重构方案核心 (The "Clean & Detached" Design)

我们要做的不是“加速”，而是“减负”。

### 2.1 策略一：父级剥离 (Detached Parenting)
**旧做法**：`NotesEditorDialog(..., parent=self)`
*   副作用：Dialog 作为 Card 的子窗口，其销毁可能引发 Card 内部的子级重绘。

**新做法**：`NotesEditorDialog(..., parent=self.window())`
*   优势：Dialog 归属于顶层主窗口，与具体的 `TimerCard` 渲染树解耦。

### 2.2 策略二：干扰屏蔽 (Interference Shielding)
在打开弹窗期间，**临时屏蔽** Card 的 Hover 响应。防止弹窗关闭瞬间触发昂贵的 `raise_()` 和动画。

### 2.3 策略三：强权回归 (Authoritative State Reset)
不依赖系统的自动焦点恢复，而是显式地、霸道地重置状态。

## 3. 代码实现 (timer_card.py)

```python
    def open_notes_editor(self):
        """
        V6 Redesign: Interference-Free Interaction
        """
        # 1. 屏蔽干扰 (Suspend potential hover effects)
        # 这一步至关重要，防止弹窗关闭瞬间触发 enterEvent -> raise_() -> Layout Thrashing
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        # 2. 宿主剥离 (Re-parent to Main Window)
        # 将 Dialog 挂载到主窗口，避免对 Card 造成布局压力
        parent_widget = self.window() if self.window() else self
        dialog = NotesEditorDialog(self.edit_notes.text(), self.config, parent_widget)
        
        # 3. 阻塞执行
        result = dialog.exec()
        
        # 4. 恢复干扰屏蔽 (Restore interactions)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        # 5. 处理结果
        if result == QDialog.Accepted:
            new_text = dialog.get_text()
            if new_text != self.edit_notes.text():
                self.edit_notes.setText(new_text)
                # 只有数据变了才需要进一步动作？不，焦点必须恢复。
        
        # 6. 状态与焦点“强权恢复” (Authoritative Reset)
        # 无论是否保存，都要确保 Card 回到可用的状态
        self.force_state_reset()

    def force_state_reset(self):
        """
        强制重置组件状态，无视之前的任何动画或焦点丢失。
        """
        # 计算理论状态
        is_running = not self.btn_del.isEnabled()
        is_desktop = self.chk_desktop.isChecked()
        should_enable = (not is_running) and (not is_desktop)
        
        if should_enable:
            # A. 确保启用
            self.edit_notes.setEnabled(True)
            self.btn_notes_edit.setEnabled(True)
            
            # B. 强制更新样式与重绘 (Sync Update)
            # 此时没有 Animation 干扰，Repaint 是安全的
            self.edit_notes.style().polish(self.edit_notes)
            self.edit_notes.update() 
            
            # C. 焦点夺回 (The Focus Grab)
            self.edit_notes.setFocus()
            
            # D. 模拟一次鼠标进入 (Optional, restore hover effect visually if mouse is here)
            # 但为了稳妥，我们先保持静态，让用户动鼠标自然触发
```

## 4. 验证计划
1.  **性能验证**：关闭弹窗是否还有 1s 以上的卡顿？（预期：因移除了 `raise_()` 干扰，应瞬间完成）。
2.  **焦点验证**：点击保存后，能否直接打字？
3.  **副作用检查**：Card 的阴影和 Hover 效果是否在鼠标移动后恢复正常？
