# iOS 风格 UI 动效与美化重构设计方案

## 1. 现状与问题本质分析 (第一性原理)

**当前系统现状：**
- **底层框架**：基于 PySide6 构建（Python + Qt）。
- **样式系统**：采用动态 QSS 模板替换机制（`theme_template.qss` + `theme_config.py`），已具备浅色/深色模式切换能力。
- **动效现状**：在 `TimerCard` 中已经引入了基于 `QGraphicsDropShadowEffect` 和 `QPropertyAnimation` 的基础悬浮阴影变化动效，但交互反馈较为单一，缺乏“呼吸感”和顺滑的物理回弹体验。
- **UI 风格**：偏向于扁平化与微小圆角设计（12px/20px），色彩饱和度较高。

**问题本质：**
用户需求是在**绝对不改变页面布局和内部业务逻辑**的前提下，让界面获得 iOS 级别的审美与交互体验。这要求我们必须以“非破坏性（Non-destructive）”的方式增加视觉层和动画层。
iOS UI 的精髓在于：
1. **毛玻璃特效 (Material/Blur)**：强烈的层级感，背景透视。
2. **流畅的物理动效 (Fluid Animation)**：按压缩放（Squish）、平滑过渡。
3. **克制的色彩与大圆角**：连续曲线（Squircle）视觉模拟，柔和的高级灰与系统蓝/绿。

---

## 2. 设计方案对比与选择

我们提供两种实现路径以供决策：

### 方案 A：纯 Qt 图形栈模拟方案 (通用性较强)
利用 Qt 自带能力模拟毛玻璃和缩放。

| 特性 | 描述 | 优点 (Pros) | 缺点 (Cons) |
| :--- | :--- | :--- | :--- |
| **毛玻璃** | 使用 `QGraphicsBlurEffect` 截取底层组件背景进行模糊处理 | 跨平台，Windows 低版本可用 | **性能极差**，计算量大，难以实现真正的穿透桌面背景模糊。 |
| **缩放动效** | 捕获鼠标事件，使用 `QPropertyAnimation` 修改 `QGraphicsScale` | 易于实现，不影响原始 Layout 尺寸 | 边缘可能产生锯齿，若元素紧凑可能相互遮挡。 |
| **色彩重构** | 修改 QSS，增加 `border-radius` (统一为 16px/24px) | 安全、无副作用 | 无法做到 iOS 级别的连续平滑圆角（Squircle）。 |

### 方案 B：系统原生 API (DWM) 融合架构 (推荐 - 高级感最高)
直接调用 Windows 11 的 DWM API 实现原生材质，配合高级 Qt 动效框架优化。

| 特性 | 描述 | 优点 (Pros) | 缺点 (Cons) |
| :--- | :--- | :--- | :--- |
| **毛玻璃** | 利用 `ctypes.windll.dwmapi` 启用 Windows 11 的 **Mica / Acrylic** 材质作为主窗口背景。 | **性能极佳**（GPU 硬件加速），真实的系统级高斯模糊。高度还原 iOS 质感。 | 仅限 Windows 10 (构建 1809+) 或 Windows 11。需编写系统的兼容性降级代码。 |
| **缩放动效** | 扩展 `TimerCard` 和按钮组，植入自定义的平滑缩放类（通过拦截 `mousePressEvent` 缩小 0.95x，松开回弹）。 | 交互反馈具有物理感，极大地提升高级感。 | 实现复杂度较高，需处理好事件拦截避免吞没原有点击逻辑。 |
| **色彩重构** | QSS 色板全面迁移至 Apple 官方 Human Interface Guidelines 色系（如 System Gray 6 等）。 | 色彩更柔和，对比度科学。 | 原有的某些高度定制化 QSS 需要仔细微调防止冲突。 |

**最终推荐方案：方案 B**
结合项目现已有通过 `ctypes` 调用 DWM API （在 `main.py` 和 `theme_config.py` 中用于深色标题栏）的技术基础，升级引入 Mica/Acrylic 材质顺理成章，能以最低的性能开销换取最极致的视觉提升。

---

## 3. 详细技术实现路径 (基于方案 B)

### 3.1 原生毛玻璃材质注入 (系统级改造)
- **目标组件**：`MainWindow` 主体背景以及部分悬浮面板。
- **实现方式**：在 `ThemeManager.set_title_bar_theme` 或 `MainWindow` 初始化中，增加针对 `DWMWA_SYSTEMBACKDROP_TYPE` (Windows 11 API 38) 的调用，开启 **Mica Alternative 或 Acrylic** 效果。
- **配合修改**：将 `theme_template.qss` 中的 `[[BG_WINDOW]]` 由纯色替换为 **带有透明度 (Alpha)** 的颜色（如 `rgba(242, 242, 247, 0.6)`），以便让底层的 DWM 模糊效果透出来。

