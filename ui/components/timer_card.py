from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, 
                             QCheckBox, QTimeEdit, QFrame, QVBoxLayout, QLabel, QSpinBox,
                             QGraphicsDropShadowEffect, QMessageBox, QDialog)
from PySide6.QtGui import QPainter, QIcon, QColor
from PySide6.QtCore import Qt, Signal, QEvent, QObject, QPropertyAnimation, QEasingCurve
import qtawesome as qta
from .notes_editor import NotesEditorDialog

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

    def __init__(self, data=None, config=None):
        super().__init__()
        self.config = config # ConfigManager instance
        self.wheel_filter = WheelIgnoreFilter(self)
        self.init_ui()
        self.setup_effects()
        if data:
            self.set_values(data)

    def setup_effects(self):
        # 1. Shadow Effect - "Heng Dong" Style: Large Blur, Very Low Opacity
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(2)
        self.shadow.setColor(Qt.transparent) # Start hidden
        self.setGraphicsEffect(self.shadow)

        # 2. Animations
        self.anim_shadow = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim_shadow.setDuration(300)
        self.anim_shadow.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_offset = QPropertyAnimation(self.shadow, b"yOffset")
        self.anim_offset.setDuration(300)
        self.anim_offset.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        self.raise_() # Elevate Z-order
        self.shadow.setColor(QColor(0, 0, 0, 15)) # Ultra-subtle shadow (5.8% alpha)
        self.anim_shadow.setEndValue(40)
        self.anim_offset.setEndValue(6)
        self.anim_shadow.start()
        self.anim_offset.start()
        self.setProperty("hover", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim_shadow.setEndValue(15)
        self.anim_offset.setEndValue(4)
        self.anim_shadow.start()
        self.anim_offset.start()
        self.setProperty("hover", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def init_ui(self):
        self.setObjectName("TimerCard")
        self.setAttribute(Qt.WA_StyledBackground) # Ensure QSS backgrounds render on custom widgets
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(60) 
        
        # Base Style (Will be refined by theme.qss, but we set object for targeting)
        # No hardcoded pixel colors here except for transparency
        pass # All styles moved to theme.qss

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
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
        self.edit_x.setFixedWidth(55)
        self.edit_x.setMaxLength(4)
        self.edit_x.setAlignment(Qt.AlignCenter)
        self.edit_y = QLineEdit()
        self.edit_y.setPlaceholderText("Y")
        self.edit_y.setFixedWidth(55)
        self.edit_y.setMaxLength(4)
        self.edit_y.setAlignment(Qt.AlignCenter)
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
            s.setFixedWidth(40) # Compacted for v9.8 (Padding reduced in QSS)
            s.installEventFilter(self.wheel_filter) # Architectural Fix: Ignore scroll
            # Removed inline 'background: white' style here, handled by theme.qss

        self.spin_h.setRange(0, 23)
        self.spin_m.setRange(0, 59)
        self.spin_s.setRange(0, 59)

        time_layout.addWidget(self.spin_h)
        lbl_colon1 = QLabel(":")
        lbl_colon1.setFixedWidth(12)
        lbl_colon1.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(lbl_colon1)
        
        time_layout.addWidget(self.spin_m)
        lbl_colon2 = QLabel(":")
        lbl_colon2.setFixedWidth(12)
        lbl_colon2.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(lbl_colon2)
        
        time_layout.addWidget(self.spin_s)
        
        layout.addWidget(self.time_frame)

        # 5. Copy Button
        self.btn_copy = QPushButton(qta.icon('fa5s.copy', color='#718096'), "")
        self.btn_copy.setFixedSize(28, 28)
        self.btn_copy.setObjectName("IconButton")
        layout.addWidget(self.btn_copy)

        # 6. Show Desktop (Final v8.3.1: Balanced spacing & Unified CheckBox)
        self.desktop_group_widget = QWidget()
        self.desktop_group_widget.setFixedWidth(42) # Precise width for balanced coupling
        
        desktop_group_layout = QHBoxLayout(self.desktop_group_widget)
        desktop_group_layout.setContentsMargins(0, 0, 0, 0)
        desktop_group_layout.setSpacing(5) # Balanced spacing (v10.5: 5px)
        
        self.lbl_desktop_icon = QLabel()
        self.lbl_desktop_icon.setPixmap(qta.icon('fa5s.desktop', color='#26D07C').pixmap(18, 18))
        self.lbl_desktop_icon.setToolTip("") # Tooltip handled by retranslate if needed
        
        self.chk_desktop = QCheckBox()
        self.chk_desktop.toggled.connect(self.on_desktop_toggled)
        
        desktop_group_layout.addWidget(self.lbl_desktop_icon)
        desktop_group_layout.addWidget(self.chk_desktop)
        
        layout.addWidget(self.desktop_group_widget)

        # 7. Execution Params (Refined v9.3: Mouse & Clock Icons)
        self.lbl_clicks_icon = QLabel()
        self.lbl_clicks_icon.setPixmap(qta.icon('fa5s.mouse', color='#26D07C').pixmap(16, 16))
        self.edit_clicks = QLineEdit()
        self.edit_clicks.setFixedWidth(45)
        self.edit_clicks.setMaxLength(2)
        self.edit_clicks.setAlignment(Qt.AlignCenter)
        
        self.lbl_interval_icon = QLabel()
        self.lbl_interval_icon.setPixmap(qta.icon('fa5s.clock', color='#26D07C').pixmap(16, 16))
        self.edit_interval = QLineEdit()
        self.edit_interval.setFixedWidth(45)
        self.edit_interval.setMaxLength(2)
        self.edit_interval.setAlignment(Qt.AlignCenter)
        
        # Sub-groups for precise 5px spacing (v10.6)
        self.clicks_group = QWidget()
        clicks_layout = QHBoxLayout(self.clicks_group)
        clicks_layout.setContentsMargins(0, 0, 0, 0)
        clicks_layout.setSpacing(5)
        clicks_layout.addWidget(self.lbl_clicks_icon)
        clicks_layout.addWidget(self.edit_clicks)
        
        self.interval_group = QWidget()
        interval_layout = QHBoxLayout(self.interval_group)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(5)
        interval_layout.addWidget(self.lbl_interval_icon)
        interval_layout.addWidget(self.edit_interval)
        
        layout.addWidget(self.clicks_group)
        layout.addWidget(self.interval_group)
        
        # 8. Notes (v14.0: Interactive Modal Editor Button)
        # Replaced QLabel with QPushButton for clickable interaction
        self.btn_notes_edit = QPushButton()
        self.btn_notes_edit.setFixedSize(24, 24) # Slightly larger click target
        self.btn_notes_edit.setFlat(True)
        self.btn_notes_edit.setCursor(Qt.PointingHandCursor)
        self.btn_notes_edit.clicked.connect(self.open_notes_editor)
        
        self.edit_notes = QLineEdit()
        self.edit_notes.setObjectName("edit_notes") # Assign ID for specific QSS styling
        self.edit_notes.setMinimumWidth(150)
        self.edit_notes.setAlignment(Qt.AlignLeft) # Code-level alignment
        
        layout.addWidget(self.edit_notes, 1)
        layout.addWidget(self.btn_notes_edit)

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
        
        # v9.5 Statification: Update Icon colors based on editability
        # Fix (v13.0): Decouple button colors from param input state
        self.update_icon_states(can_edit=not is_desktop, actions_active=True)

    def update_icon_states(self, can_edit, actions_active=None):
        """
        Update colors of all icons.
        can_edit: Controls param inputs (X, Y, Clicks, Notes) color.
        actions_active: Controls management buttons (Add, Del, Copy) color. 
                        If None, defaults to same as can_edit (Legacy behavior).
        """
        if actions_active is None:
            actions_active = can_edit

        color_param = '#26D07C' if can_edit else '#CBD5E0'
        # Desktop icon should match param state or be highlighted if checked? 
        # Requirement: "Modified to Green". Keep it consistent with params for now.
        color_desktop = '#26D07C' if can_edit else '#CBD5E0'
        
        # 1. Labels (Pure Pixmap - works naturally)
        self.lbl_desktop_icon.setPixmap(qta.icon('fa5s.desktop', color=color_desktop).pixmap(18, 18))
        self.lbl_clicks_icon.setPixmap(qta.icon('fa5s.mouse', color=color_param).pixmap(16, 16))
        self.lbl_interval_icon.setPixmap(qta.icon('fa5s.clock', color=color_param).pixmap(16, 16))
        # self.lbl_notes_icon (Removed in v14.0)
        
        # 2. Buttons (Plan A: Force Disable Stage to matching solid color)
        def set_solid_icon(btn, icon_name, active_color, locked_color, size=18):
            # Use actions_active for Copy/Del/Add/Up/Down
            target_color = active_color if actions_active else locked_color
            pix = qta.icon(icon_name, color=target_color).pixmap(size, size)
            icon = QIcon()
            icon.addPixmap(pix, QIcon.Disabled) # Override Qt's automatic fading
            btn.setIcon(icon)

        # Copy Button & Notes Edit Button (v14.0)
        set_solid_icon(self.btn_copy, 'fa5s.copy', '#26D07C', '#CBD5E0', 16)
        # Notes button should behave like a param input (can_edit), not an action button?
        # Requirement: "Clicking edit button...". It edits the input. So it follows can_edit.
        notes_color = '#26D07C' if can_edit else '#CBD5E0'
        pix_notes = qta.icon('fa5s.edit', color=notes_color).pixmap(16, 16)
        # We manually set icon for btn_notes_edit because it uses can_edit logic directly
        self.btn_notes_edit.setIcon(QIcon(pix_notes))
        self.btn_notes_edit.setEnabled(can_edit) # Logically disable it too
        
        # Left side buttons (Management) - Also unified to #CBD5E0 when locked
        set_solid_icon(self.btn_del, 'fa5s.trash-alt', '#EF4444', '#CBD5E0', 16)
        set_solid_icon(self.btn_add, 'fa5s.plus', '#10B981', '#CBD5E0', 16)
        set_solid_icon(self.btn_up, 'fa5s.arrow-up', '#4A5568', '#CBD5E0', 16)
        set_solid_icon(self.btn_down, 'fa5s.arrow-down', '#4A5568', '#CBD5E0', 16)

    def open_notes_editor(self):
        """Open modal dialog to edit notes."""
        dialog = NotesEditorDialog(self.edit_notes.text(), self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.edit_notes.setText(dialog.get_text())

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
        """Update tooltips without overwriting Pixmap Icons."""
        self.lbl_desktop_icon.setToolTip(self.config.get_message("radio_show_desktop"))
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
        else:
            # v9.5: If the whole card is disabled, ensure icons are grayed out
            self.update_icon_states(False)
