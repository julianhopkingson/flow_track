# 架构设计方案：资源归档与 EXE 内部嵌入自动化 (Resource Embedding Design)

**角色：** 首席架构师 (Lead Architect)  
**目标：** 实现 `flow-track.ico` 从根目录迁移至 `assets/` 目录，并确保其作为资源嵌入 EXE 内部，而非以外部文件形式依赖。

---

## 1. 核心改进策略
作为架构师，我主张不仅要解决“图片位置”问题，更要建立一套健壮的**资源寻址机制**。目前的实现方案存在资源路径强依赖于外部文件系统的风险，在不同打包环境下可能导致“图标找不到”的崩溃。

### 1.1 资源归档 (Archive Strategy)
将根目录下的 `flow-track.ico` 迁移至 `assets/v1.0_ui_preview.png` 所在的同级目录。
*   **目标路径**：`/assets/flow-track.ico`
*   **收益**：保持根目录简洁，符合“源码与资产分离”的业界标准。

### 1.2 资源嵌入逻辑 (Embedding Logic)
我们将利用 PyInstaller 的 `sys._MEIPASS` 属性。当应用以 EXE 模式运行时，PyInstaller 会将所有 `datas` 声明的文件解压到一个临时目录。我们需要一个通用的路径解析函数来适配“开发环境”与“生产 EXE 环境”。

---

## 2. 详细实现路线图

### A. 打包配置改进 (PyInstaller .spec)
修改 `flow_track.spec`，确保图标在两个维度被正确处理：应用外壳图标（EXE 外观）和运行期资源（Tkinter 内部引用）。

```python
# 修改 a.datas，将 assets 目录整体打包进 EXE 内部
datas=[('assets', 'assets')], 

# 修改 exe 块的 icon 路径
exe = EXE(
    ...
    icon=['assets/flow-track.ico'],  # 指向新位置
    ...
)
```

### B. 代码层路径抽象 (Python Source)
在 `flow_track.py` 中引入 `get_resource_path` 辅助函数。

```python
def get_resource_path(relative_path):
    """
    获取资源的绝对路径，适配开发环境和 PyInstaller 打包环境。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 修改 Tkinter 的加载方式
icon_path = get_resource_path("assets/flow-track.ico")
if os.path.exists(icon_path):
    self.iconbitmap(icon_path)
```

---

## 3. 风险评估与防控 (Risk Management)

| 风险项 | 严重程度 | 说明 | 应对措施 |
| :--- | :--- | :--- | :--- |
| **运行时路径失效** | 高 | 在 EXE 模式下，直接引用 `assets/` 会指向当前运行目录而非解压目录。 | 必须使用 `sys._MEIPASS` 动态寻址。 |
| **多图标缓存问题** | 中 | Windows 资源管理器有时会缓存 EXE 的旧图标。 | 打包后手动清理图标缓存或更改 EXE 文件名进行验证。 |
| **反病毒软件阻断** | 低 | 某些杀毒软件对带嵌入式资源且未签名的单文件 EXE 敏感。 | 建议在打包时使用 `--upx` 压缩（当前已禁用，建议维持现状以降低假阳性）。 |
| **临时目录锁定** | 低 | `_MEIPASS` 目录在某些受限环境下（如 Read-only Temp）可能无法写入。 | 仅进行资源读取，严禁向解压目录写入任何持久化配置（Config.ini 应保留在外部）。 |

---

## 4. 结论
本方案通过“路径抽象化”彻底解决了资源路径脆弱的问题方案实施后，`flow_track.exe` 将成为一个真正独立的可执行文件，不再依赖外部的 `.ico` 文件。

> [!IMPORTANT]
> **待确认事项：**
> 1. 打包时是否需要将 `language.ini` 一并嵌入？（目前建议暂时只处理图标，保持语言文件可外部修改以方便国际化扩充）。

---
*设计者：首席架构师 (Lead Architect)*  
*状态：方案已锁定，等待“执行”指令。*