### 3.2 QPropertyAnimation 缩放特效 (交互升维)
- **目标组件**：`TimerCard` 和 常用的操作按键 (`ActionButton`)。
- **实现方式**：
  - 为需要缩放的组件附加 `QGraphicsScale` 对象。
  - 重写 `enterEvent`、`mousePressEvent` 和 `mouseReleaseEvent`。
  - **Hover 动画**：鼠标悬浮时缓慢放大至 1.02x（配合现有阴影）。
  - **Press 动画**：鼠标按压时迅速缩放至 0.96x（iOS 标志性阻尼回弹），松开时采用 `QEasingCurve.OutElastic` 或 `OutBack` 曲线弹回至 1.0x 或 1.02x。

### 3.3 iOS 级 QSS 主题色板体系重组
- **修改 `theme_config.py`**：完全替换现有的 "Heng Dong" 色板。
  - **Light 模式**：背景采用 iOS System Light 灰白（如 `#F2F2F7`），卡片采用纯白 `#FFFFFF`，取消多余的 `border` 和 Raised 人造阴影，改用无边框+大圆角+超柔和实体阴影。
  - **Dark 模式**：背景采用 `#000000` 或 `#1C1C1E`，卡片采用 `#2C2C2E`。
  - **圆角参数**：统一大幅提升，如 `border-radius: 16px` (小元素) 和 `24px` (大容器)。
- **简化代码**：剔除目前卡片为了伪造 "Raised" 效果而设置的 top/bottom 2px 边框，让界面回归纯粹的毛玻璃排版。

---

## 4. 潜在风险评估及其应对策略

> [!WARNING]
> **风险 1：事件吞没与交互失灵 (Event Swallowing)**
> **描述**：重写 `TimerCard` 的鼠标事件（实现按压缩放）可能导致原本用于点击内部按钮、拉取下拉框的事件被拦截，造成功能失效。
> **应对**：在拦截 `mousePressEvent` 等事件时，严格使用 `super().mousePressEvent(event)` 确保事件向子控件正确传递，避免拦截冒泡的子控件事件。

> [!CAUTION]
> **风险 2：透明度导致的文本渲染缺陷 (ClearType 丢失)**
> **描述**：在开启 QWidget 透明底色以显示深层毛玻璃时，Windows 的字库可能会丢失 ClearType 亚像素平滑，导致字体发虚。
> **应对**：对于直接渲染文本的非悬浮区域（如 `LogText` 和 `NotesEditorField`），保留其父容器具有不透明度（Opacity=1的 QFrame 承载），仅对主窗体和卡片间隙应用透明模糊透视。

> [!NOTE]
> **风险 3：系统兼容性降级 (Compatibility)**
> **描述**：Windows 10 旧版或 Windows 7 不支持 DWMWA_SYSTEMBACKDROP_TYPE 这类 API。
> **应对**：使用 `sys.getwindowsversion()` 检测构建版本，如果是低版本系统，则退化回优雅的不透明纯色（当前使用的深/浅色），确保系统核心稳定性。

> [!IMPORTANT]
> **风险 4：布局挤压裁剪 (Layout Clipping)**
> **描述**：使用缩小/放大动效时，组件边界可能因为 Layout 限制被裁剪（特别是放大到 1.02x 时）。
> **应对**：在现有的 Layout 中为 `TimerCard` 等关键组件保留足够的毛边间距（Margins），并确保父容器没有施加严苛的裁切属性（如 `clipChildren: true`）。目前 `TimerCard` 设置的 `margin: 3px 4px` 可能不够伸展，需要适度调大至 `8px` 以策安全。

---

## 5. 接下来需要执行的具体任务
当您确认方案并输入 **「执行」** 后，我将按以下顺序操作：
1. **环境准备**：确认关闭应用进程进程。
2. **底层色彩体系调整**：修改 `theme_config.py`，配置 iOS 极简色彩体系，启用对 Win11 材质的支持预留通道。
3. **样式表重构**：修改 `theme_template.qss`，删除臃肿的伪3D边框，应用大圆角、极简边距与半透明背景。
4. **组件动效注入**：改造 `ui/components/timer_card.py`，实现继承 QPropertyAnimation 和 QGraphicsScale 的优雅缓动缩放效果引擎。

```markdown
📌 Flow Track - UI 美化改良工程 (iOS 风格化)
├── 🧠 核心架构理念 (Core Architectural Concept)
│   ├── 🧊 平台增强：采用 DWM 接口拉取系统底层毛玻璃，避免应用层高耗电模糊
│   ├── 🌊 阻尼反馈：抛弃生硬的 Hover，引入缩放弹性系数模拟真实按压与回弹
│   └── 🎨 极简重构：去除边框，化繁为简，靠光影分割层级
└── 🚀 结论与行动 (Conclusion & Action)
    └── ⏳ 等待指令：已进入静默期，请回复 "执行" 以启动重构代码。
```
