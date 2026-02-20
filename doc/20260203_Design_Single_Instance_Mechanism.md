# 📌 Design Specification: Single Instance Application Mechanism

**Project**: Flow Track  
**Version**: 2.2+  
**Author**: Lead Architect (Antigravity)  
**Date**: 2026-02-03  
**Status**: Draft (Waiting for Approval)

---

## 1. 核心问题 (Problem Statement)
在 Windows 环境下，用户快速连续点击应用图标（Double Click mashing）会触发操作系统的并发进程启动机制。由于每一个新进程在初始化 UI 窗口前都需要一定的加载时间（Python 解释器启动 -> PySide6 加载 -> 资源加载），后续的点击往往在前一个进程建立 "存在感"（如窗口显示）之前就已经启动了新进程。

这导致：
1.  屏幕上出现多个重叠的应用窗口。
2.  `config.ini` 可能面临多进程并发写入的风险（尽管当前逻辑通常是退出保存，但仍不安全）。
3.  全局快捷键或系统资源（如端口、热键）冲突。

## 2. 解决方案评估 (Solution Evaluation)

我们对比了三种业界通用的“单实例”实现方案：

| 方案 | 技术原语 | 优点 (Pros) | 缺点 (Cons) | 推荐指数 |
| :--- | :--- | :--- | :--- | :--- |
| **A. 文件锁 (Lock File)** | `os.open` / `QLockFile` | 跨平台，实现简单，无额外依赖。 | **极高风险**：若程序崩溃（Crash/Kill），锁文件残留会导致程序再也无法启动，必须手动删除。 | ⭐ |
| **B. Qt 共享内存 (QSharedMemory)** | `PySide6.QtCore.QSharedMemory` | Qt 原生，无需引入 OS 特定 API。 | 逻辑稍显复杂（需处理 Attach/Detach），在某些极端崩溃下也可能导致段残留。 | ⭐⭐⭐ |
| **C. Windows 互斥体 (Named Mutex)** | `win32event.CreateMutex` | **OS 内核级对象**。进程结束（无论正常或崩溃）OS 自动释放句柄。**零残留风险**。 | 仅限 Windows（本项目即为 Win 独占），需 `pywin32` (已存在于本项目依赖)。 | ⭐⭐⭐⭐⭐ |

## 3. 架构决策 (Architectural Decision)

基于本项目 **Windows 11** 的目标环境以及已有的 **`pywin32`** 依赖，我们采用 **方案 C: Windows Named Mutex**。

这是一个**内核级 (Kernel-Level)** 的解决方案，它是最稳健的防线。

### 3.1 核心机制
1.  在 `main.py` 的**最早期**（`QApplication` 初始化之前），尝试创建一个**命名互斥体 (Named Mutex)**。
2.  互斥体名称包含唯一的 **GUID**，防止与其他应用冲突。
3.  系统检查：
    -   如果创建成功且 `GetLastError` 返回 `ERROR_ALREADY_EXISTS`：说明已有实例在运行。
    -   **动作**：当前进程立即静默退出 (Exit)。
    -   *可选增强*：尝试找到已有窗口并将其置顶（本次暂不实现，优先保证“只能启动一个”的核心诉求）。

### 3.2 风险与规避 (Risks & Mitigation)

| 风险点 | 规避策略 |
| :--- | :--- |
| **互斥体名称冲突** | 使用 `Local\` 前缀 + UUID 确保唯一性。例如 `Local\FlowTrack_Instance_Mutex_9D2A3B4C`。`Local\` 命名空间仅限当前用户会话，避免多用户登录时的权限问题。 |
| **进程残留** | 如果前一个进程僵死（Zombie）但未完全退出，互斥体可能仍被占用。**策略**：这正是我们想要的——只要旧进程还在占坑，新进程就不该启动。通常 Task Manager 杀掉旧进程即可释放。 |
| **垃圾回收陷阱** | 在 Python 中，如果 Mutex 对象被垃圾回收（GC），句柄可能被关闭。**策略**：将 Mutex 句柄对象保存在全局变量或 `main` 函数的整个生命周期内，防止提前释放。 |

## 4. 详细实施规范 (Implementation Specs)

**目标文件**: `main.py`

### 步骤 1: 引入依赖
```python
import win32event
import win32api
import win32con
from win32error import ERROR_ALREADY_EXISTS
```

### 步骤 2: 定义互斥类
构建一个轻量级的 Context Manager 或工具函数。

```python
# 伪代码示例
mutex_name = "Local\\FlowTrack_Mutex_v2.2_56d7606"
mutex = win32event.CreateMutex(None, False, mutex_name)
if win32api.GetLastError() == ERROR_ALREADY_EXISTS:
    # 发现已有实例
    sys.exit(0)
```

### 步骤 3: 注入点 (Injection Point)
必须在 `app = QApplication(sys.argv)` **之前** 执行检查。这样可以节省大量内存和 CPU，因为被阻挡的进程几乎是瞬间退出的。

## 5. 验收标准 (Verification criteria)
1.  **连点测试**：在资源管理器中极速双击图标 10 次 -> **只能出现 1 个窗口**。
2.  **崩溃测试**：从任务管理器强制结束进程 -> 再次启动 -> **必须能正常启动**（验证无死锁残留）。
3.  **功能完整**：单实例启动后，所有原有功能（定时器、配置加载）正常工作。

---

**⚠️ 等待指令**：
本设计文档已完成。请审核上述方案。
输入 **'执行'** 以授权修改 `main.py`。
