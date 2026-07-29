# 项目升级计划文档：版本 2.3

## 1. 目标
全面将项目系统标识与核心内核升阶至 **"v2.3"** 版本，引入“显示桌面前自动发送 ESC 退出全屏”功能，并彻底修复“显示桌面图标激活时变灰”的状态显示反转 Bug。

## 2. 变更清单

### A. 核心代码与引擎 (Core & UI)
- **单例互斥锁标识**: [main.py](file:///e:/workspace_antigravity/flow_track/main.py)  
  更新互斥锁唯一标识符为 `Local\\FlowTrack_Instance_Mutex_9D2A3B4C-v2.3`。
- **UI 图标状态解耦**: [timer_card.py](file:///e:/workspace_antigravity/flow_track/ui/components/timer_card.py)  
  解耦显示桌面图标高亮逻辑与输入框 `can_edit` 逻辑，新增 `desktop_active` 独立参数控制图标状态。
- **显示桌面执行增强**: [timer_engine.py](file:///e:/workspace_antigravity/flow_track/core/timer_engine.py)  
  在发送 `Win+D` 组合键之前，先模拟发送 `ESC` 键并进行 300 毫秒的微步挂起等待，确保前台全屏窗口正确退出。

### B. 国际化与语言包 (Language)
- **提示文本补充**: [language.ini](file:///e:/workspace_antigravity/flow_track/assets/language.ini)  
  新增 `log_timer_esc_fullscreen` 的中英文日志说明文本。

### C. 架构设计与发布文档 (Documentation)
- **技术设计文档**: [20260729_Design_ShowDesktop_Enhancement.md](file:///e:/workspace_antigravity/flow_track/doc/20260729_Design_ShowDesktop_Enhancement.md)  
  包含完整的全流程 Meramig 状态图与改动前后对照说明。
- **版本发布说明**: [20260729_Release_Note_v2.3.md](file:///e:/workspace_antigravity/flow_track/doc/20260729_Release_Note_v2.3.md)  
  记载 v2.3 版本的更新摘要。

---

```markdown
📌 项目升级计划架构总结 (Version 2.3 Plan)
├── 🎯 升级目标 (Upgrade Objectives)
│   ├── 🚀 版本跳升 (Version Bump to v2.3)
│   ├── 🖥️ 全屏兼容 (Fullscreen Auto-ESC Exit)
│   └── 🎨 视觉矫正 (Icon Color Decoupling)
├── 📦 模块变更清单 (Module Modifications)
│   ├── ⚙️ 核心进程 (main.py Mutex Update)
│   ├── 🎨 界面卡片 (timer_card.py Decoupling)
│   ├── ⏱️ 任务引擎 (timer_engine.py ESC Injection)
│   └── 🌐 语言资源 (language.ini Log Key)
└── 📑 文档产出 (Documentation Artifacts)
    ├── 📘 架构设计文档 (Design Document)
    └── 📜 发版日志说明 (Release Note v2.3)
```
