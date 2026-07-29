# 项目升级计划文档：版本 2.2

## 1. 目标
全面将项目标识从 "v2.0" / "v2.1" 升级至 **"v2.2"**，确保文档、资源和软件界面的一致性。

## 2. 变更清单

### A. 静态资源
**路径**: `flow_track/assets/`
仅修改文件名，以匹配新版本号（内容无需变动）：
- `v2.0_ui_preview.png` -> `v2.2_ui_preview.png`
- `v2.0_ui_preview_cn.png` -> `v2.2_ui_preview_cn.png`

### B. 文档
**路径**: `flow_track/README.md` 与 `flow_track/README_CN.md`
更新对预览图的引用链接：
- `![Software Preview](assets/v2.0_ui_preview.png)` -> `...(assets/v2.2_ui_preview.png)`
- `![软件预览](assets/v2.0_ui_preview_cn.png)` -> `...(assets/v2.2_ui_preview_cn.png)`

### C. 排除项
根据指示，以下内容**保持不变**：
- **软件配置**: `language.ini` 保持原样，不添加版本号。
- **代码注释**: `main_window.py` 等文件中的 `v2.0` 历史注释保留，不进行批量替换。
- **图片内容**: 现有截图已是最新的，仅需重命名，无需重新截图。

## 3. 执行步骤
1. **重命名资源**: 执行文件重命名操作。
2. **更新文档**: 替换自述文件中的链接。
3. **提交规则**: 遵照约定式提交规范。

```markdown
📌 项目升级计划架构总结 (Version 2.2 Plan)
├── 🎯 核心目标 (Core Goal)
│   └── 🚀 标识统一 (Unified Branding to v2.2)
├── 📦 变更清单 (Change List)
│   ├── 🖼️ 静态资源 (Assets Renaming)
│   ├── 📄 自述文档 (README Links Update)
│   └── 🛡️ 排除规则 (Explicit Exclusions)
└── 🏁 执行步骤 (Execution Flow)
    └── ✅ 资产重命名与文档同步 (Sync Assets & Docs)
```
