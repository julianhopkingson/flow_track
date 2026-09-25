from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, 
                             QCheckBox, QTimeEdit, QFrame, QVBoxLayout, QLabel, QSpinBox,
                             QGraphicsDropShadowEffect, QMessageBox, QDialog)
from PySide6.QtGui import QPainter, QIcon, QColor
from PySide6.QtCore import Qt, Signal, QEvent, QObject, QPropertyAnimation, QEasingCurve
import qtawesome as qta
from .notes_editor import NotesEditorDialog
from .random_time_dialog import RandomTimeDialog
from ui.styles.theme_config import ThemeManager

class WheelIgnoreFilter(QObject):
    """Event filter to ignore wheel events on spinboxes so list scrolling works naturally."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            event.ignore()
            return True
        return super().eventFilter(obj, event)

class NotesFocusFilter(QObject):
    """
    Auto-scroll to start when focus is lost.
    Ensures long text is displayed from the beginning ("Left Aligned" view) 
    when not actively editing.
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            if isinstance(obj, QLineEdit):
                # Force view to scroll to start (Left Display)
                obj.setCursorPosition(0) 
        return super().eventFilter(obj, event)

class TimerCard(QFrame):
    # Signals for parent communication
    delete_requested = Signal(object)
    insert_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    copy_requested = Signal(object)
    random_triggered = Signal(object)
    random_toggled = Signal(object, bool)

    def __init__(self, data=None, config=None):
        super().__init__()
        self.config = config # ConfigManager instance
        self.theme_manager = ThemeManager()
        self.wheel_filter = WheelIgnoreFilter(self)
        self.data = data or {}
        
        # 随机时间参数存储
        self.random_enabled = bool(int(self.data.get("random_enabled", 0))) if self.data else False
        self.random_start_h = int(self.data.get("random_start_h", 8)) if self.data else 8
        self.random_start_m = int(self.data.get("random_start_m", 50)) if self.data else 50
        self.random_end_h = int(self.data.get("random_end_h", 8)) if self.data else 8
        self.random_end_m = int(self.data.get("random_end_m", 59)) if self.data else 59
        self.random_min_interval = int(self.data.get("random_min_interval", 3)) if self.data else 3
        self.random_last_time = str(self.data.get("random_last_time", "")) if self.data else ""

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
            s.setButtonSymbols(QSpinBox.NoButtons) # Scheme C: Default hidden for height alignment
            s.setWrapping(True)
            s.setAlignment(Qt.AlignCenter)
            s.setFixedWidth(48) 
            s.installEventFilter(self.wheel_filter) 
            
            # Scheme C: Add hover detection logic
            s.enterEvent = lambda e, sb=s: sb.setButtonSymbols(QSpinBox.UpDownArrows) if sb.isEnabled() else None
            s.leaveEvent = lambda e, sb=s: sb.setButtonSymbols(QSpinBox.NoButtons)

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
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.btn_copy)

        # 5.1 随机时间单选开关 (Radio Checkbox，位于随机按钮之前)
        self.chk_random = QCheckBox()
        self.chk_random.setCursor(Qt.PointingHandCursor)
        self.chk_random.toggled.connect(self.on_random_chk_toggled)
        layout.addWidget(self.chk_random)

        # 5.2 重新随机摇点按钮 (专职 Action 按钮)
        self.btn_random_toggle = QPushButton()
        self.btn_random_toggle.setFixedSize(28, 28)
        self.btn_random_toggle.setObjectName("IconButton")
        self.btn_random_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_random_toggle.clicked.connect(self.on_random_action_clicked)
        layout.addWidget(self.btn_random_toggle)

        # 5.3 随机参数设置图标
        self.btn_random_config = QPushButton()
        self.btn_random_config.setFixedSize(28, 28)
        self.btn_random_config.setObjectName("IconButton")
        self.btn_random_config.clicked.connect(self.open_random_config_dialog)
        layout.addWidget(self.btn_random_config)

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
        
        # Install Focus Filter for Auto-Home Alignment (v20.0)
        self.notes_focus_filter = NotesFocusFilter(self)
        self.edit_notes.installEventFilter(self.notes_focus_filter)
        
        layout.addWidget(self.edit_notes, 1)
        layout.addWidget(self.btn_notes_edit)

        # Initialize Tooltips
        self.retranslate_ui()

        # Connections
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self))
        self.btn_add.clicked.connect(lambda: self.insert_requested.emit(self))
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self))
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self))
        self.btn_copy.clicked.connect(lambda: self.copy_requested.emit(self))

        # 初始同步图标与状态 (确保未选中时骰子与设置按钮立即置灰)
        self.refresh_icons()

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
        self.refresh_icons()

    def refresh_icons(self):
        """统一刷新整张卡片的所有图标与颜色状态，消除不同调用源的逻辑分歧。"""
        is_card_enabled = self.btn_del.isEnabled()
        is_desktop = self.chk_desktop.isChecked()
        self.update_icon_states(
            can_edit=is_card_enabled and not is_desktop,
            actions_active=is_card_enabled,
            desktop_active=is_desktop
        )

    def update_after_theme_change(self):
        """Called by MainWindow when theme changes."""
        self.refresh_icons()

    def update_icon_states(self, can_edit, actions_active=None, desktop_active=False):
        """
        Update colors of all icons.
        can_edit: Controls param inputs (X, Y, Clicks, Notes) color.
        actions_active: Controls management buttons (Add, Del, Copy) color. 
                        If None, defaults to same as can_edit (Legacy behavior).
        """
        if actions_active is None:
            actions_active = can_edit

        color_theme = self.theme_manager.get_color("ICON_COLOR")
        color_alt = self.theme_manager.get_color("ICON_COLOR_ALT")
        color_muted = self.theme_manager.get_color("ICON_COLOR_MUTED")

        color_param = color_theme if can_edit else color_muted
        # Desktop icon follows its own 'desktop_active' flag, independent of can_edit
        color_desktop = color_theme if desktop_active else color_muted
        
        # 1. Labels (Pure Pixmap - works naturally)
        self.lbl_desktop_icon.setPixmap(qta.icon('fa5s.desktop', color=color_desktop).pixmap(18, 18))
        self.lbl_clicks_icon.setPixmap(qta.icon('fa5s.mouse', color=color_param).pixmap(16, 16))
        self.lbl_interval_icon.setPixmap(qta.icon('fa5s.clock', color=color_param).pixmap(16, 16))
        
        # 2. Buttons (Plan A: Force Disable Stage to matching solid color)
        def set_solid_icon(btn, icon_name, active_color, locked_color, size=18):
            target_color = active_color if actions_active else locked_color
            pix = qta.icon(icon_name, color=target_color).pixmap(size, size)
            icon = QIcon()
            icon.addPixmap(pix, QIcon.Normal, QIcon.Off)
            icon.addPixmap(pix, QIcon.Normal, QIcon.On)
            icon.addPixmap(pix, QIcon.Disabled, QIcon.Off)
            icon.addPixmap(pix, QIcon.Disabled, QIcon.On)
            btn.setIcon(icon)

        # Copy Button & Notes Edit Button (v14.0)
        set_solid_icon(self.btn_copy, 'fa5s.copy', color_theme, color_muted, 16)
        
        # 随机时间开关 (chk_random) 与 随机动作按钮 (Dice)、配置 (Sliders) 状态联动
        is_random_on = self.chk_random.isChecked()
        random_btns_active = is_random_on and actions_active
        
        self.btn_random_toggle.setEnabled(random_btns_active)
        color_dice = color_theme if random_btns_active else color_muted
        pix_dice = qta.icon('fa5s.dice', color=color_dice).pixmap(16, 16)
        icon_dice = QIcon()
        icon_dice.addPixmap(pix_dice, QIcon.Normal, QIcon.Off)
        icon_dice.addPixmap(pix_dice, QIcon.Normal, QIcon.On)
        icon_dice.addPixmap(pix_dice, QIcon.Disabled, QIcon.Off)
        icon_dice.addPixmap(pix_dice, QIcon.Disabled, QIcon.On)
        self.btn_random_toggle.setIcon(icon_dice)
        self.btn_random_toggle.setCursor(Qt.PointingHandCursor if random_btns_active else Qt.ArrowCursor)

        self.btn_random_config.setEnabled(random_btns_active)
        color_config = color_theme if random_btns_active else color_muted
        pix_config = qta.icon('fa5s.sliders-h', color=color_config).pixmap(15, 15)
        icon_cfg = QIcon()
        icon_cfg.addPixmap(pix_config, QIcon.Normal, QIcon.Off)
        icon_cfg.addPixmap(pix_config, QIcon.Normal, QIcon.On)
        icon_cfg.addPixmap(pix_config, QIcon.Disabled, QIcon.Off)
        icon_cfg.addPixmap(pix_config, QIcon.Disabled, QIcon.On)
        self.btn_random_config.setIcon(icon_cfg)
        self.btn_random_config.setCursor(Qt.PointingHandCursor if random_btns_active else Qt.ArrowCursor)

        # Notes button should behave like a param input (can_edit), not an action button?
        # Requirement: "Clicking edit button...". It edits the input. So it follows can_edit.
        notes_color = color_theme if can_edit else color_muted
        pix_notes = qta.icon('fa5s.edit', color=notes_color).pixmap(16, 16)
        # We manually set icon for btn_notes_edit because it uses can_edit logic directly
        self.btn_notes_edit.setIcon(QIcon(pix_notes))
        self.btn_notes_edit.setEnabled(can_edit) # Logically disable it too
        
        # Left side buttons (Management) - Also unified to color_muted when locked
        set_solid_icon(self.btn_del, 'fa5s.trash-alt', '#EF4444', color_muted, 16)
        set_solid_icon(self.btn_add, 'fa5s.plus', '#10B981', color_muted, 16)
        set_solid_icon(self.btn_up, 'fa5s.arrow-up', color_alt, color_muted, 16)
        set_solid_icon(self.btn_down, 'fa5s.arrow-down', color_alt, color_muted, 16)

    def open_notes_editor(self):
        """
        V6 Redesign: Interference-Free Interaction
        """
        # 1. 屏蔽干扰 (Suspend potential hover effects)
        # 这一步至关重要，防止弹窗关闭瞬间触发 enterEvent -> raise_() -> Layout Thrashing
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        # 2. 宿主剥离 (Re-parent to Main Window)
        # 将 Dialog 挂载到主窗口，避免对 Card 造成布局压力
        parent_widget = self.window() if self.window() else self
        dialog = NotesEditorDialog(self.edit_notes.text(), self.config, parent_widget)
        
        # 3. 阻塞执行
        result = dialog.exec()
        
        # 4. 恢复干扰屏蔽 (Restore interactions)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        # 5. 处理结果
        if result == QDialog.Accepted:
            new_text = dialog.get_text()
            if new_text != self.edit_notes.text():
                self.edit_notes.setText(new_text)
        
        # 6. 状态与焦点“强权恢复” (Authoritative Reset)
        # 无论是否保存，都要确保 Card 回到可用的状态
        self.force_state_reset()

    def force_state_reset(self):
        """
        强制重置组件状态，无视之前的任何动画或焦点丢失。
        """
        # 计算理论状态
        is_running = not self.btn_del.isEnabled()
        is_desktop = self.chk_desktop.isChecked()
        should_enable = (not is_running) and (not is_desktop)
        
        if should_enable:
            # A. 确保启用
            self.edit_notes.setEnabled(True)
            self.btn_notes_edit.setEnabled(True)
            
            # B. 强制更新样式与重绘 (Sync Update)
            # 此时没有 Animation 干扰，Repaint 是安全的
            self.edit_notes.style().polish(self.edit_notes)
            self.edit_notes.update() 
            
            # C. 焦点夺回 (The Focus Grab)
            self.edit_notes.setFocus()

    def on_random_chk_toggled(self, checked):
        """单选圆圈开关切换：选中时亮起并激活随机，未选中时置灰并关闭。"""
        self.random_enabled = checked
        self.refresh_icons()
        self.retranslate_ui()
        self.random_toggled.emit(self, checked)

    def on_random_action_clicked(self):
        """点击骰子按钮：在开启状态下重新随机摇点并向下填充。"""
        if self.chk_random.isChecked():
            self.random_triggered.emit(self)

    def open_random_config_dialog(self):
        # 1. 屏蔽干扰 (防止弹窗关闭瞬间触发 enterEvent -> raise_() -> Layout Thrashing)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        # 2. 宿主剥离 (将 Dialog 挂载到主窗口，避免对 Card 造成内部焦点压力)
        parent_widget = self.window() if self.window() else self
        data = {
            "random_start_h": self.random_start_h,
            "random_start_m": self.random_start_m,
            "random_end_h": self.random_end_h,
            "random_end_m": self.random_end_m,
            "random_min_interval": self.random_min_interval,
            "random_last_time": self.random_last_time
        }
        dlg = RandomTimeDialog(data, self.config, parent_widget)
        
        # 3. 阻塞执行
        result = dlg.exec()
        
        # 4. 恢复干扰屏蔽
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        # 5. 强权恢复状态并彻底清空所有时间框与卡片焦点
        self.clearFocus()
        for sp in [self.spin_h, self.spin_m, self.spin_s]:
            sp.clearFocus()
            le = sp.findChild(QLineEdit)
            if le:
                le.clearFocus()
        if self.window():
            self.window().setFocus()
            
        # 6. 处理结果：若保存且处于开启状态，立即在主线程同步触发原子随机重算，杜绝异步竞态
        if result == QDialog.Accepted:
            res = dlg.result_data
            if res:
                self.random_start_h = res["random_start_h"]
                self.random_start_m = res["random_start_m"]
                self.random_end_h = res["random_end_h"]
                self.random_end_m = res["random_end_m"]
                self.random_min_interval = res["random_min_interval"]
                if self.chk_random.isChecked():
                    self.random_triggered.emit(self)

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
            "paste_text": self.edit_notes.text(),
            "random_enabled": self.chk_random.isChecked(),
            "random_start_h": self.random_start_h,
            "random_start_m": self.random_start_m,
            "random_end_h": self.random_end_h,
            "random_end_m": self.random_end_m,
            "random_min_interval": self.random_min_interval,
            "random_last_time": self.random_last_time
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
        
        self.random_enabled = bool(int(data.get("random_enabled", 0)))
        self.random_start_h = int(data.get("random_start_h", 8))
        self.random_start_m = int(data.get("random_start_m", 50))
        self.random_end_h = int(data.get("random_end_h", 8))
        self.random_end_m = int(data.get("random_end_m", 59))
        self.random_min_interval = int(data.get("random_min_interval", 3))
        self.random_last_time = str(data.get("random_last_time", ""))
        self.chk_random.blockSignals(True)
        self.chk_random.setChecked(self.random_enabled)
        self.chk_random.blockSignals(False)
        
        # [Fix] Force view to start (Left Align) on initial load
        self.edit_notes.setCursorPosition(0)
        
        # Scheme F: Force LayoutDirection to LeftToRight to block Bidi-induced alignment shifts
        self.edit_notes.setLayoutDirection(Qt.LeftToRight)
        self.edit_notes.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.chk_desktop.blockSignals(False)
        # Apply visual state manually (Pass pure boolean to avoid truthiness bugs)
        self.on_desktop_toggled(self.chk_desktop.isChecked())

    def set_time_explicit(self, h, m, s):
        """权威强制原子更新时间显示与内部值，双重保障界面文本与数值强同步，杜绝状态机脱节。"""
        # 1. 彻底清除焦点并强制停止内部编辑状态
        for sp in [self.spin_h, self.spin_m, self.spin_s]:
            sp.clearFocus()
            le = sp.findChild(QLineEdit)
            if le:
                le.clearFocus()
                le.deselect()
        
        # 2. 权威写入数值并直接同步 QLineEdit 文本显示，防止滞后失焦解析旧文本
        for sp, val in [(self.spin_h, h), (self.spin_m, m), (self.spin_s, s)]:
            sp.blockSignals(True)
            sp.setValue(int(val))
            le = sp.findChild(QLineEdit)
            if le:
                txt = f"{int(val):02d}" if sp is self.spin_s else str(int(val))
                le.setText(txt)
            sp.blockSignals(False)
            sp.update()
            sp.repaint()

    def update_partial_values(self, data):
        """Update only specific fields (used for copy logic)."""
        if "time" in data:
            t_str = str(data["time"])
            if len(t_str) == 6:
                h = int(t_str[0:2])
                m = int(t_str[2:4])
                s = int(t_str[4:6])
                self.set_time_explicit(h, m, s)
        if "clicks" in data and data["clicks"] is not None:
            self.edit_clicks.setText(str(data["clicks"]))
        if "interval" in data and data["interval"] is not None:
            self.edit_interval.setText(str(data["interval"]))

    def retranslate_ui(self):
        """Update tooltips and placeholders for all interactive elements (v15.0)."""
        # 1. Management Buttons
        self.btn_del.setToolTip(self.config.get_message("tooltip_btn_delete_timer"))
        self.btn_add.setToolTip(self.config.get_message("tooltip_btn_insert_timer"))
        self.btn_up.setToolTip(self.config.get_message("tooltip_btn_up_timer"))
        self.btn_down.setToolTip(self.config.get_message("tooltip_btn_down_timer"))
        
        # 2. Parameters (With Placeholders)
        self.chk_enabled.setToolTip(self.config.get_message("tooltip_row_enabled"))
        self.edit_x.setPlaceholderText(self.config.get_message("placeholder_x"))
        self.edit_x.setToolTip(self.config.get_message("tooltip_edit_x"))
        self.edit_y.setPlaceholderText(self.config.get_message("placeholder_y"))
        self.edit_y.setToolTip(self.config.get_message("tooltip_edit_y"))
        
        # 3. Time
        time_tip = self.config.get_message("tooltip_spin_time")
        self.spin_h.setToolTip(time_tip)
        self.spin_m.setToolTip(time_tip)
        self.spin_s.setToolTip(time_tip)
        
        # 4. Actions
        self.btn_copy.setToolTip(self.config.get_message("tooltip_btn_copy"))
        self.chk_random.setToolTip(self.config.get_message("tooltip_chk_random"))
        self.btn_random_toggle.setToolTip(self.config.get_message("tooltip_btn_random_action"))
        self.btn_random_config.setToolTip(self.config.get_message("tooltip_btn_random_config"))
        self.lbl_desktop_icon.setToolTip(self.config.get_message("tooltip_show_desktop"))
        self.chk_desktop.setToolTip(self.config.get_message("tooltip_chk_desktop"))
        
        # 5. Params
        self.lbl_clicks_icon.setToolTip(self.config.get_message("tooltip_clicks_icon"))
        self.edit_clicks.setToolTip(self.config.get_message("tooltip_clicks_icon"))
        self.lbl_interval_icon.setToolTip(self.config.get_message("tooltip_interval_icon"))
        self.edit_interval.setToolTip(self.config.get_message("tooltip_interval_icon"))
        
        # 6. Notes (With Placeholder)
        self.edit_notes.setPlaceholderText(self.config.get_message("placeholder_notes"))
        self.edit_notes.setToolTip(self.config.get_message("tooltip_edit_notes"))
        self.btn_notes_edit.setToolTip(self.config.get_message("tooltip_btn_notes_edit"))

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
        self.chk_random.setEnabled(enabled)
        self.btn_random_toggle.setEnabled(enabled and self.chk_random.isChecked())
        self.btn_random_config.setEnabled(enabled and self.chk_random.isChecked())
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
