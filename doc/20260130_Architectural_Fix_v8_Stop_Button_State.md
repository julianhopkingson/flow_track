# 架构设计方案 v8.1：停止按钮状态恢复机制优化 (对比旧版优化建议)

## 旧版逻辑分析 (Heritage Review)
通过阅读 `doc/mouse_clicker.py`，发现旧版处理极其简单：
1. **状态切换**：`start_timers` 仅仅是将 `btn_start` 禁用了。
2. **解锁机制**：它并没有像新版这样试图通过子线程信号自动恢复 UI，而是完全依赖 `stop_timers` 手动恢复。
3. **弊端**：如果计时器任务全部自然结束，旧版的 UI 依然会锁死在“开始按钮被禁用”的状态，除非用户手动点“停止”（这对用户来说体验很差）。

## 现状诊断
新版引入了 `on_task_finished(is_last)` 试图实现全自动恢复。这是一个进步，但其实现的**脆弱点**在于：
- **`is_last` 强约束**：它强制要求必须有且仅有一个任务被标记为 `is_last` 并且成功发出该信号。
- **信号丢失后果**：一旦那个“天选之子”所在的线程因为任何原因（甚至就是因为挂机时间太长导致主线程循环由于某种原因错过了信号通知）没能送达信号，UI 就无法恢复。

## 升级版设计方案 (Selected Solution)

为了兼顾“自动恢复”的便利性和“即使信号丢失也能解锁”的鲁棒性，方案调整如下：

### 1. 核心监测器 (MainWindow 增强)
引入一个 **UI 兜底保护计数器** 或 **活跃检查器**：
- **逻辑**：在 `start_timers` 时，记录当前真正启动的线程总数 `active_tasks_count`。
- **解耦**：不再强依赖特定的 `is_last` 标记信号。
- **计数下降**：每当接收到 `on_task_finished` 信号（无论是否是最后一个），`active_tasks_count` 减 1。
- **强制解锁触发**：当 `active_tasks_count` 降至 0 时，执行 `set_ui_locked(False)`。

### 2. 长时间挂机保护 (Active Monitoring)
针对用户提到的“挂机几小时后点击停止无效”：
- **方案**：在 `stop_timers` 中，不再只是调用 `engine.stop_all()`，而是增加一次显式的 **UI 状态同步原语**。
- **代码动作**：
  ```python
  def stop_timers(self):
      self.engine.stop_all() # 停止引擎
      # 显式强制解锁
      self.set_ui_locked(False) 
      # 立即刷新 UI 状态
      QApplication.processEvents() 
  ```

### 3. 定时器引擎鲁棒性 (Engine 增强)
在 `TimerEngine.stop_all()` 内部增加对阻塞操作的清理，确保即使长时间无响应的线程也能被快速 `quit` 和 `wait`。

## 潜在风险与应对
- **计数器偏移**：如果某个任务崩溃且未发出 `finished` 信号，计数器将无法清零。
  - **对策**：在 `MainWindow` 中依然保留一个 1 秒周期的 `watchdog_timer`。如果检测到 `active_tasks_count > 0` 但引擎内部反馈 `is_any_worker_running() == False`，则强制清零计数器并解锁。

## 验证计划 (Verification Plan)
1. **边界测试**：只勾选一个已过期的计时器，点击开始，确认 UI 是否能立即解锁（不再卡死）。
2. **并发测试**：勾选多个计时器，快速连续点击开始/停止，观察 UI 状态是否能正确同步。
3. **长时间模拟**：通过代码模拟一个极长等待的任务，手动触发停止按钮，检查反馈。
