import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect,
                             QButtonGroup)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from ui.styles.theme_config import ThemeManager

class WeekDayToggleButton(QPushButton):
    """
    星期状态切换胶囊按钮：
    - 点亮态（开启）：翡翠绿背景，纯白加粗文字；
    - 变暗态（关闭）：次级暗灰色，次级文字颜色；
    - 带有圆角与平滑悬浮效果。
    """
    def __init__(self, text, is_checked=True, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(is_checked)
        self.setFixedSize(54, 38)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()
        self.toggled.connect(self.update_style)

    def update_style(self):
        tm = ThemeManager()
        is_dark = tm.current_theme == "Dark"
        
        if self.isChecked():
            # 点亮态（翡翠绿）
            self.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    border: 1px solid #059669;
                    border-radius: 8px;
                    font-size: 10pt;
                    font-weight: bold;
                    padding: 0px;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
        else:
            # 变暗态（次级灰）
            bg_color = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.06)"
            border_color = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.12)"
            text_color = "#A0AEC0" if is_dark else "#718096"
            hover_bg = "rgba(255, 255, 255, 0.15)" if is_dark else "rgba(0, 0, 0, 0.10)"
            
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                    font-size: 10pt;
                    font-weight: normal;
                    padding: 0px;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                    color: {text_color};
                }}
            """)


class AutoStartScheduleDialog(QDialog):
    """
    模态弹窗：用于设置开机自启动在星期一到星期天的生效排程。
    设计语言与 RandomTimeDialog 和 NotesEditorDialog 严格统一，具备毛玻璃悬浮卡片与深浅色自适应。
    """
    def __init__(self, schedule_days, config, parent=None):
        super().__init__(parent)
        self.config = config
        # schedule_days: 7项 bool 列表，索引 0~6 对应周一至周日
        if not schedule_days or len(schedule_days) != 7:
            self.schedule_days = [True, True, True, True, True, False, False]
        else:
            self.schedule_days = list(schedule_days)
            
        self.result_schedule = None
        
        self.setWindowTitle(self.config.get_message("dialog_autostart_schedule_title"))
        self.setFixedSize(480, 270)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setObjectName("AutoStartScheduleDialog")
        
        # 标题栏深浅主题同步
        tm = ThemeManager()
        ThemeManager.set_title_bar_theme(self.winId(), tm.current_theme == "Dark")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        
        # 1. 悬浮质感主卡片 (对齐 RandomTimeCard 规范)
        self.card_frame = QFrame()
        self.card_frame.setObjectName("AutoStartScheduleCard")
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(12)
        
        # 卡片投影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 35))
        self.card_frame.setGraphicsEffect(shadow)
        
        # 提示文案
        lbl_hint = QLabel(self.config.get_message("tooltip_autostart_settings"))
        lbl_hint.setStyleSheet("font-size: 10pt; color: #4A5568; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;")
        card_layout.addWidget(lbl_hint)
        
        # 2. 星期切换胶囊排 (周一至周日)
        days_layout = QHBoxLayout()
        days_layout.setContentsMargins(0, 4, 0, 4)
        days_layout.setSpacing(8)
        
        weekday_keys = [
            "weekday_mon", "weekday_tue", "weekday_wed", 
            "weekday_thu", "weekday_fri", "weekday_sat", "weekday_sun"
        ]
        
        self.day_buttons = []
        for i, key in enumerate(weekday_keys):
            day_name = self.config.get_message(key)
            is_active = self.schedule_days[i]
            btn = WeekDayToggleButton(day_name, is_checked=is_active)
            self.day_buttons.append(btn)
            days_layout.addWidget(btn)
            
        card_layout.addLayout(days_layout)
        
        # 3. 快捷预设按钮组 (工作日一键开启 / 全周开启)
        quick_layout = QHBoxLayout()
        quick_layout.setContentsMargins(0, 0, 0, 0)
        quick_layout.setSpacing(10)
        
        self.btn_workdays = QPushButton(self.config.get_message("btn_quick_workdays"))
        self.btn_workdays.setCursor(Qt.PointingHandCursor)
        self.btn_workdays.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #10B981;
                border: none;
                font-size: 9.5pt;
                font-weight: 500;
                text-decoration: underline;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QPushButton:hover {
                color: #059669;
            }
        """)
        self.btn_workdays.clicked.connect(self.set_quick_workdays)
        
        self.btn_everyday = QPushButton(self.config.get_message("btn_quick_everyday"))
        self.btn_everyday.setCursor(Qt.PointingHandCursor)
        self.btn_everyday.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #10B981;
                border: none;
                font-size: 9.5pt;
                font-weight: 500;
                text-decoration: underline;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QPushButton:hover {
                color: #059669;
            }
        """)
        self.btn_everyday.clicked.connect(self.set_quick_everyday)
        
        quick_layout.addWidget(self.btn_workdays)
        quick_layout.addWidget(self.btn_everyday)
        quick_layout.addStretch()
        
        card_layout.addLayout(quick_layout)
        layout.addWidget(self.card_frame)
        
        # 4. 底部标准操作按钮 (对齐 NotesEditorDialog / RandomTimeDialog 规范)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton(self.config.get_message("btn_cancel"))
        self.btn_cancel.setObjectName("ActionButton")
        self.btn_cancel.setProperty("type", "cancel")
        self.btn_cancel.setFixedSize(105, 36)
        self.btn_cancel.setStyleSheet("font-size: 10pt; font-weight: 500;")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton(self.config.get_message("btn_save"))
        self.btn_save.setObjectName("ActionButton")
        self.btn_save.setProperty("type", "start")
        self.btn_save.setFixedSize(105, 36)
        self.btn_save.setStyleSheet("font-size: 10pt; font-weight: 500;")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_and_close)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def set_quick_workdays(self):
        """一键设置为工作日开启 (周一至周五亮起，周六日变暗)"""
        for i, btn in enumerate(self.day_buttons):
            btn.setChecked(i < 5)

    def set_quick_everyday(self):
        """一键设置为全周每天开启"""
        for btn in self.day_buttons:
            btn.setChecked(True)

    def save_and_close(self):
        self.result_schedule = [btn.isChecked() for btn in self.day_buttons]
        self.accept()

    def get_schedule(self):
        return self.result_schedule or self.schedule_days
