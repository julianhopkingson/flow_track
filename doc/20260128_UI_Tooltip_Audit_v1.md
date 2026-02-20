# UI 悬停说明 (Tooltip) 全面审计报告

本项目旨在提升 **Flow Track** 的用户体验，确保所有交互元素在鼠标悬停时均有清晰的中文/英文说明。以下是当前 UI 状态的完整盘点。

---

## 1. Header (页眉区域)

| UI 元素 | 变量名 | 当前 Tooltip | 语言包 Key | 建议说明 (中文) |
| :--- | :--- | :--- | :--- | :--- |
| **语言切换图标** | `lbl_lang_sel` | ✅ 有 | `tooltip_lang_sel` | 切换界面语言 |
| **语言下拉框** | `combo_lang` | ✅ 有 | `tooltip_combo_lang` | 选择界面语言 (中文 / English) |
| **加载配置文件** | `btn_load` | ✅ 有 | `tooltip_btn_load_config` | 加载外部 .ini 配置文件 |
| **批量复制图标** | `lbl_copy_range_sel` | ✅ 有 | `label_copy_range` | 批量复制范围：点击下方复制按钮将同步修改后 N 行 |
| **批量复制下拉框** | `combo_copy_range` | ✅ 有 | `tooltip_copy_range_combo` | 设置向下同步的任务数量 |
| **坐标探测图标** | `lbl_coord_icon` | ✅ 有 | `tooltip_coord_icon` | 当前鼠标实时位置 (相对于屏幕左上角) |
| **坐标显示数值** | `lbl_coords` | ✅ 有 | `tooltip_coords` | 鼠标坐标实时数值 (X, Y) |
| **开始按钮** | `btn_start` | ✅ 有 | `tooltip_btn_start` | 开始执行所有选中的定时任务 |
| **停止按钮** | `btn_stop` | ✅ 有 | `tooltip_btn_stop` | 停止当前正在运行的所有任务 |

---

## 2. Timer Card (任务行区域)

| UI 元素 | 变量名 | 当前 Tooltip | 语言包 Key | 建议说明 (中文) |
| :--- | :--- | :--- | :--- | :--- |
| **删除按钮** | `btn_del` | ✅ 有 | `tooltip_btn_delete_timer` | 删除此任务行 |
| **添加按钮** | `btn_add` | ✅ 有 | `tooltip_btn_insert_timer` | 在此行后插入新任务 |
| **上移按钮** | `btn_up` | ✅ 有 | `tooltip_btn_up_timer` | 将任务行上移 |
| **下移按钮** | `btn_down` | ✅ 有 | `tooltip_btn_down_timer` | 将任务行下移 |
| **启用开关** | `chk_enabled` | ✅ 有 | `tooltip_row_enabled` | 启用/禁用此行任务 |
| **坐标输入 (X/Y)** | `edit_x/y` | ✅ 有 | `tooltip_edit_x/y` | 点击触发的屏幕 X/Y 坐标 |
| **时间设置** | `spin_h/m/s` | ✅ 有 | `tooltip_spin_time` | 任务执行的具体时刻 (时:分:秒) |
| **行内复制按钮** | `btn_copy` | ✅ 有 | `tooltip_btn_copy` | 向下批量同步此行的设置 |
| **显示桌面图标** | `lbl_desktop_icon` | ✅ 有 | `tooltip_show_desktop` | 显示桌面模式：执行此行时将最小化所有窗口 |
| **显示桌面开关** | `chk_desktop` | ✅ 有 | `tooltip_chk_desktop` | 开启显示桌面模式 (将自动清空并锁定坐标与点击项) |
| **点击次数图标** | `lbl_clicks_icon` | ✅ 有 | `tooltip_clicks_icon` | 点击执行次数 |
| **点击次数输入** | `edit_clicks` | ✅ 有 | `tooltip_clicks_icon` | 设置连续点击的次数 |
| **点击间隔图标** | `lbl_interval_icon` | ✅ 有 | `tooltip_interval_icon` | 点击间隔时间 (秒) |
| **点击间隔输入** | `edit_interval` | ✅ 有 | `tooltip_interval_icon` | 设置多次点击之间的时间间隔 |
| **备注输入框** | `edit_notes` | ✅ 有 | `tooltip_edit_notes` | 需要粘贴的文本 (执行时将自动粘贴文本至当前光标处) |
| **备注编辑按钮** | `btn_notes_edit` | ✅ 有 | `tooltip_btn_notes_edit` | 打开多行文本编辑器 |

---

## 3. Log (日志区域)

| UI 元素 | 变量名 | 当前 Tooltip | 语言包 Key | 建议说明 (中文) |
| :--- | :--- | :--- | :--- | :--- |
| **日志标题** | `lbl_log_header` | ❌ 无 | - | 操作记录与系统消息 |
| **日志文本域** | `txt_log` | ❌ 无 | - | 详细的运行日志输出 |

---

## 🛠️ 改善方案建议

1.  **统一语言包引用**：将所有硬编码（如 `Delete`）替换为 `self.config.get_message("...")`。
2.  **补全图标说明**：由于 UI 采用极简图标设计，为 **图标本身** 和 **关联输入框** 增加 Tooltip 对新用户非常有帮助。
3.  **多语言同步**：更新 `language.ini`，确保每个新增的 Tooltip 都有配套的中英文翻译。
4.  **动态刷新**：在 `retranslate_ui` (MainWindow & TimerCard) 中加入这些 Tooltip 的设置，确保语言切换时说明也同步切换。

> [!IMPORTANT]
> **状态声明**：此方案仅为设计与盘点结果。在获得“执行”指令前，不会对现有代码库进行任何修改。
