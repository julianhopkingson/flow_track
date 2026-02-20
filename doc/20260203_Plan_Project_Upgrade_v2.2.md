# Project Upgrade Plan: Version 2.2

## 1. 目标 (Goal)
全面将项目标识从 "v2.0" / "v2.1" 升级至 **"v2.2"**，确保文档、资源和软件界面的一致性。

## 2. 变更清单 (Change List)

### A. 静态资源 (Assets)
**路径**: `flow_track/assets/`
仅修改文件名，以匹配新版本号（内容无需变动）：
- [ ] `v2.0_ui_preview.png` -> `v2.2_ui_preview.png`
- [ ] `v2.0_ui_preview_cn.png` -> `v2.2_ui_preview_cn.png`

### B. 文档 (Documentation)
**路径**: `flow_track/README.md` & `flow_track/README_CN.md`
更新对预览图的引用链接：
- [ ] `![Software Preview](assets/v2.0_ui_preview.png)` -> `...(assets/v2.2_ui_preview.png)`
- [ ] `![软件预览](assets/v2.0_ui_preview_cn.png)` -> `...(assets/v2.2_ui_preview_cn.png)`

### C. 排除项 (Exclusions)
根据指示，以下内容**保持不变**：
- **软件配置 (Config)**: `language.ini` 保持原样，不添加版本号。
- **代码注释 (Comments)**: `main_window.py` 等文件中的 `v2.0` 历史注释保留，不进行批量替换。
- **图片内容**: 现有截图已是最新的，仅需重命名，无需重新截图。

## 3. 执行步骤 (Execution Steps)
1.  **Rename Assets**: 执行文件重命名操作。
2.  **Update Docs**: 替换 README 中的链接。
3.  **Commit**: 提交更为 "chore: upgrade project assets to v2.2"。
