# 开发与构建协议 (Dev Protocol)

> **重要**：此文档记录了用户强制要求的开发交互规则，Agent 必须严格遵守。

## 1. 构建流程 (Build Workflow)
在每次修改代码后进行验证时，必须严格遵循以下顺序操作：

1.  **清理进程** (Pre-build Cleanup)
    - 执行命令：`taskkill /F /IM flow_track.exe /T`
    - 目的：解除文件占用锁定，确保打包顺利覆盖。
    - 注意：即使进程未运行导致报错也可忽略，但必须先尝试执行。

2.  **执行打包** (Build)
    - 执行命令：`pyinstaller main.spec --clean --noconfirm`
    - 目的：生成最新的可执行文件。

3.  **启动验证** (Run & Verify)
    - 执行命令：`e:\workspace_antigravity\flow_track\dist\flow_track.exe` (使用绝对路径)
    - **关键要求**：
        - 必须在打包后自动打开 App。
        - **不要关闭** App，保持前台运行以便用户直接核对效果。

## 2. 版本控制 (Version Control)
- **绝对禁止** (Strictly Prohibited)：
    - 未经用户明确口头/书面指令，严禁执行 `git commit`和`git push`。
- **允许**：
    - 可以执行 `git status` 或 `git diff` 查看状态。

---
*Last Updated: 2026-01-28*
