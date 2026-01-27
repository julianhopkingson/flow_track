import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import configparser
import threading, time, datetime
import win32api, win32con
import pyperclip  # For clipboard operations

LANGUAGE_FILE = "assets/language.ini"
CONFIG_FILE = "config/config.ini"

def get_resource_path(relative_path):
    """
    获取资源的绝对路径，适配开发环境和 PyInstaller 打包环境。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class TimerRow:
    def __init__(self, parent, grid_row_index, lang_texts, app=None, data=None, log_timer_row_index_in_list=0):
        """
        创建一行定时器控件
        """
        self.parent = parent
        self.app = app
        self.lang = lang_texts
        self.grid_row = grid_row_index # Tkinter grid的行号
        self.log_timer_row_index_in_list = log_timer_row_index_in_list # 在 app.timer_rows 列表中的索引

        col_offset = 0 # 用于控制列的起始

        # 删除按钮 ("x" / "删")
        self.btn_delete = ttk.Button(parent, text=lang_texts.get("button_delete_timer", "x"), width=3, command=lambda: self.app.delete_log_timer_row_by_object(self))
        self.btn_delete.grid(row=self.grid_row, column=col_offset, padx=1, pady=2, sticky="w")
        col_offset += 1

        # 插入按钮 ("add" / "插入")
        self.btn_add = ttk.Button(parent, text=lang_texts.get("button_insert_timer", "add"), width=4, command=lambda: self.app.insert_log_timer_row_after_object(self))
        self.btn_add.grid(row=self.grid_row, column=col_offset, padx=1, pady=2, sticky="w")
        col_offset += 1

        # 往上按钮
        self.btn_up = ttk.Button(parent, text=lang_texts.get("button_up_timer", "up"), width=3, command=lambda: self.app.move_timer_row_up(self))
        self.btn_up.grid(row=self.grid_row, column=col_offset, padx=1, pady=2, sticky="w")
        col_offset += 1

        # 往下按钮
        self.btn_down = ttk.Button(parent, text=lang_texts.get("button_down_timer", "down"), width=3, command=lambda: self.app.move_timer_row_down(self))
        self.btn_down.grid(row=self.grid_row, column=col_offset, padx=1, pady=2, sticky="w")
        col_offset += 1

        self.enabled = tk.BooleanVar()
        self.chk = tk.Checkbutton(parent, variable=self.enabled)
        self.chk.grid(row=self.grid_row, column=col_offset, padx=1, pady=2, sticky="w")
        col_offset += 1

        self.entry_x = tk.Entry(parent, width=6)
        self.entry_x.grid(row=self.grid_row, column=col_offset, padx=2, sticky="w")
        col_offset += 1
        self.entry_y = tk.Entry(parent, width=6)
        self.entry_y.grid(row=self.grid_row, column=col_offset, padx=2, sticky="w")
        col_offset += 1

        # 时分秒三个spinbox
        self.time_frame = tk.Frame(parent)
        self.time_frame.grid(row=self.grid_row, column=col_offset, padx=2, sticky="w")
        col_offset += 1

        # 小时 (0-23)
        self.hour_var = tk.StringVar()
        self.hour_spinbox = tk.Spinbox(self.time_frame, from_=0, to=23, width=2, format="%02.0f", textvariable=self.hour_var)
        self.hour_spinbox.pack(side="left")

        tk.Label(self.time_frame, text=":").pack(side="left")

        # 分钟 (0-59)
        self.minute_var = tk.StringVar()
        self.minute_spinbox = tk.Spinbox(self.time_frame, from_=0, to=59, width=2, format="%02.0f", textvariable=self.minute_var)
        self.minute_spinbox.pack(side="left")

        tk.Label(self.time_frame, text=":").pack(side="left")

        # 秒钟 (0-59)
        self.second_var = tk.StringVar()
        self.second_spinbox = tk.Spinbox(self.time_frame, from_=0, to=59, width=2, format="%02.0f", textvariable=self.second_var)
        self.second_spinbox.pack(side="left")

        # 复制按钮
        self.btn_copy = ttk.Button(parent, text=lang_texts.get("button_copy", "Copy"), width=5, command=lambda: self.app.copy_time_settings(self.log_timer_row_index_in_list))
        self.btn_copy.grid(row=self.grid_row, column=col_offset, padx=1, sticky="w")
        col_offset += 1

        # "显示桌面" Checkbutton
        self.show_desktop_var = tk.BooleanVar(value=False)  # 默认不选中
        # 创建一个 Frame 来容纳标签和 Checkbutton，以便它们在同一列中并排显示
        self.show_desktop_frame = tk.Frame(parent)
        self.show_desktop_frame.grid(row=self.grid_row, column=col_offset, padx=(2,2), pady=2, sticky="w")
        col_offset += 1

        # 标签 "显示桌面" - 现在放置在 Frame 内部，在 Checkbutton 左侧
        self.lbl_show_desktop = ttk.Label(self.show_desktop_frame, text=lang_texts.get("radio_show_desktop", "Show Desktop"))
        self.lbl_show_desktop.grid(row=0, column=0, sticky='e', padx=(0, 0), ipadx=0)  # 靠右对齐，右侧无额外边距

        # Checkbutton "显示桌面" - 不再需要自带文本，文本由旁边的Label提供
        self.chk_show_desktop_button = tk.Checkbutton(self.show_desktop_frame, variable=self.show_desktop_var, command=self.toggle_show_desktop_widgets)
        self.chk_show_desktop_button.grid(row=0, column=1, sticky='w', padx=(0, 0), ipadx=0)  # 靠左对齐，左侧无额外边距

        # 新增: 配置show_desktop_frame的列，以使其内容更紧凑
        # 第0列 (文本标签radio_show_desktop所在列): 不扩展权重，列内边距为0
        self.show_desktop_frame.columnconfigure(0, weight=0, pad=0)
        # 第1列 (复选框chk_show_desktop_button所在列): 不扩展权重，列内边距为0
        self.show_desktop_frame.columnconfigure(1, weight=0, pad=0)

        # 点击次数按钮
        self.entry_clicks = tk.Entry(parent, width=6)
        self.entry_clicks.grid(row=self.grid_row, column=col_offset, padx=2, sticky="w")
        col_offset += 1

        # 间隔时间(s)按钮
        self.entry_interval = tk.Entry(parent, width=6)
        self.entry_interval.grid(row=self.grid_row, column=col_offset, padx=2, sticky="w")
        col_offset += 1

        # 添加粘贴文本区域
        self.paste_text_frame = tk.Frame(parent)
        self.paste_text_frame.grid(row=self.grid_row, column=col_offset, padx=2, pady=2, sticky="ew")
        self.paste_text = scrolledtext.ScrolledText(self.paste_text_frame, width=100, height=3, relief="sunken", borderwidth=1)
        self.paste_text.pack(fill="both", expand=True)

        # 如果有预设数据，则填充
        if data:
            try:
                self.enabled.set(data.get("enabled", False))

                # 解析时间字符串为时分秒
                time_str = data.get("time", "")
                if len(time_str) == 6:  # 确保格式为HHMMSS
                    self.hour_var.set(time_str[0:2])
                    self.minute_var.set(time_str[2:4])
                    self.second_var.set(time_str[4:6])
                else:
                    self.hour_var.set("00")
                    self.minute_var.set("00")
                    self.second_var.set("00")

                # 在设置 clicks, interval, paste_text 之前，先设置 show_desktop 状态
                # 因为 toggle_show_desktop_widgets 会根据 show_desktop_var 的状态来决定是否清空和禁用它们
                show_desktop_state_str = data.get("show_desktop", "0")  # 从配置读取的是字符串
                show_desktop_state = show_desktop_state_str == "1"
                self.show_desktop_var.set(show_desktop_state)
                # 调用一次以根据初始状态更新控件，但不触发其内部的清空，因为我们下面会加载值
                self.update_dependent_widgets_state(show_desktop_state)

                if not show_desktop_state:  # 只有在非显示桌面模式下才加载这些值
                    self.entry_x.insert(0, data.get("x", ""))
                    self.entry_y.insert(0, data.get("y", ""))
                    self.entry_clicks.insert(0, data.get("clicks", ""))
                    self.entry_interval.insert(0, data.get("interval", ""))
                    # 填充粘贴文本
                    if "paste_text" in data:
                        paste_text_val = data.get("paste_text", "")
                        self.paste_text.insert(tk.END, paste_text_val)
                else:  # 如果是显示桌面模式，确保它们是空的（即使配置文件中有值也不加载）
                    self.entry_x.delete(0, tk.END)
                    self.entry_y.delete(0, tk.END)
                    self.entry_clicks.delete(0, tk.END)
                    self.entry_interval.delete(0, tk.END)
                    self.paste_text.delete("1.0", tk.END)
            except Exception as e:
                self.app.log(self.app.get_log_message("error_load_timer_data", error=str(e)))

        self.hour_spinbox.bind("<KeyRelease>", self.validate_hour)
        self.minute_spinbox.bind("<KeyRelease>", self.validate_minute)
        self.second_spinbox.bind("<KeyRelease>", self.validate_second)

        # --- 为TimerRow内的“安全”子控件绑定滚轮事件转发 ---
        if self.app and hasattr(self.app, 'on_mousewheel'):
            wheel_callback = lambda event: self.app.on_mousewheel(event)

            # 定义一个列表，包含那些应该转发滚轮事件的控件
            # 不包括 Spinbox 和 ScrolledText (self.paste_text)
            widgets_to_bind_for_global_scroll = [
                self.btn_delete, self.btn_add, self.btn_up, self.btn_down,
                self.chk,
                self.entry_x, self.entry_y,
                self.entry_clicks, self.entry_interval,
                self.btn_copy,
                # Frames (它们本身以及它们内部的非特殊子控件)
                self.time_frame,
                self.show_desktop_frame,
                self.paste_text_frame, # 注意：self.paste_text (ScrolledText) 不绑定
                # Labels and Checkbuttons within Frames (if not covered by Frame binding & bubbling)
                self.lbl_show_desktop,
                self.chk_show_desktop_button,
            ]

            # 为time_frame内的Label控件也绑定
            for child in self.time_frame.winfo_children():
                if isinstance(child, tk.Label):
                    widgets_to_bind_for_global_scroll.append(child)

            for widget in widgets_to_bind_for_global_scroll:
                if widget and widget.winfo_exists(): # 确保控件存在
                    # 使用 add="+" 来确保我们添加绑定而不是替换可能存在的其他滚轮绑定（尽管对这些控件不常见）
                    widget.bind("<MouseWheel>", wheel_callback, add="+")

    def update_dependent_widgets_state(self, is_show_desktop_mode):
        # 根据是否为显示桌面模式更新相关控件的状态和内容
        if is_show_desktop_mode:
            # 选中时，清空并禁用 X, Y, 点击次数, 间隔秒数, 文档
            self.entry_x.delete(0, tk.END)
            self.entry_x.config(state="disabled")
            self.entry_y.delete(0, tk.END)
            self.entry_y.config(state="disabled")
            self.entry_clicks.delete(0, tk.END)
            self.entry_clicks.config(state="disabled")
            self.entry_interval.delete(0, tk.END)
            self.entry_interval.config(state="disabled")
            self.paste_text.delete("1.0", tk.END)
            self.paste_text.config(state="disabled")
        else:
            # 取消选中时，恢复这些输入框为可用状态
            self.entry_x.config(state="normal")
            self.entry_y.config(state="normal")
            self.entry_clicks.config(state="normal")
            self.entry_interval.config(state="normal")
            self.paste_text.config(state="normal")

    def toggle_show_desktop_widgets(self):
        """
        当 "显示桌面" Checkbutton 状态改变时调用。
        如果选中，则清空并禁用点击次数、间隔和粘贴文本。
        如果未选中，则启用它们。
        """
        is_selected = self.show_desktop_var.get()
        self.update_dependent_widgets_state(is_selected)

    def destroy_widgets(self):
        # 销毁所有控件 (用于删除行时)
        self.btn_delete.destroy()
        self.btn_add.destroy()
        self.btn_up.destroy()
        self.btn_down.destroy()
        self.chk.destroy()
        self.entry_x.destroy()
        self.entry_y.destroy()
        self.time_frame.destroy()
        self.btn_copy.destroy()
        self.show_desktop_frame.destroy()
        self.entry_clicks.destroy()
        self.entry_interval.destroy()
        self.paste_text_frame.destroy()

    def get_values(self):
        # 将时分秒合并为HHMMSS格式
        time_str = f"{self.hour_var.get().zfill(2)}{self.minute_var.get().zfill(2)}{self.second_var.get().zfill(2)}"

        return {
            "enabled": self.enabled.get(),
            "x": self.entry_x.get(),
            "y": self.entry_y.get(),
            "time": time_str,
            "show_desktop": self.show_desktop_var.get(),
            "clicks": self.entry_clicks.get(),
            "interval": self.entry_interval.get(),
            "paste_text": self.paste_text.get("1.0", tk.END).strip()
        }

    def disable(self):
        self.btn_delete.config(state="disabled")
        self.btn_add.config(state="disabled")
        self.btn_up.config(state="disabled")
        self.btn_down.config(state="disabled")
        self.chk.config(state="disabled")
        self.entry_x.config(state="disabled")
        self.entry_y.config(state="disabled")
        self.hour_spinbox.config(state="disabled")
        self.minute_spinbox.config(state="disabled")
        self.second_spinbox.config(state="disabled")
        self.btn_copy.config(state="disabled")
        self.chk_show_desktop_button.config(state="disabled")
        self.entry_clicks.config(state="disabled")
        self.entry_interval.config(state="disabled")
        self.paste_text.config(state="disabled")

    def enable(self):
        self.btn_delete.config(state="normal")
        self.btn_add.config(state="normal")
        self.btn_up.config(state="normal")
        self.btn_down.config(state="normal")
        self.chk.config(state="normal")
        self.entry_x.config(state="normal")
        self.entry_y.config(state="normal")
        self.hour_spinbox.config(state="normal")
        self.minute_spinbox.config(state="normal")
        self.second_spinbox.config(state="normal")
        self.btn_copy.config(state="normal")
        self.chk_show_desktop_button.config(state="normal")
        self.update_dependent_widgets_state(self.show_desktop_var.get())

    def validate_hour(self, event):
        """验证小时输入，超出 23 则仅保留最后输入的数字"""
        value = self.hour_var.get()
        if value.isdigit():
            if int(value) > 23:
                # 如果当前输入不是空且为数字，则只保留本次输入的数字
                if event.char.isdigit():
                    self.hour_var.set(event.char)
                else:
                    self.hour_var.set("")
        else:
            self.hour_var.set("")

    def validate_minute(self, event):
        """验证分钟输入，超出 59 则仅保留最后输入的数字"""
        value = self.minute_var.get()
        if value.isdigit():
            if int(value) > 59:
                if event.char.isdigit():
                    self.minute_var.set(event.char)
                else:
                    self.minute_var.set("")
        else:
            self.minute_var.set("")

    def validate_second(self, event):
        """验证秒钟输入，超出 59 则仅保留最后输入的数字"""
        value = self.second_var.get()
        if value.isdigit():
            if int(value) > 59:
                if event.char.isdigit():
                    self.second_var.set(event.char)
                else:
                    self.second_var.set("")
        else:
            self.second_var.set("")


class FlowTrackApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # 如果存在图标文件，则设置图标
        icon_path = get_resource_path("assets/flow-track.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        # 检查语言文件是否存在
        lang_path = get_resource_path(LANGUAGE_FILE)
        if not os.path.exists(lang_path):
            messagebox.showerror("Error", f"The required language file was not found:\n{lang_path}")
            self.destroy()
            return # 提前退出，防止后续代码因 lang_config 未初始化而出错
        else:
            self.lang_config = configparser.ConfigParser()
            self.lang_config.read(lang_path, encoding="utf-8")
        # 默认语言：中文，如果 config.ini 中有保存则读取
        self.selected_language = tk.StringVar()
        self.selected_language.set("中文")
        self.timer_canvas_height = 200 # 为定时器区域Canvas设置默认高度
        self.copy_range_var = tk.StringVar(value="7")

        # Autoclose settings
        self.auto_close_enabled = False
        self.auto_close_delay_seconds = 10

        self.load_app_config()

        # 新增拖动状态变量
        self.is_resizing_canvas = False
        self.canvas_resize_start_y = 0
        self.initial_canvas_height_on_drag = 0 # 拖动开始时的 canvas 高度

        # 设置窗口位置
        self.set_window_position()

        # 用于存放定时器行
        self.timer_rows = []
        # 用于保存正在运行的定时器线程取消事件
        self.timer_threads = []

        self.build_ui()
        self.update_coordinate()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_app_config(self):
        """从 config.ini 中读取上次保存的语言和定时器数据"""
        self.app_config = configparser.ConfigParser()
        self.window_x = None
        self.window_y = None
        self.window_width = 600  # Default width
        self.window_height = 500  # Default height

        if os.path.exists(CONFIG_FILE):
            self.app_config.read(CONFIG_FILE, encoding="utf-8")
            lang = self.app_config.get("General", "language", fallback="中文")
            self.selected_language.set(lang)  # Set language before UI is built

            try:
                self.window_x = self.app_config.getint("General", "window_x")
                self.window_y = self.app_config.getint("General", "window_y")
                self.window_width = self.app_config.getint("General", "window_width", fallback=600)
                self.window_height = self.app_config.getint("General", "window_height", fallback=500)
                self.timer_canvas_height = self.app_config.getint("General", "timer_canvas_height", fallback=self.timer_canvas_height)
                copy_range_value = self.app_config.get("General", "copy_range", fallback="7")
                if copy_range_value.isdigit() and 1 <= int(copy_range_value) <= 10:
                    self.copy_range_var.set(copy_range_value)
                else:
                    self.copy_range_var.set("7") # 如果无效则设为默认值
                
                # Load AutoClose settings from [General]
                self.auto_close_enabled = self.app_config.getboolean('General', 'auto_close_enabled', fallback=False)
                self.auto_close_delay_seconds = self.app_config.getint('General', 'auto_close_delay_seconds', fallback=10)

            except (configparser.NoOptionError, ValueError):
                self.window_x = None # Ensure they are None if not found or invalid
                self.window_y = None
                # Keep default width/height if specific values are problematic
                self.copy_range_var.set("7")
        else:
            # If config file doesn't exist, set defaults for General section
            self.app_config["General"] = {
                "language": "中文",  # Default language
                "window_width": str(self.window_width),
                "window_height": str(self.window_height),
                "timer_canvas_height": str(self.timer_canvas_height),  # 保存默认高度
                "copy_range": self.copy_range_var.get()
            }
            # window_x and window_y remain None, so window will be centered

    def set_window_position(self):
        """设置窗口位置和大小"""
        self.update_idletasks()  # 更新控件信息
        if self.window_x is not None and self.window_y is not None:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # 确保窗口坐标在屏幕内
            if self.window_x < 0:
                self.window_x = 0
            if self.window_y < 0:
                self.window_y = 0
            if self.window_x > screen_width - self.window_width:
                self.window_x = screen_width - self.window_width
            if self.window_y > screen_height - self.window_height:
                self.window_y = screen_height - self.window_height

            self.geometry(f"{self.window_width}x{self.window_height}+{self.window_x}+{self.window_y}")
        else:
            # 默认600x500，并居中显示
            self.geometry(f"{self.window_width}x{self.window_height}")
            self.center_window()

    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def get_lang_texts(self):
        """根据当前选择的语言，返回对应的字典"""
        lang = self.selected_language.get()
        return dict(self.lang_config[lang])

    def move_timer_row_up(self, timer_row_object):
        """将指定的定时器行向上移动一个位置"""
        try:
            current_index = self.timer_rows.index(timer_row_object)
            timer_no_display = current_index + 1 # 定时器编号从1开始显示
            if current_index > 0:
                # 交换列表中的元素
                self.timer_rows[current_index], self.timer_rows[current_index - 1] = \
                    self.timer_rows[current_index - 1], self.timer_rows[current_index]
                self.rebuild_timer_rows_ui()
                self.log(self.get_log_message("log_timer_row_moved_up", timer_no=timer_no_display, default=f"Timer {timer_no_display} moved up."))
            else:
                self.log(self.get_log_message("log_timer_row_already_top", timer_no=timer_no_display, default=f"Timer {timer_no_display} is already at the top."))
        except ValueError:
            self.log("Error: Timer row not found for moving up.")
        except Exception as e:
            self.log(f"Error moving timer row up: {str(e)}")

    def move_timer_row_down(self, timer_row_object):
        """将指定的定时器行向下移动一个位置"""
        try:
            current_index = self.timer_rows.index(timer_row_object)
            timer_no_display = current_index + 1 # 定时器编号从1开始显示
            if current_index < len(self.timer_rows) - 1:
                # 交换列表中的元素
                self.timer_rows[current_index], self.timer_rows[current_index + 1] = \
                    self.timer_rows[current_index + 1], self.timer_rows[current_index]
                self.rebuild_timer_rows_ui()
                self.log(self.get_log_message("log_timer_row_moved_down", timer_no=timer_no_display, default=f"Timer {timer_no_display} moved down."))
            else:
                self.log(self.get_log_message("log_timer_row_already_bottom", timer_no=timer_no_display, default=f"Timer {timer_no_display} is already at the bottom."))
        except ValueError:
            self.log("Error: Timer row not found for moving down.")
        except Exception as e:
            self.log(f"Error moving timer row down: {str(e)}")

    def copy_time_settings(self, current_log_timer_row_list_index):
        """将当前行的时分秒、点击次数和间隔秒数设置复制到后面7个定时器行"""
        try:
            # 获取当前行在timer_rows中的索引
            current_idx = current_log_timer_row_list_index
            if current_idx < 0 or current_idx >= len(self.timer_rows):
                return

            # 获取当前行的时分秒、点击次数和间隔秒数设置
            current_row = self.timer_rows[current_idx]
            hour_value = current_row.hour_var.get()
            minute_value = current_row.minute_var.get()
            second_value = current_row.second_var.get()
            # 获取 "显示桌面" 复选框的状态
            is_show_desktop_mode = current_row.show_desktop_var.get()
            if not is_show_desktop_mode:
                # 仅在非 "显示桌面" 模式下获取点击次数和间隔
                clicks_value = current_row.entry_clicks.get()  # 获取点击次数
                interval_value = current_row.entry_interval.get()  # 获取间隔秒数

            # 从 copy_range_var 获取复制范围
            try:
                copy_count = int(self.copy_range_var.get())
            except ValueError:
                copy_count = 7 # 如果获取失败，则默认为7
                self.log(self.get_log_message("error_invalid_copy_range", default=f"Invalid copy range value '{self.copy_range_var.get()}', defaulting to 7."))

            # 复制到后面的定时器
            for i in range(1, copy_count + 1):
                target_idx = current_idx + i
                if target_idx < len(self.timer_rows):
                    target_row = self.timer_rows[target_idx]
                    # 复制 时、分
                    target_row.hour_var.set(hour_value)
                    target_row.minute_var.set(minute_value)
                    # 计算并设置新的秒钟值
                    # 目标行的秒钟 = 源秒钟 + 偏移量 (i)
                    new_second_value = (int(second_value) + i) % 60  # 秒数递增
                    target_row.second_var.set(f"{new_second_value:02d}")  # 0-59循环
                    if not is_show_desktop_mode:
                        target_row.entry_clicks.delete(0, tk.END)  # 清空目标行点击次数
                        target_row.entry_clicks.insert(0, clicks_value)  # 设置点击次数
                        target_row.entry_interval.delete(0, tk.END)  # 清空目标行间隔秒数
                        target_row.entry_interval.insert(0, interval_value)  # 设置间隔秒数

            self.log(self.get_log_message("log_settings_copied_range", from_row=current_idx + 1, count=copy_count, default=f"Settings from timer {current_idx + 1} copied to next {copy_count} timers."))
        except Exception as e:
            self.log(self.get_log_message("error_copy_settings", error=str(e)))

    def build_ui(self):
        lang_texts = self.get_lang_texts()

        self.title(lang_texts.get("app_title", "Mouse Clicker"))

        # 定义 ttk 样式
        style = ttk.Style()
        style.configure("Blue.TLabel", foreground="blue", font=('TkDefaultFont', 16))
        style.configure("Red.TLabel", foreground="red", font=('TkDefaultFont', 12))
        style.configure("GreenLarge.TLabel", foreground="green", font=('TkDefaultFont', 18))

        # ----------------- 第1部分：语言选项 -----------------
        frm_option = ttk.Frame(self)
        frm_option.pack(padx=5, pady=5, anchor="w")
        self.lbl_option = ttk.Label(frm_option, text=lang_texts.get("label_option_language", "Language"), style="Blue.TLabel")
        self.lbl_option.pack(side="left", anchor="n")
        option_menu = ttk.OptionMenu(frm_option, self.selected_language, self.selected_language.get(), "中文", "English", command=lambda _: self.update_language())
        option_menu.pack(side="left", padx=5)
        # 读取设置
        self.btn_load_config = ttk.Button(frm_option, text=lang_texts.get("button_load_config", "Load Config"), command=self.load_config_from_file_dialog, width=7)
        self.btn_load_config.pack(side="left", padx=20)
        # 复制范围 (Copy Range)
        self.lbl_copy_range_ui = ttk.Label(frm_option, text=lang_texts.get("label_copy_range", "Copy Range"))
        self.lbl_copy_range_ui.pack(side="left", padx=(20, 5), anchor="n")
        self.lbl_copy_range_ui.config(style="GreenLarge.TLabel")
        copy_range_values = [str(i) for i in range(1, 11)]  # 1 到 10
        self.cmb_copy_range = ttk.Combobox(frm_option, textvariable=self.copy_range_var, values=copy_range_values, width=4, state="readonly")
        self.cmb_copy_range.pack(side="left", padx=5)
        self.cmb_copy_range.bind("<<ComboboxSelected>>", self.on_copy_range_changed)
        # 坐标获取
        self.lbl_coord = ttk.Label(frm_option, text=lang_texts.get("label_coordinate", "Current Pos:") + " (0, 0)", style="Red.TLabel")
        self.lbl_coord.pack(side="left", padx=20)
        # 开始/结束
        self.btn_start = ttk.Button(frm_option, text=lang_texts.get("button_start", "Start"), command=self.start_timers)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(frm_option, text=lang_texts.get("button_stop", "Stop"), command=self.stop_timers, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        # ----------------- 第2部分：定时器 -----------------
        # 创建一个外层 LabelFrame，用于容纳表头和可滚动区域
        self.frm_timer_outer = ttk.LabelFrame(self, text=lang_texts.get("timer", "Timer"))
        self.frm_timer_outer.pack(padx=5, pady=5, fill="both", expand=True)

        # 创建表头框架 (将放置在 Canvas 上方)
        self.frm_timer_headers = ttk.Frame(self.frm_timer_outer)
        self.frm_timer_headers.pack(fill="x", pady=(0, 2))

        headers = ["", "", "", "", "",  # 删(0), 增(1), 上(2), 下(3), 复选框(4)
                   lang_texts.get("x", "X"),  # X (5)
                   lang_texts.get("y", "Y"),  # Y (6)
                   lang_texts.get("time", "Time"),  # 时间 (7)
                   "",  # Copy按键 (8)
                   "",  # 为 "显示桌面" Checkbutton 预留的空表头 (9)
                   lang_texts.get("clicks", "Clicks"),  # 点击次数 (10)
                   lang_texts.get("interval", "Interval"),  # 间隔 (11)
                   lang_texts.get("paste_text", "Paste Text")]  # 粘贴文本 (12)
        self.header_labels = [] # 用于在语言切换时更新表头文本

        # 定义与TimerRow中控件大致匹配的表头标签字符宽度
        header_char_widths = [
            3,  # 删除按钮
            4,  # 插入按钮
            3,  # 往上按钮
            3,  # 往下按钮
            6,  # Enabled Checkbutton
            7,  # X 输入框
            7,  # Y 输入框
            12, # 时间标签
            5,  # Copy按钮
            10, # 显示桌面
            6,  # 点击次数输入框
            8,  # 间隔秒数输入框
            0   # 粘贴文本 (使用 0， 此列会自动调整宽度)
        ]

        # 定义与TimerRow中控件对应的padx值
        # TimerRow中：
        # 按钮类(del,add,up,down,copy): padx=1
        # Checkbutton(enabled): padx=1
        # Entry(x,y,clicks,interval): padx=2
        # time_frame: padx=2
        # show_desktop_frame: padx=(2,2) -> 我们取2
        # paste_text_frame: padx=2
        header_padx_values = [
            1, 1, 1, 1, 1,  # 删, 增, 上, 下, 复选框
            2,              # X
            2,              # Y
            2,              # 时间
            1,              # Copy
            2,              # 显示桌面 (对应show_desktop_frame的padx)
            2,              # 点击次数
            2,              # 间隔
            2               # 粘贴文本
        ]

        for idx, h_text in enumerate(headers):
            current_padx = header_padx_values[idx]
            char_width_for_label = header_char_widths[idx]
            if char_width_for_label > 0:
                # 为需要固定宽度的表头标签设置 width
                lbl = ttk.Label(self.frm_timer_headers, text=h_text, width=char_width_for_label, anchor="center")
            else:
                # 对于其他表头（如长文本或扩展列的表头），不设置固定width，让其自适应
                lbl = ttk.Label(self.frm_timer_headers, text=h_text, anchor="center")
            current_sticky = "w"
            if idx == len(headers) - 1: # 最后一列（粘贴文本）
                current_sticky = "ew"
            lbl.grid(row=0, column=idx, padx=current_padx, pady=2, sticky=current_sticky)
            self.header_labels.append(lbl)
            # 配置 frm_timer_headers 的列权重
            if idx == len(headers) - 1:  # 最后一列（粘贴文本）
                self.frm_timer_headers.columnconfigure(idx, weight=1)
            else:
                self.frm_timer_headers.columnconfigure(idx, weight=0)

        # 创建一个容器Frame来容纳Canvas和Scrollbar，以便更好地控制它们的布局
        self.canvas_timers_container = ttk.Frame(self.frm_timer_outer)
        self.canvas_timers_container.pack(fill="both", expand=True)

        # 创建Canvas用于显示可滚动的定时器行
        self.canvas_timers = tk.Canvas(self.canvas_timers_container,
                                       height=self.timer_canvas_height,
                                       borderwidth=0,
                                       highlightthickness=0)  # 移除边框和高亮

        # 创建垂直滚动条
        self.scrollbar_timers = ttk.Scrollbar(self.canvas_timers_container, orient="vertical", command=self.canvas_timers.yview)
        self.canvas_timers.configure(yscrollcommand=self.scrollbar_timers.set)

        # 布局Scrollbar和Canvas
        self.scrollbar_timers.pack(side="right", fill="y")
        self.canvas_timers.pack(side="left", fill="both", expand=True)

        # 创建在Canvas内部滚动的Frame (所有TimerRow将放在这里)
        self.scrollable_frame_timers = ttk.Frame(self.canvas_timers)

        # 将scrollable_frame_timers添加到canvas窗口中
        self.canvas_timers.create_window((0, 0), window=self.scrollable_frame_timers, anchor="nw", tags="scrollable_frame")

        # 绑定事件，以便在scrollable_frame_timers大小变化时更新canvas的滚动区域
        self.scrollable_frame_timers.bind("<Configure>", self.on_scrollable_frame_configure)
        # 绑定事件，以便在canvas大小变化时调整内部frame的宽度
        self.canvas_timers.bind("<Configure>", self.on_canvas_configure)

        # 为Canvas和其内部的可滚动框架绑定鼠标滚轮事件
        # 1. 绑定到最外层的定时器框架
        self.frm_timer_outer.bind("<MouseWheel>", self.on_mousewheel)
        # 2. 绑定到画布本身
        self.canvas_timers.bind("<MouseWheel>", self.on_mousewheel)
        # 3. 绑定到画布内部容纳所有TimerRow的框架
        self.scrollable_frame_timers.bind("<MouseWheel>", self.on_mousewheel)
        # 4. 表头框架
        self.frm_timer_headers.bind("<MouseWheel>", self.on_mousewheel)
        # 5. 画布的直接容器
        self.canvas_timers_container.bind("<MouseWheel>", self.on_mousewheel)
        # 6. 底部拖动手柄 (如果存在)
        if hasattr(self, 'timer_resize_handle'):
            self.timer_resize_handle.bind("<MouseWheel>", self.on_mousewheel)

        # !! 关键: 将 self.frm_timer 指向新的 scrollable_frame_timers !!
        # TimerRow 类及其相关方法 (如 add_log_timer_row_at_index) 依赖 self.frm_timer 作为父容器。
        self.frm_timer = self.scrollable_frame_timers

        # 配置 scrollable_frame_timers 的列以匹配 frm_timer_headers 的列伸展行为
        # headers 列表在之前创建表头时已定义
        num_header_cols = len(headers)
        for i in range(num_header_cols):
            if i == num_header_cols - 1:  # 最后一列（粘贴文本）
                self.scrollable_frame_timers.columnconfigure(i, weight=1)
            else:
                self.scrollable_frame_timers.columnconfigure(i, weight=0)

        # 创建定时器区域高度调整手柄
        self.timer_resize_handle = ttk.Frame(self.frm_timer_outer, height=7, style="Resize.TFrame") # 高度可调整
        self.timer_resize_handle.pack(fill="x", side="bottom", pady=(2,0)) # pack在frm_timer_outer的底部
        self.timer_resize_handle.bind("<ButtonPress-1>", self.on_timer_resize_press)
        self.timer_resize_handle.bind("<B1-Motion>", self.on_timer_resize_motion)
        self.timer_resize_handle.bind("<ButtonRelease-1>", self.on_timer_resize_release)
        self.timer_resize_handle.bind("<Enter>", self.on_timer_resize_enter)
        self.timer_resize_handle.bind("<Leave>", self.on_timer_resize_leave)

        # 加载 config.ini 中保存的定时器数据
        timer_data_list = []
        for section in self.app_config.sections():
            if section.startswith("Timer_"):
                timer_data = {
                    "x": self.app_config.get(section, "x", fallback=""),
                    "y": self.app_config.get(section, "y", fallback=""),
                    "time": self.app_config.get(section, "time", fallback=""),
                    "show_desktop": self.app_config.get(section, "show_desktop", fallback="0"),
                    "clicks": self.app_config.get(section, "clicks", fallback=""),
                    "interval": self.app_config.get(section, "interval", fallback=""),
                    "enabled": self.app_config.get(section, "enabled", fallback="0") == "1",
                    "paste_text": self.app_config.get(section, "paste_text", fallback="")
                }
                timer_data_list.append(timer_data)

        if not timer_data_list and self.app_config.has_section("Timers"):
            for key in sorted(self.app_config["Timers"].keys()):
                try:
                    parts = self.app_config["Timers"][key].split(',', 7) # 最多7个字段，允许show_desktop
                    if len(parts) >= 6:
                        # x, y, time, clicks, interval, enabled
                        timer_data = {
                            "x": parts[0],
                            "y": parts[1],
                            "time": parts[2],
                            "clicks": parts[3],
                            "interval": parts[4],
                            "enabled": parts[5] == "1"
                        }
                        timer_data["paste_text"] = parts[6] if len(parts) >= 7 else ""
                        timer_data["show_desktop"] = parts[7] if len(parts) >= 8 else "0"  # 旧格式兼容
                        timer_data_list.append(timer_data)
                except:
                    continue

        if not timer_data_list:  # 如无则创建5行空白定时器
            for _ in range(5):
                timer_data_list.append(None)

        for data in timer_data_list:
            self.add_log_timer_row_at_end(data)

        self.rebuild_timer_rows_ui()
        self.rebuild_timer_rows_ui()
        # 延迟一点执行，确保所有组件都已创建并计算了大小
        self.after(100, lambda: self.on_scrollable_frame_configure(None))

        # ----------------- 第3部分：信息框 -----------------
        self.frm_log = ttk.LabelFrame(self, text=lang_texts.get("log", "Log"))
        self.frm_log.pack(padx=5, pady=5, fill="both", expand=True)
        self.txt_log = scrolledtext.ScrolledText(self.frm_log, height=5, state="disabled")
        # self.txt_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_log.pack(fill="x", expand=False, padx=5, pady=5)

    def on_mousewheel(self, event):
        """处理鼠标滚轮事件以滚动定时器列表的Canvas。"""
        if hasattr(self, 'canvas_timers') and self.canvas_timers.winfo_exists():
            # 在Windows上，event.delta 通常是120的倍数 (向上滚动为正，向下为负)
            # 我们希望向上滚动时，canvas向上移动 (yview_scroll的单位为负数)
            # 向下滚动时，canvas向下移动 (yview_scroll的单位为正数)
            if event.delta != 0: # 仅当delta非零时处理
                # 将delta值转换为滚动单位。例如，每次滚动3个单位。
                # event.delta / 120 大约是一个“标准”滚动格。乘以3表示一次滚动3行。
                # 根据需要调整此处的 "40" (120/3=40) 来改变滚动的灵敏度。
                # 更小的除数意味着更快的滚动 (一次滚动更多行)。
                scroll_units = -1 * (event.delta // 40) # 整数除法

                if scroll_units != 0: # 确保实际有滚动量
                    self.canvas_timers.yview_scroll(scroll_units, "units")
            return "break"  # 阻止事件继续传播到父控件
        return "" # 如果canvas不存在，则不执行任何操作

    def on_timer_resize_press(self, event):
        self.is_resizing_canvas = True
        self.canvas_resize_start_y = event.y_root  # 使用屏幕坐标
        if hasattr(self, 'canvas_timers') and self.canvas_timers.winfo_exists() and self.canvas_timers.winfo_height() > 1:
            self.initial_canvas_height_on_drag = self.canvas_timers.winfo_height()
        else:
            self.initial_canvas_height_on_drag = self.timer_canvas_height
        self.timer_resize_handle.config(cursor="sb_v_double_arrow")

    def on_timer_resize_motion(self, event):
        if not self.is_resizing_canvas:
            return

        delta_y = event.y_root - self.canvas_resize_start_y
        new_height = self.initial_canvas_height_on_drag + delta_y

        min_h = 50  # 最小高度
        # === 最大高度 (max_h) 计算逻辑修改区域 ===
        # 基于窗口当前高度，减去其他主要UI元素所占高度，来估算canvas_timers可以使用的最大高度
        try:
            # 获取其他主要UI元素的实际或预估高度
            # 使用winfo_reqheight()获取其请求的最小高度，确保这些部分可见
            option_h = self.frm_option.winfo_reqheight() if hasattr(self, 'frm_option') and self.frm_option.winfo_exists() else 20
            control_h = self.frm_control.winfo_reqheight() if hasattr(self, 'frm_control') and self.frm_control.winfo_exists() else 30

            # 日志区域 frm_log 也是 expand=True，估算其最小保留高度
            # (例如ScrolledText默认5行的高度，加上LabelFrame的边框和标题)
            log_area_min_h = 100 # 根据实际情况调整此估算值
            if hasattr(self, 'txt_log') and self.txt_log.winfo_exists():
                # 一个更细致的估算：ScrolledText请求高度 + frm_log的额外部分(如Label)
                # 这里简化为一个固定值，或者可以基于ScrolledText的height属性计算
                pass # 使用下面的固定值

            header_h = self.frm_timer_headers.winfo_reqheight() if hasattr(self, 'frm_timer_headers') and self.frm_timer_headers.winfo_exists() else 20
            resize_handle_h = self.timer_resize_handle.winfo_reqheight() if hasattr(self, 'timer_resize_handle') and self.timer_resize_handle.winfo_exists() else 7

            # 各个部分之间的总间距和窗口的内边距估算
            total_paddings_estimate = 50 # 估算值，根据实际布局调整

            # 计算留给 canvas_timers 的最大可用高度
            available_height_for_canvas = self.winfo_height() - (option_h + control_h + log_area_min_h + header_h + resize_handle_h + total_paddings_estimate)

            max_h = max(min_h + 20, available_height_for_canvas) # 确保max_h至少比min_h大一点
        except tk.TclError:
            # 如果在获取winfo_* 时出错 (例如窗口尚未完全初始化)
            max_h = self.winfo_height() * 0.6 # 使用一个相对保守的比例作为备用
        # === 最大高度计算逻辑修改结束 ===

        # 将计算出的新高度限制在最小和最大高度之间
        new_height_clamped = max(min_h, min(new_height, max_h))

        if hasattr(self, 'canvas_timers') and self.canvas_timers.winfo_exists():
            # 仅在高度实际变化超过1个像素时才更新，避免不必要的重绘
            if abs(self.canvas_timers.winfo_height() - new_height_clamped) > 1:
                self.canvas_timers.config(height=new_height_clamped)
                self.timer_canvas_height = new_height_clamped # 保存当前高度，用于下次启动或保存配置

                # 强制Tkinter更新挂起的几何形状更改
                self.update_idletasks()
                # Canvas高度改变后，可能需要更新其内部可滚动框架的配置
                self.on_scrollable_frame_configure(None)

    def on_timer_resize_release(self, event):
        if self.is_resizing_canvas:
            self.is_resizing_canvas = False
            if hasattr(self, 'canvas_timers') and self.canvas_timers.winfo_exists():
                self.timer_canvas_height = self.canvas_timers.winfo_height()  # 确保保存的是最终高度
            self.timer_resize_handle.config(cursor="")

    def on_timer_resize_enter(self, event):
        self.timer_resize_handle.config(cursor="sb_v_double_arrow")

    def on_timer_resize_leave(self, event):
        if not self.is_resizing_canvas:  # 只有在未拖动时才恢复光标
            self.timer_resize_handle.config(cursor="")

    def on_scrollable_frame_configure(self, event):
        """当内部可滚动框架的大小改变时，更新Canvas的滚动区域。"""
        self.canvas_timers.configure(scrollregion=self.canvas_timers.bbox("all"))

    def on_canvas_configure(self, event):
        """当Canvas本身大小改变时（例如窗口缩放），调整内部可滚动框架的宽度以匹配Canvas宽度。"""
        canvas_width = event.width
        self.canvas_timers.itemconfig("scrollable_frame", width=canvas_width)

    def update_language(self):
        lang_texts = self.get_lang_texts()

        # 更新窗口标题
        self.title(lang_texts.get("app_title", "Mouse Clicker"))

        # 更新语言选项标签
        self.lbl_option.config(text=lang_texts.get("label_option_language", "Language"))

        # 更新读取配置按钮
        self.btn_load_config.config(text=lang_texts.get("button_load_config", "Load Config"))

        # 清除旧的表头标签
        for lbl in self.header_labels:
            lbl.destroy()
        self.header_labels.clear()

        headers = ["", "", "", "", "",  # 删(0), 增(1), 上(2), 下(3), 复选框(4)
                   lang_texts.get("x", "X"),  # X (5)
                   lang_texts.get("y", "Y"),  # Y (6)
                   lang_texts.get("time", "Time"),  # 时间 (7)
                   "",  # Copy按键 (8)
                   "",  # 为 "显示桌面" Checkbutton 预留的空表头 (9)
                   lang_texts.get("clicks", "Clicks"),  # 点击次数 (10)
                   lang_texts.get("interval", "Interval"),  # 间隔 (11)
                   lang_texts.get("paste_text", "Paste Text")]  # 粘贴文本 (12)

        # 定义与TimerRow中控件大致匹配的表头标签字符宽度 (与 build_ui 中一致)
        header_char_widths = [
            3,  # 删除按钮
            4,  # 插入按钮
            3,  # 往上按钮
            3,  # 往下按钮
            6,  # Enabled Checkbutton
            7,  # X 输入框
            7,  # Y 输入框
            12, # 时间标签
            5,  # Copy按钮
            10, # 显示桌面
            6,  # 点击次数输入框
            8,  # 间隔秒数输入框
            0   # 粘贴文本 (使用 0， 此列会自动调整宽度)
        ]
        # 使用与 build_ui 中相同的 padx 逻辑
        header_padx_values = [
            1, 1, 1, 1, 1,  # 删, 增, 上, 下, 复选框
            2,              # X
            2,              # Y
            2,              # 时间
            1,              # Copy
            2,              # 显示桌面
            2,              # 点击次数
            2,              # 间隔
            2               # 粘贴文本
        ]

        for idx, h_text in enumerate(headers):
            current_padx = header_padx_values[idx]
            char_width_for_label = header_char_widths[idx]
            if char_width_for_label > 0:
                lbl = ttk.Label(self.frm_timer_headers, text=h_text, width=char_width_for_label, anchor="center")
            else:
                lbl = ttk.Label(self.frm_timer_headers, text=h_text, anchor="center")
            current_sticky = "w"
            if idx == len(headers) - 1:
                current_sticky = "ew"

            lbl.grid(row=0, column=idx, padx=current_padx, pady=2, sticky=current_sticky)
            self.header_labels.append(lbl)
            # 列权重配置通常在 build_ui 中已设置且固定，此处主要重建标签
            # 为确保一致性，可以再次配置，但如果frm_timer_headers未销毁重建，则可能非必需
            if idx == len(headers) - 1:
                self.frm_timer_headers.columnconfigure(idx, weight=1)
            else:
                self.frm_timer_headers.columnconfigure(idx, weight=0)


        self.frm_timer_outer.config(text=lang_texts.get("timer", "Timer"))  # 更新外层LabelFrame的标题
        self.btn_start.config(text=lang_texts.get("button_start", "Start"))
        self.btn_stop.config(text=lang_texts.get("button_stop", "Stop"))
        self.lbl_coord.config(text=lang_texts.get("label_coordinate", "Current Pos:") + " (0, 0)")
        self.lbl_copy_range_ui.config(text=lang_texts.get("label_copy_range", "Copy Range"), style="GreenLarge.TLabel")

        # 更新日志区域标题
        self.frm_log.config(text=lang_texts.get("log", "Log"))

        # 更新所有TimerRow中的复制,删除和插入,往上,往下按钮文本, 及Checkbutton文本
        for row_obj in self.timer_rows:
            row_obj.btn_delete.config(text=lang_texts.get("button_delete_timer", "x"))
            row_obj.btn_add.config(text=lang_texts.get("button_insert_timer", "add"))
            row_obj.btn_up.config(text=lang_texts.get("button_up_timer", "up"))
            row_obj.btn_down.config(text=lang_texts.get("button_down_timer", "down"))
            row_obj.btn_copy.config(text=lang_texts.get("button_copy", "Copy"))
            row_obj.lbl_show_desktop.config(text=lang_texts.get("radio_show_desktop", "Show Desktop"))

        # 保存选择
        self.app_config["General"]["language"] = self.selected_language.get()

    def get_header_count(self):
        # 辅助方法获取表头数量，用于 columnspan
        lang_texts = self.get_lang_texts()
        headers = ["", "", "", "", "",  # 删(0), 增(1), 上(2), 下(3), 复选框(4)
                   lang_texts.get("x", "X"),     # X (5)
                   lang_texts.get("y", "Y"),     # Y (6)
                   lang_texts.get("time", "Time"), # 时间 (7)
                   "",  # Copy按键 (8)
                   "",  # "显示桌面" (9)
                   lang_texts.get("clicks", "Clicks"),      # 点击次数 (10)
                   lang_texts.get("interval", "Interval"), # 间隔 (11)
                   lang_texts.get("paste_text", "Paste Text")] # 粘贴文本 (12)
        return len(headers)

    def rebuild_timer_rows_ui(self):
        """根据 self.timer_rows 列表，重新排列和更新界面上的所有定时器行。"""
        lang_texts = self.get_lang_texts() # 获取当前语言文本

        # 确保所有 TimerRow 对象的旧 widgets 都被 ungrid
        # 这很重要，因为行的顺序可能改变，或者有些行可能被删除了。
        # 如果一个 TimerRow 对象的控件已经被其 destroy_widgets() 方法销毁了，
        # 尝试 grid_forget() 会抛出 TclError，所以需要捕获它。
        for log_timer_row_obj in self.timer_rows:
            try:
                # 尝试 ungrid 所有主要控件，如果它们还存在的话
                if hasattr(log_timer_row_obj, 'btn_delete') and log_timer_row_obj.btn_delete.winfo_exists():
                    log_timer_row_obj.btn_delete.grid_forget()
                if hasattr(log_timer_row_obj, 'btn_add') and log_timer_row_obj.btn_add.winfo_exists():
                    log_timer_row_obj.btn_add.grid_forget()
                if hasattr(log_timer_row_obj, 'btn_up') and log_timer_row_obj.btn_up.winfo_exists():
                    log_timer_row_obj.btn_up.grid_forget()
                if hasattr(log_timer_row_obj, 'btn_down') and log_timer_row_obj.btn_down.winfo_exists():
                    log_timer_row_obj.btn_down.grid_forget()
                if hasattr(log_timer_row_obj, 'chk') and log_timer_row_obj.chk.winfo_exists():
                    log_timer_row_obj.chk.grid_forget()
                if hasattr(log_timer_row_obj, 'entry_x') and log_timer_row_obj.entry_x.winfo_exists():
                    log_timer_row_obj.entry_x.grid_forget()
                if hasattr(log_timer_row_obj, 'entry_y') and log_timer_row_obj.entry_y.winfo_exists():
                    log_timer_row_obj.entry_y.grid_forget()
                if hasattr(log_timer_row_obj, 'time_frame') and log_timer_row_obj.time_frame.winfo_exists():
                    log_timer_row_obj.time_frame.grid_forget()
                if hasattr(log_timer_row_obj, 'btn_copy') and log_timer_row_obj.btn_copy.winfo_exists():
                    log_timer_row_obj.btn_copy.grid_forget()
                if hasattr(log_timer_row_obj, 'show_desktop_frame') and log_timer_row_obj.show_desktop_frame.winfo_exists():
                    log_timer_row_obj.show_desktop_frame.grid_forget()
                if hasattr(log_timer_row_obj, 'entry_clicks') and log_timer_row_obj.entry_clicks.winfo_exists():
                    log_timer_row_obj.entry_clicks.grid_forget()
                if hasattr(log_timer_row_obj, 'entry_interval') and log_timer_row_obj.entry_interval.winfo_exists():
                    log_timer_row_obj.entry_interval.grid_forget()
                if hasattr(log_timer_row_obj, 'paste_text_frame') and log_timer_row_obj.paste_text_frame.winfo_exists():
                    log_timer_row_obj.paste_text_frame.grid_forget()
            except tk.TclError: # Widget可能已经被销毁
                pass

        # 遍历 self.timer_rows 列表，为每个 TimerRow 对象更新其在界面上的位置
        for i, log_timer_row_obj in enumerate(self.timer_rows):
            # 更新 TimerRow 实例的 grid_row (界面行号) 和 log_timer_row_index_in_list (列表索引)
            new_grid_row = i + 1  # grid 行号从1开始 (第0行是表头)
            log_timer_row_obj.grid_row = new_grid_row
            log_timer_row_obj.log_timer_row_index_in_list = i

            # 确保 TimerRow 对象的父容器是 self.frm_timer
            # (通常在创建时就已设置，但以防万一)
            log_timer_row_obj.parent = self.scrollable_frame_timers

            # 手动重新 grid 该 TimerRow 对象的所有内部控件到新的 grid_row
            # 并确保按钮文本等是当前语言
            col_offset = 0
            if hasattr(log_timer_row_obj, 'btn_delete'):
                log_timer_row_obj.btn_delete.config(text=lang_texts.get("button_delete_timer", "x"))
                log_timer_row_obj.btn_delete.grid(row=new_grid_row, column=col_offset, padx=1, pady=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'btn_add'):
                log_timer_row_obj.btn_add.config(text=lang_texts.get("button_insert_timer", "add"))
                log_timer_row_obj.btn_add.grid(row=new_grid_row, column=col_offset, padx=1, pady=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'btn_up'):
                log_timer_row_obj.btn_up.config(text=lang_texts.get("button_up_timer", "up"))
                log_timer_row_obj.btn_up.grid(row=new_grid_row, column=col_offset, padx=1, pady=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'btn_down'):
                log_timer_row_obj.btn_down.config(text=lang_texts.get("button_down_timer", "down"))
                log_timer_row_obj.btn_down.grid(row=new_grid_row, column=col_offset, padx=1, pady=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'chk'):
                log_timer_row_obj.chk.grid(row=new_grid_row, column=col_offset, padx=1, pady=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'entry_x'):
                log_timer_row_obj.entry_x.grid(row=new_grid_row, column=col_offset, padx=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'entry_y'):
                log_timer_row_obj.entry_y.grid(row=new_grid_row, column=col_offset, padx=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'time_frame'):
                log_timer_row_obj.time_frame.grid(row=new_grid_row, column=col_offset, padx=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'btn_copy'):
                log_timer_row_obj.btn_copy.config(text=lang_texts.get("button_copy", "Copy"))
                log_timer_row_obj.btn_copy.grid(row=new_grid_row, column=col_offset, padx=1, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'show_desktop_frame'):
                log_timer_row_obj.lbl_show_desktop.config(text=lang_texts.get("radio_show_desktop", "Show Desktop"))
                log_timer_row_obj.show_desktop_frame.grid(row=new_grid_row, column=col_offset, padx=(2,2), pady=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'entry_clicks'):
                log_timer_row_obj.entry_clicks.grid(row=new_grid_row, column=col_offset, padx=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'entry_interval'):
                log_timer_row_obj.entry_interval.grid(row=new_grid_row, column=col_offset, padx=2, sticky="w")
            col_offset += 1

            if hasattr(log_timer_row_obj, 'paste_text_frame'):
                log_timer_row_obj.paste_text_frame.grid(row=new_grid_row, column=col_offset, padx=2, pady=2, sticky="w")

        # 重建后更新滚动区域
        self.after(50, lambda: self.on_scrollable_frame_configure(None))

    def add_log_timer_row_at_end(self, data=None):
        """在列表末尾添加一个新的定时器行"""
        self.add_log_timer_row_at_index(len(self.timer_rows), data)

    def add_log_timer_row_at_index(self, index_in_list, data=None):
        """在指定索引处创建一个新的TimerRow对象并将其插入到self.timer_rows列表中。
        注意：此方法本身不更新UI的grid布局，调用者负责后续调用 rebuild_timer_rows_ui。
        """
        lang_texts = self.get_lang_texts()
        initial_grid_row_for_timer_row_init = index_in_list + 1 # grid行号从1开始 (第0行是表头)

        new_timer_row = TimerRow(
            self.scrollable_frame_timers,  # 父容器是可滚动框架
            initial_grid_row_for_timer_row_init,
            lang_texts,
            app=self,
            data=data,
            log_timer_row_index_in_list=index_in_list
        )
        self.timer_rows.insert(index_in_list, new_timer_row)

    def delete_log_timer_row_by_object(self, log_timer_row_object_to_delete):
        """通过 TimerRow 对象删除指定的定时器行"""
        if log_timer_row_object_to_delete in self.timer_rows:
            log_timer_row_object_to_delete.destroy_widgets()
            self.timer_rows.remove(log_timer_row_object_to_delete)
            self.rebuild_timer_rows_ui()
            self.log(self.get_log_message("log_timer_row_deleted", default="Timer row deleted."))
        else:
            self.log("Error: Attempted to delete a non-existent timer row object.")

    def insert_log_timer_row_after_object(self, preceding_log_timer_row_object):
        """在指定的 TimerRow 对象之后插入一个新的空白定时器行"""
        try:
            idx = self.timer_rows.index(preceding_log_timer_row_object)
            # add_log_timer_row_at_index 将创建行对象并将其插入到 self.timer_rows 列表中。
            # 它本身不再调用 rebuild_timer_rows_ui。
            self.add_log_timer_row_at_index(idx + 1, None) # data is None for a new blank row

            # 在逻辑插入完成后，显式调用UI重建。
            self.rebuild_timer_rows_ui()
            self.log(self.get_log_message("log_timer_row_inserted", default="Timer row inserted."))
        except ValueError:
            self.log("Error: Could not find the preceding timer row to insert after.")
        except Exception as e:
            self.log(f"Error inserting timer row: {str(e)}")

    def get_log_message(self, key, **kwargs):
        lang_texts = self.get_lang_texts()
        template = lang_texts.get(key, key)
        try:
            return template.format(**kwargs)
        except Exception as e:
            # 防止因格式化出错导致程序崩溃
            return template

    def start_timers(self):
        """点击开始按钮后的处理：禁用定时器区域，启动定时器线程"""
        self.log(self.get_log_message("log_timer_started"))
        for row in self.timer_rows:
            row.disable()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.timer_threads = []

        enabled_timers_info = []
        now = datetime.datetime.now()
        for idx, row in enumerate(self.timer_rows):
            values = row.get_values()
            if values["enabled"]:
                try:
                    t_str = values["time"]
                    scheduled_time = datetime.datetime.strptime(t_str, "%H%M%S")
                    scheduled_time = now.replace(hour=scheduled_time.hour, minute=scheduled_time.minute, second=scheduled_time.second, microsecond=0)
                    if scheduled_time < now:
                        self.log(self.get_log_message("log_timer_time_passed", timer_no=idx + 1))
                        continue
                    enabled_timers_info.append({"row": row, "scheduled_time": scheduled_time, "idx": idx})
                except Exception:
                    self.log(self.get_log_message("error_timer_format", timer_no=idx + 1, time_str=t_str))
                    continue
        
        if not enabled_timers_info:
            self.log(self.get_log_message("error_no_valid_timer"))
            self.stop_timers()
            return

        last_scheduled_time = max(info["scheduled_time"] for info in enabled_timers_info)

        for info in enabled_timers_info:
            row = info["row"]
            scheduled_time = info["scheduled_time"]
            idx = info["idx"]
            values = row.get_values()
            
            is_last_timer = (scheduled_time == last_scheduled_time)

            try:
                show_desktop_mode = values["show_desktop"]
                if not show_desktop_mode:
                    x = int(values["x"]) if values["x"] else 0
                    y = int(values["y"]) if values["y"] else 0
                    clicks = int(values["clicks"]) if values["clicks"] else 1
                    interval = float(values["interval"]) if values["interval"] else 1.0
                    paste_text = values["paste_text"]
                else:
                    x, y, clicks, interval, paste_text = 0, 0, 0, 0.0, ""

                timer_no = idx + 1
                cancel_event = threading.Event()
                args = (timer_no, x, y, scheduled_time, clicks, interval, paste_text, cancel_event, show_desktop_mode, is_last_timer)
                t = threading.Thread(target=self.run_timer, args=args)
                t.daemon = True
                t.start()
                self.timer_threads.append(cancel_event)
            except Exception as e:
                self.log(self.get_log_message("error_timer", timer_no=idx + 1, error=str(e)))

    def run_timer(self, timer_no, x, y, scheduled_time, clicks, interval, paste_text, cancel_event, show_desktop_mode, is_last_timer):
        """线程函数：等待到预定时间，然后执行操作"""
        mode_log_key = "log_timer_mode_desktop" if show_desktop_mode else "log_timer_mode_clickpaste"
        self.log(self.get_log_message(mode_log_key, timer_no=timer_no, default=f"Timer {timer_no} mode: {'Show Desktop' if show_desktop_mode else 'Click/Paste'}"))

        while not cancel_event.is_set():
            wait_seconds = (scheduled_time - datetime.datetime.now()).total_seconds()
            if wait_seconds <= 0:
                break
            
            self.log(self.get_log_message("log_timer_wait", timer_no=timer_no, seconds=int(wait_seconds)))
            
            sleep_duration = 0.5
            if wait_seconds > 15: sleep_duration = 10
            if wait_seconds > 60: sleep_duration = 30
            if wait_seconds > 660: sleep_duration = max(int(wait_seconds / 10) - 60, 600)
            
            cancel_event.wait(min(sleep_duration, wait_seconds))

        if cancel_event.is_set():
            self.log(self.get_log_message("log_timer_cancel", timer_no=timer_no))
            return

        # --- 执行操作 ---
        if show_desktop_mode:
            self.log(self.get_log_message("log_timer_show_desktop", timer_no=timer_no))
            try:
                win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
                win32api.keybd_event(ord('D'), 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(ord('D'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)
                self.log(self.get_log_message("log_timer_show_desktop_done", timer_no=timer_no))
            except Exception as e:
                self.log(self.get_log_message("error_show_desktop", timer_no=timer_no, error=str(e)))
        else:
            self.log(self.get_log_message("log_timer_begin", timer_no=timer_no))
            for i in range(clicks):
                if cancel_event.is_set():
                    self.log(self.get_log_message("error_timer_click_interrupt", timer_no=timer_no))
                    break
                try:
                    win32api.SetCursorPos((x, y))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                    self.log(self.get_log_message("log_timer_click", timer_no=timer_no, count=i + 1))
                    if paste_text:
                        self.log(self.get_log_message("log_timer_paste_begin", timer_no=timer_no))
                        pyperclip.copy(paste_text)
                        time.sleep(0.1)
                        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                        self.log(self.get_log_message("log_timer_paste_completed", timer_no=timer_no))
                except Exception as e:
                    self.log(self.get_log_message("error_timer_click", timer_no=timer_no, error=str(e)))
                if i < clicks - 1:
                    time.sleep(interval)
        
        self.log(self.get_log_message("log_timer_completed", timer_no=timer_no))

        # --- 自动关闭逻辑 ---
        if is_last_timer and self.auto_close_enabled:
            countdown_msg = self.get_log_message("log_autoclose_countdown", delay=self.auto_close_delay_seconds)
            self.after(0, self.log, countdown_msg)
            
            time.sleep(self.auto_close_delay_seconds)
            
            self.after(0, self.save_config)
            
            closing_msg = self.get_log_message("log_autoclose_closing")
            self.after(1, self.log, closing_msg)
            
            self.after(100, self.destroy)

    def stop_timers(self):
        """点击结束按钮后停止所有定时器，恢复编辑区域"""
        self.log(self.get_log_message("log_stop_all_timer"))
        for event in self.timer_threads:
            event.set()
        self.btn_stop.config(state="disabled")
        self.btn_start.config(state="normal")
        for row in self.timer_rows:
            row.enable()

    def update_coordinate(self):
        """实时更新当前鼠标坐标显示"""
        try:
            pos = win32api.GetCursorPos()
            lang_texts = self.get_lang_texts()
            self.lbl_coord.config(text=f"{lang_texts.get('label_coordinate', 'Current Pos:')} {pos}")
        except Exception as e:
            self.log(self.get_log_message("error_get_coord", error=str(e)))
        self.after(200, self.update_coordinate)

    def log(self, message):
        """在日志框中按时间记录信息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")

    def load_config_from_file_dialog(self):
        """打开文件对话框选择配置文件并加载"""
        filepath = filedialog.askopenfilename(
            title=self.get_lang_texts().get("button_load_config", "Load Config"),
            initialdir=os.getcwd(),  # 默认目录是当前app相同目录
            filetypes=(("INI files", "*.ini"), ("All files", "*.*的发展"))
        )
        if not filepath:
            return # 用户取消选择

        filename = os.path.basename(filepath)
        # 检查文件后缀是否为 .ini (不区分大小写)
        if not filename.lower().endswith(".ini"):
            messagebox.showerror(
                self.get_lang_texts().get("error_file_dialog_title", "File Selection Error"),
                self.get_log_message("error_wrong_file_extension")
            )
            self.log(self.get_log_message("error_wrong_file_extension"))
            return

        temp_config = configparser.ConfigParser()
        try:
            temp_config.read(filepath, encoding="utf-8")
            # 校验文件内容是否基本正确 (至少有 General section 和 language)
            if not temp_config.has_section("General") or not temp_config.has_option("General", "language"):
                raise configparser.Error("Missing General section or language option")

            # 如果校验通过，则应用配置
            self.apply_config_data(temp_config, filepath)
            self.log(self.get_log_message("log_config_loaded", filename=filename))

        except configparser.Error as e:
            messagebox.showerror(
                self.get_lang_texts().get("error_config_parse", "Config Parse Error").format(filename=filename, error=str(e)),
                self.get_log_message("error_config_parse", filename=filename, error=str(e))
            )
            self.log(self.get_log_message("log_config_load_failed", filename=filename) + f" Error: {str(e)}")
        except Exception as e: # 其他可能的读取错误
            messagebox.showerror(
                self.get_lang_texts().get("error_config_parse", "Config Parse Error").format(filename=filename, error=str(e)),
                self.get_log_message("error_config_parse", filename=filename, error=str(e))
            )
            self.log(self.get_log_message("log_config_load_failed", filename=filename) + f" General Error: {str(e)}")

    def apply_config_data(self, new_config, config_filepath):
        """应用从文件中读取的配置数据来更新UI"""
        # 1. 更新语言
        old_lang = self.selected_language.get()
        new_lang = new_config.get("General", "language", fallback=old_lang)
        if new_lang != old_lang:
            self.selected_language.set(new_lang)
            # update_language 会重建很多UI，所以要在加载定时器之前做
            self.update_language() # 这会触发UI更新

        # 更新 app_config 实例，以便后续保存时基于此文件
        self.app_config = new_config
        # 在这里，我们并不直接使用 self.app_config 去构建UI，
        # 而是用 new_config 的数据来重新构建。

        # 2. 清除旧的定时器行UI和数据
        for row_obj in self.timer_rows:
            row_obj.destroy_widgets()
        self.timer_rows.clear()

        # 3. 加载新的定时器数据
        timer_data_list = []
        for section in new_config.sections():
            if section.startswith("Timer_"):
                timer_data = {
                    "x": new_config.get(section, "x", fallback=""),
                    "y": new_config.get(section, "y", fallback=""),
                    "time": new_config.get(section, "time", fallback=""),
                    "clicks": new_config.get(section, "clicks", fallback=""),
                    "show_desktop": new_config.get(section, "show_desktop", fallback="0"),
                    "interval": new_config.get(section, "interval", fallback=""),
                    "enabled": new_config.getboolean(section, "enabled", fallback=False),
                    "paste_text": new_config.get(section, "paste_text", fallback="")
                }
                timer_data_list.append(timer_data)

        if not timer_data_list: # 如果配置文件中没有Timer_数据
            # 可以选择添加默认的空行，或者保持为空
            # for _ in range(5): # 例如，添加5个空行
            #     self.add_log_timer_row_at_end(None)
            pass # 当前选择：如果没有则不添加

        # 4. 创建新的定时器行
        for data in timer_data_list:
            self.add_log_timer_row_at_end(data) # add_log_timer_row_at_end 内部会调用 rebuild_timer_rows_ui

        # 5. 更新窗口位置和大小 (可选，看是否希望加载配置时也恢复窗口状态)
        try:
            window_x = new_config.getint("General", "window_x")
            window_y = new_config.getint("General", "window_y")
            window_width = new_config.getint("General", "window_width", fallback=self.window_width)
            window_height = new_config.getint("General", "window_height", fallback=self.window_height)
            self.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
            # 更新定时器Canvas高度
            loaded_timer_canvas_height = new_config.getint("General", "timer_canvas_height", fallback=self.timer_canvas_height)
            if self.timer_canvas_height != loaded_timer_canvas_height:
                self.timer_canvas_height = loaded_timer_canvas_height
                if hasattr(self, 'canvas_timers') and self.canvas_timers.winfo_exists():
                    self.canvas_timers.config(height=self.timer_canvas_height)
                    # 高度改变后，可能需要重新计算滚动区域
                    self.after(50, lambda: self.on_scrollable_frame_configure(None))
        except (configparser.NoOptionError, ValueError):
            self.log("Window position/size not found or invalid in loaded config, using current.")
            pass # 如果没有或无效，则保持当前窗口状态

        # 确保 "Add Timer" 按钮在正确的位置
        self.rebuild_timer_rows_ui() # 再次调用以确保一切就绪

        self.log(f"UI updated from {os.path.basename(config_filepath)}")

    def on_copy_range_changed(self, event=None):
        """当复制范围下拉框选择改变时调用"""
        new_range = self.copy_range_var.get()
        if not self.app_config.has_section("General"):
            self.app_config.add_section("General")
        self.app_config.set("General", "copy_range", new_range)
        self.log(self.get_log_message("log_copy_range_changed", range=new_range, default=f"Copy range changed to: {new_range}"))

    def save_config(self):
        """保存当前设置 config.ini"""
        # 更新窗口当前位置和大小
        self.window_x = self.winfo_x()
        self.window_y = self.winfo_y()
        self.window_width = self.winfo_width()
        self.window_height = self.winfo_height()

        # 获取Canvas的当前高度用于保存
        # 确保canvas_timers存在 (例如，如果UI构建失败则可能不存在)
        current_timer_canvas_height = self.timer_canvas_height  # 默认为加载或初始化的值
        if hasattr(self, 'canvas_timers') and self.canvas_timers.winfo_exists():
            current_timer_canvas_height = self.canvas_timers.winfo_height()

        # 保存当前语言设置和窗口信息
        config = configparser.ConfigParser()
        config["General"] = {
            "language": self.selected_language.get(),
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "timer_canvas_height": current_timer_canvas_height,
            "copy_range": self.copy_range_var.get(),
            'auto_close_enabled': str(self.auto_close_enabled),
            'auto_close_delay_seconds': str(self.auto_close_delay_seconds)
        }

        # 保存当前定时器数据
        for idx, row in enumerate(self.timer_rows):
            values = row.get_values()
            section_name = f"Timer_{idx}"
            config[section_name] = {
                "x": values['x'],
                "y": values['y'],
                "time": values['time'],
                "show_desktop": "1" if values['show_desktop'] else "0",
                "clicks": values['clicks'],
                "interval": values['interval'],
                "enabled": "1" if values['enabled'] else "0"
            }
            # 单独处理粘贴文本，确保特殊字符不会导致问题
            if values['paste_text']:
                config[section_name]["paste_text"] = values['paste_text']

        # 确保 config 目录存在
        config_dir = os.path.dirname(CONFIG_FILE)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)
        self.log(self.get_log_message("log_config_saved"))

    def on_closing(self):
        """退出时保存配置再退出"""
        self.save_config()
        self.destroy()


if __name__ == '__main__':
    app = FlowTrackApp()
    app.mainloop()