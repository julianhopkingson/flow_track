import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QSpinBox, 
                             QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import qtawesome as qta
from ui.styles.theme_config import ThemeManager

class RandomTimeDialog(QDialog):
    """
    模态弹窗：用于设置单行任务的随机时间波动范围与防重间隔。
    设计语言与 NotesEditorDialog 严格统一，具备毛玻璃卡片与深浅色模式自适应。
    """
    def __init__(self, data, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.data = data or {}
        
        # 解析初始数据
        self.start_h = self.data.get("random_start_h", 8)
        self.start_m = self.data.get("random_start_m", 50)
        self.end_h = self.data.get("random_end_h", 8)
        self.end_m = self.data.get("random_end_m", 59)
        self.min_interval = self.data.get("random_min_interval", 3)
        self.last_time = self.data.get("random_last_time", "")
        
        self.result_data = None
        
        self.setWindowTitle(self.config.get_message("title_random_time_config"))
        self.setFixedSize(480, 260)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setObjectName("RandomTimeDialog")
        
        # 标题栏深浅主题同步
        tm = ThemeManager()
        ThemeManager.set_title_bar_theme(self.winId(), tm.current_theme == "Dark")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        
        # 1. 悬浮质感主卡片 (饱满舒展，与窗口形成自然黄金比例)
        self.card_frame = QFrame()
        self.card_frame.setObjectName("RandomTimeCard")
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(20, 14, 20, 14)
        card_layout.setSpacing(10)
        
        # 卡片投影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 35))
        self.card_frame.setGraphicsEffect(shadow)
        
        # 2. 表单网格 (大字体、深色清晰、比例匀称)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        
        # 文本标签基础样式 (无加粗，舒适视觉层级)
        lbl_style_normal = "font-size: 10pt; font-weight: normal; color: #2D3748; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;"
        
        # 行 1: 随机范围 (从 ~ 到)
        lbl_range = QLabel(self.config.get_message("lbl_random_range"))
        lbl_range.setStyleSheet(lbl_style_normal)
        
        range_widget = QFrame()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.setSpacing(4)
        
        self.spin_start_h = self._create_spin(0, 23, self.start_h, width=50)
        lbl_colon1 = QLabel(":")
        lbl_colon1.setStyleSheet("font-size: 10pt; font-weight: bold; color: #10B981;")
        self.spin_start_m = self._create_spin(0, 59, self.start_m, width=52)
        
        lbl_to = QLabel("~")
        lbl_to.setStyleSheet("font-size: 10pt; font-weight: bold; color: #10B981; padding: 0 4px;")
        
        self.spin_end_h = self._create_spin(0, 23, self.end_h, width=50)
        lbl_colon2 = QLabel(":")
        lbl_colon2.setStyleSheet("font-size: 10pt; font-weight: bold; color: #10B981;")
        self.spin_end_m = self._create_spin(0, 59, self.end_m, width=52)
        
        range_layout.addWidget(self.spin_start_h)
        range_layout.addWidget(lbl_colon1)
        range_layout.addWidget(self.spin_start_m)
        range_layout.addWidget(lbl_to)
        range_layout.addWidget(self.spin_end_h)
        range_layout.addWidget(lbl_colon2)
        range_layout.addWidget(self.spin_end_m)
        range_layout.addStretch()
        
        grid.addWidget(lbl_range, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(range_widget, 0, 1, Qt.AlignLeft | Qt.AlignVCenter)
        
        # 行 2: 最小间隔相差分钟数
        lbl_interval = QLabel(self.config.get_message("lbl_random_interval"))
        lbl_interval.setStyleSheet(lbl_style_normal)
        
        self.spin_interval = self._create_spin(0, 60, self.min_interval, width=50)
        lbl_unit = QLabel(self.config.get_message("lbl_minutes_unit"))
        lbl_unit.setStyleSheet("font-size: 9.5pt; font-weight: normal; color: #4A5568; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;")
        
        interval_box = QHBoxLayout()
        interval_box.setContentsMargins(0, 0, 0, 0)
        interval_box.setSpacing(6)
        interval_box.addWidget(self.spin_interval)
        interval_box.addWidget(lbl_unit)
        interval_box.addStretch()
        
        grid.addWidget(lbl_interval, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addLayout(interval_box, 1, 1, Qt.AlignLeft | Qt.AlignVCenter)
        
        # 行 3: 上次时间记录
        lbl_last = QLabel(self.config.get_message("lbl_random_last_time"))
        lbl_last.setStyleSheet("font-size: 9.5pt; font-weight: normal; color: #718096; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;")
        
        last_time_display = self._format_last_time(self.last_time)
        self.lbl_last_val = QLabel(last_time_display)
        self.lbl_last_val.setStyleSheet("color: #10B981; font-weight: bold; font-size: 10pt; font-family: 'Consolas', 'Segoe UI', monospace;")
        
        grid.addWidget(lbl_last, 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(self.lbl_last_val, 2, 1, Qt.AlignLeft | Qt.AlignVCenter)
        
        card_layout.addLayout(grid)
        
        # 错误提示标签
        self.lbl_err = QLabel()
        self.lbl_err.setStyleSheet("color: #E53E3E; font-size: 9pt; font-weight: bold;")
        self.lbl_err.hide()
        card_layout.addWidget(self.lbl_err)
        
        layout.addWidget(self.card_frame)
        
        # 3. 底部操作按钮 (对齐 NotesEditorDialog 规范，舒展大气)
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
        
        # 监听数值变化进行防呆验证
        self.spin_start_h.valueChanged.connect(self.validate_range)
        self.spin_start_m.valueChanged.connect(self.validate_range)
        self.spin_end_h.valueChanged.connect(self.validate_range)
        self.spin_end_m.valueChanged.connect(self.validate_range)
        self.validate_range()

    def _create_spin(self, min_val, max_val, current_val, width=50):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(current_val)
        spin.setFixedWidth(width)
        spin.setFixedHeight(32)
        spin.setAlignment(Qt.AlignCenter)
        spin.setStyleSheet("color: #10B981; font-size: 10pt; font-weight: bold;")
        return spin

    def _format_last_time(self, t_str):
        if not t_str or len(str(t_str)) < 4:
            return self.config.get_message("lbl_none")
        s = str(t_str)
        if len(s) == 6:
            return f"{s[0:2]}:{s[2:4]}:{s[4:6]}"
        elif len(s) == 4:
            return f"{s[0:2]}:{s[2:4]}:00"
        return s

    def validate_range(self):
        s_min = self.spin_start_h.value() * 60 + self.spin_start_m.value()
        e_min = self.spin_end_h.value() * 60 + self.spin_end_m.value()
        
        if s_min > e_min:
            self.lbl_err.setText(self.config.get_message("err_random_range_invalid"))
            self.lbl_err.show()
            self.btn_save.setEnabled(False)
        else:
            self.lbl_err.hide()
            self.btn_save.setEnabled(True)

    def save_and_close(self):
        self.result_data = {
            "random_start_h": self.spin_start_h.value(),
            "random_start_m": self.spin_start_m.value(),
            "random_end_h": self.spin_end_h.value(),
            "random_end_m": self.spin_end_m.value(),
            "random_min_interval": self.spin_interval.value(),
            "random_last_time": self.last_time
        }
        self.accept()
