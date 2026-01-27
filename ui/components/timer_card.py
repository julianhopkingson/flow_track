from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, 
                             QCheckBox, QTimeEdit, QFrame, QVBoxLayout, QLabel, QSpinBox)
from PySide6.QtCore import Qt, QTime, Signal, QEvent, QObject
import qtawesome as qta

class WheelIgnoreFilter(QObject):
    """Event filter to ignore wheel events on spinboxes so list scrolling works naturally."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            event.ignore()
            return True
        return super().eventFilter(obj, event)

class TimerCard(QFrame):
    # Signals for parent communication
    delete_requested = Signal(object)
    insert_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    copy_requested = Signal(object)

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
    def __init__(self, data=None, config=None):
        super().__init__()
        self.config = config # ConfigManager instance
        self.wheel_filter = WheelIgnoreFilter(self)
        self.init_ui()
        if data:
            self.set_values(data)

    def init_ui(self):
        self.setObjectName("TimerCard")
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(80) # Fixed height for consistency
        
        # Style
        self.setStyleSheet("""
            QFrame#TimerCard {
                background-color: white;
                border-radius: 12px;
                margin: 4px;
            }
            QPushButton#IconButton {
                border: 1px solid #E2E8F0; 
                border-radius: 8px; 
                background: #F8FAFC;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        # 1. Action Buttons Group
        self.btn_del = QPushButton(qta.icon('fa5s.trash-alt', color='#EF4444'), "")
        self.btn_add = QPushButton(qta.icon('fa5s.plus', color='#10B981'), "")
        self.btn_up = QPushButton(qta.icon('fa5s.arrow-up'), "")
        self.btn_down = QPushButton(qta.icon('fa5s.arrow-down'), "")
        
        self.btn_del.setToolTip("Delete")
        self.btn_add.setToolTip("Insert After")
        
        for btn in [self.btn_del, self.btn_add, self.btn_up, self.btn_down]:
            btn.setFixedSize(28, 28)
            btn.setObjectName("IconButton")
            layout.addWidget(btn)

        # 2. Enabled Checkbox
        self.chk_enabled = QCheckBox()
        self.chk_enabled.setChecked(True)
        self.chk_enabled.setFixedWidth(30)
        layout.addWidget(self.chk_enabled)

        # 3. Coordinates
        self.edit_x = QLineEdit()
        self.edit_x.setPlaceholderText("X")
        self.edit_x.setFixedWidth(50)
        self.edit_y = QLineEdit()
        self.edit_y.setPlaceholderText("Y")
        self.edit_y.setFixedWidth(50)
        layout.addWidget(self.edit_x)
        layout.addWidget(self.edit_y)

        # 4. Time (HH:MM:SS) - Legacy Fidelity
        self.time_frame = QWidget()
        time_layout = QHBoxLayout(self.time_frame)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(2)

        self.spin_h = QSpinBox()
        self.spin_m = QSpinBox()
        self.spin_s = QSpinBox()
        
        for s in [self.spin_h, self.spin_m, self.spin_s]:
            s.setButtonSymbols(QSpinBox.NoButtons)
            s.setAlignment(Qt.AlignCenter)
            s.setFixedWidth(33) # Slightly wider for better visual gap
            s.installEventFilter(self.wheel_filter) # Architectural Fix: Ignore scroll
            # Removed inline 'background: white' style here, handled by theme.qss

        self.spin_h.setRange(0, 23)
        self.spin_m.setRange(0, 59)
        self.spin_s.setRange(0, 59)

        time_layout.addWidget(self.spin_h)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.spin_m)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.spin_s)
        
        layout.addWidget(self.time_frame)

        # 5. Copy Button
        self.btn_copy = QPushButton(qta.icon('fa5s.copy', color='#4B5563'), "")
        self.btn_copy.setFixedSize(28, 28)
        self.btn_copy.setObjectName("IconButton")
        layout.addWidget(self.btn_copy)

        # 6. Show Desktop (Order: Icon then Checkbox)
        self.lbl_desktop_icon = QLabel(self.config.get_message("radio_show_desktop"))
        self.chk_desktop = QCheckBox()
        layout.addWidget(self.lbl_desktop_icon)
        layout.addWidget(self.chk_desktop)
        self.chk_desktop.toggled.connect(self.on_desktop_toggled)

        # 7. Execution Params
        self.edit_clicks = QLineEdit()
        self.edit_clicks.setPlaceholderText(self.config.get_message("clicks"))
        self.edit_clicks.setFixedWidth(50)
        self.edit_interval = QLineEdit()
        self.edit_interval.setPlaceholderText(self.config.get_message("interval"))
        self.edit_interval.setFixedWidth(50)
        layout.addWidget(self.edit_clicks)
        layout.addWidget(self.edit_interval)

        # 8. Notes
        self.edit_notes = QLineEdit()
        self.edit_notes.setPlaceholderText(self.config.get_message("paste_text"))
        self.edit_notes.setMinimumWidth(150)
        layout.addWidget(self.edit_notes, 1)

        # Connections
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self))
        self.btn_add.clicked.connect(lambda: self.insert_requested.emit(self))
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self))
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self))
        self.btn_copy.clicked.connect(lambda: self.copy_requested.emit(self))

    def on_desktop_toggled(self, checked):
        # Fix for Qt Enum truthiness: bool(Qt.Unchecked) is often True in Python.
        # We must explicitly check for Checked state or boolean True.
        if isinstance(checked, bool):
            is_desktop = checked
        else:
            is_desktop = checked == Qt.Checked
        
        # Legacy Logic: Clear and Disable dependent widgets
        widgets = [self.edit_x, self.edit_y, self.edit_clicks, self.edit_interval, self.edit_notes]
        for w in widgets:
            w.setEnabled(not is_desktop)
            if is_desktop:
                # Physically clear the content to prevent accidental execution
                w.clear()

    def get_values(self):
        time_str = f"{self.spin_h.value():02d}{self.spin_m.value():02d}{self.spin_s.value():02d}"
        return {
            "enabled": self.chk_enabled.isChecked(),
            "x": self.edit_x.text(),
            "y": self.edit_y.text(),
            "time": time_str,
            "show_desktop": self.chk_desktop.isChecked(),
            "clicks": self.edit_clicks.text(),
            "interval": self.edit_interval.text(),
            "paste_text": self.edit_notes.text()
        }

    def set_values(self, data):
        # Block signals to prevent on_desktop_toggled from clearing data during loading
        self.chk_desktop.blockSignals(True)
        
        self.chk_enabled.setChecked(data.get("enabled", True))
        self.edit_x.setText(str(data.get("x", "")))
        self.edit_y.setText(str(data.get("y", "")))
        
        t_str = str(data.get("time", "000000"))
        if len(t_str) == 6:
            self.spin_h.setValue(int(t_str[0:2]))
            self.spin_m.setValue(int(t_str[2:4]))
            self.spin_s.setValue(int(t_str[4:6]))
            
        self.chk_desktop.setChecked(bool(int(data.get("show_desktop", 0))))
        self.edit_clicks.setText(str(data.get("clicks", "")))
        self.edit_interval.setText(str(data.get("interval", "")))
        self.edit_notes.setText(str(data.get("paste_text", "")))
        
        self.chk_desktop.blockSignals(False)
        # Apply visual state manually (Pass pure boolean to avoid truthiness bugs)
        self.on_desktop_toggled(self.chk_desktop.isChecked())

    def update_partial_values(self, data):
        """Update only specific fields (used for copy logic)."""
        if "time" in data:
            t_str = str(data["time"])
            if len(t_str) == 6:
                self.spin_h.setValue(int(t_str[0:2]))
                self.spin_m.setValue(int(t_str[2:4]))
                self.spin_s.setValue(int(t_str[4:6]))
        if "clicks" in data and data["clicks"] is not None:
            self.edit_clicks.setText(str(data["clicks"]))
        if "interval" in data and data["interval"] is not None:
            self.edit_interval.setText(str(data["interval"]))

    def retranslate_ui(self):
        """Update localized text for inputs."""
        self.lbl_desktop_icon.setText(self.config.get_message("radio_show_desktop"))
        self.edit_clicks.setPlaceholderText(self.config.get_message("clicks"))
        self.edit_interval.setPlaceholderText(self.config.get_message("interval"))
        self.edit_notes.setPlaceholderText(self.config.get_message("paste_text"))

    def set_editing_enabled(self, enabled):
        """Enable or disable all child widgets for editing."""
        self.btn_del.setEnabled(enabled)
        self.btn_add.setEnabled(enabled)
        self.btn_up.setEnabled(enabled)
        self.btn_down.setEnabled(enabled)
        self.chk_enabled.setEnabled(enabled)
        self.edit_x.setEnabled(enabled)
        self.edit_y.setEnabled(enabled)
        self.spin_h.setEnabled(enabled)
        self.spin_m.setEnabled(enabled)
        self.spin_s.setEnabled(enabled)
        self.btn_copy.setEnabled(enabled)
        self.chk_desktop.setEnabled(enabled)
        self.edit_clicks.setEnabled(enabled)
        self.edit_interval.setEnabled(enabled)
        self.edit_notes.setEnabled(enabled)
        
        # Re-enforce desktop logic if enabled
        if enabled:
            self.on_desktop_toggled(self.chk_desktop.isChecked())
