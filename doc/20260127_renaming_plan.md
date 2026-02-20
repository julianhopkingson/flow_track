# 项目重命名方案：流痕 (Flow Track)

本方案详细列出了将项目从“定时鼠标点击 / Mouse Clicker”更名为“流痕 / Flow Track”所需的全部变更。

## 1. 资产与文件重命名 (File Renaming)

| 原始文件路径 | 变更后文件路径 | 目的 |
| :--- | :--- | :--- |
| `assets/mouse-clicker.ico` | `assets/flow-track.ico` | 品牌标识同步 |
| `mouse_clicker.py` | `flow_track.py` | 核心源码命名一致性 |
| `mouse_clicker.spec` | `flow_track.spec` | 打包配置文件同步 |

---

## 2. 交互与多语言配置 (Configuration)

### [修改] `assets/language.ini`
针对界面显示标题进行更新。

```diff
 [中文]
-app_title = 定时鼠标点击
+app_title = 流痕
 ...
 [English]
-app_title = Mouse Clicker
+app_title = Flow Track
```

---

## 3. 打包脚本配置 (Build Script)

### [修改] `flow_track.spec`
更新生成的 EXE 名称及图标引用。

```diff
-a = Analysis(['mouse_clicker.py'], ...)
+a = Analysis(['flow_track.py'], ...)
 ...
 exe = EXE(
     ...
-    name='mouse_clicker',
+    name='flow_track',
-    icon=['assets/mouse-clicker.ico'],
+    icon=['assets/flow-track.ico'],
 )
```

---

## 4. 源代码引用 (Source Code)

### [修改] `flow_track.py`
更新内部资源路径与类名。

```diff
-class MouseClickerApp(tk.Tk):
+class FlowTrackApp(tk.Tk):
     ...
-        icon_path = get_resource_path("assets/mouse-clicker.ico")
+        icon_path = get_resource_path("assets/flow-track.ico")
 ...
-if __name__ == '__main__':
-    app = MouseClickerApp()
+if __name__ == '__main__':
+    app = FlowTrackApp()
```

---

## 5. 文档同步 (Documentation)

### 影响范围：
- `doc/ui_analysis.md`
- `doc/version_1.0_features.md`
- `doc/resource_embedding_design.md`
- `doc/walkthrough.md`

所有文档中的“定时鼠标点击”将统一替换为“流痕”，“Mouse Clicker”替换为“Flow Track”。

---

## 6. 潜在风险与注意事项 (Risks)
1. **EXE 名称变更**：用户之前建立的快捷方式可能会失效。
2. **配置文件冲突**：如果用户习惯了 `dist/mouse_clicker.exe`，切换到 `dist/flow_track.exe` 后，若不手动迁移 `config/` 目录，可能会丢失之前的定时器设定。
3. **UI 截图不一致**：`assets/v1.0_ui_preview.png` 中显示的标题仍为旧名称。建议在重命名并重新构建后，截取一张新的 UI 预览图。

---
*状态：方案已执行并验证通过。 (Status: Executed & Verified)*
