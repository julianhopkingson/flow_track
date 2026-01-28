import os
import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QScrollArea, 
                             QTextEdit, QFrame, QFileDialog, QMessageBox, QStyledItemDelegate)
from PySide6.QtCore import Qt, QTimer, QSize, QObject, QEvent
from PySide6.QtGui import QIcon, QTextCursor
import qtawesome as qta
import win32api

from core.config_manager import ConfigManager
from core.timer_engine import TimerEngine
from ui.components.timer_card import TimerCard
from ui.styles.theme_config import ThemeManager

class CenterAlignmentDelegate(QStyledItemDelegate):
    """Delegate to center align text in QComboBox (v11.0)."""
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignCenter
        super().paint(painter, option, index)

class LineEditClickFilter(QObject):
    """Filter to pass clicks from read-only line edit to combo box popup."""
    def __init__(self, combo):
        super().__init__(combo)
        self.combo = combo
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            if self.combo.view().isVisible():
                self.combo.hidePopup()
            else:
                self.combo.showPopup()
            return True
        return super().eventFilter(obj, event)

class ThemeButtonHoverFilter(QObject):
    """Filter to change Sun icon color on hover (Light Mode only) (v2.3)."""
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window

    def eventFilter(self, obj, event):
        if self.mw.theme_manager.current_theme == "Light":
            if event.type() == QEvent.Enter:
                # Hover: Gold Sun
                icon = self.mw._draw_sun_icon(QSize(32, 32), '#F6AD55') # Gold/Orange
                self.mw.btn_theme.setIcon(icon)
            elif event.type() == QEvent.Leave:
                # Normal: Green Sun
                icon = self.mw._draw_sun_icon(QSize(32, 32), '#26D07C') # Green
                self.mw.btn_theme.setIcon(icon)
        return super().eventFilter(obj, event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.theme_manager = ThemeManager()
        self.theme_manager.current_theme = self.config.theme

        self.engine = TimerEngine(config=self.config)
        self.timer_cards = []

        self.setWindowTitle(self.config.get_message("app_title"))
        
        # --- LOGO FIX ---
        icon_path = self.config.get_resource_path("assets/flow-track.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(self.config.window_width, self.config.window_height)
        if self.config.window_x is not None and self.config.window_y is not None:
            self.move(self.config.window_x, self.config.window_y)

        self.init_ui()
        self.load_initial_data()
        self.change_language(self.config.selected_language)
        
        # Coordinate Polling
        self.coord_timer = QTimer(self)
        self.coord_timer.timeout.connect(self.update_coords)
        self.coord_timer.start(200)

        # Engine Signals
        self.engine.log_signal.connect(self.log)
        self.engine.task_finished.connect(self.on_task_finished)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10) # Tighter margins
        main_layout.setSpacing(10) # Balanced spacing (was 4, originally 20)

        # --- Header Card ---
        self.header_card = QFrame()
        self.header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(20) # Group spacing

        self.lbl_lang_sel = QLabel()
        self.lbl_lang_sel.setPixmap(qta.icon('fa5s.globe', color='#26D07C').pixmap(22, 22))
        self.combo_lang = QComboBox()
        self.combo_lang.setObjectName("combo_lang")
        self.combo_lang.setFixedHeight(31)
        self.combo_lang.setFixedWidth(90)
        # Structural Fix for Centering: Editable + ReadOnly LineEdit
        self.combo_lang.setEditable(True)
        self.combo_lang.lineEdit().setReadOnly(True)
        self.combo_lang.lineEdit().setAlignment(Qt.AlignCenter)
        self.combo_lang.lineEdit().installEventFilter(LineEditClickFilter(self.combo_lang)) # Fix: Click to open
        self.combo_lang.setItemDelegate(CenterAlignmentDelegate(self.combo_lang))
        
        self.combo_lang.addItems(["中文", "English"])
        self.combo_lang.setCurrentText(self.config.selected_language)
        self.combo_lang.currentTextChanged.connect(self.change_language)
        
        # 语言组：Icon + Combo
        lang_group = QHBoxLayout()
        lang_group.setSpacing(5)
        lang_group.addWidget(self.lbl_lang_sel)
        lang_group.addWidget(self.combo_lang)

        self.btn_load = QPushButton()
        self.btn_load.setFixedHeight(32) 
        self.btn_load.setFixedWidth(42)
        self.btn_load.setToolTip(self.config.get_message("button_load_config"))
        self.btn_load.clicked.connect(self.load_config_dialog)
        
        # 统一使用图标：fa5s.copy
        self.lbl_copy_range_sel = QLabel()
        self.lbl_copy_range_sel.setPixmap(qta.icon('fa5s.copy', color='#26D07C').pixmap(18, 18))
        
        self.combo_copy_range = QComboBox()
        self.combo_copy_range.setFixedHeight(31) 
        self.combo_copy_range.setFixedWidth(50)
        
        # Move Tooltip settings here, after combo_copy_range is created
        self.combo_lang.setToolTip(self.config.get_message("tooltip_combo_lang"))
        self.lbl_copy_range_sel.setToolTip(self.config.get_message("tooltip_copy_range_icon"))
        self.combo_copy_range.setToolTip(self.config.get_message("tooltip_copy_range_combo"))
        # Structural Fix for Centering
        self.combo_copy_range.setEditable(True)
        self.combo_copy_range.lineEdit().setReadOnly(True)
        self.combo_copy_range.lineEdit().setAlignment(Qt.AlignCenter)
        self.combo_copy_range.lineEdit().installEventFilter(LineEditClickFilter(self.combo_copy_range)) # Fix: Click to open
        self.combo_copy_range.setItemDelegate(CenterAlignmentDelegate(self.combo_copy_range))
        
        self.combo_copy_range.addItems([str(i) for i in range(1, 11)])
        self.combo_copy_range.setCurrentText(str(self.config.copy_range))
        self.combo_copy_range.currentTextChanged.connect(self.on_copy_range_changed)

        # 复制组：Icon + Combo
        copy_group = QHBoxLayout()
        copy_group.setSpacing(5)
        copy_group.addWidget(self.lbl_copy_range_sel)
        copy_group.addWidget(self.combo_copy_range)

        # 坐标组：Icon + Value (Background only on value)
        self.lbl_coord_icon = QLabel()
        self.lbl_coord_icon.setPixmap(qta.icon('fa5s.crosshairs', color='#E53E3E').pixmap(18, 18))
        self.lbl_coords = QLabel("(0, 0)")
        self.lbl_coords.setObjectName("CoordinateLabel")
        self.lbl_coords.setFixedHeight(31) # Align height with other header items (v10.8)
        self.lbl_coords.setFixedWidth(130) # Fixed width for consistency
        self.lbl_coords.setAlignment(Qt.AlignCenter) # Center text
        coord_group = QHBoxLayout()
        coord_group.setSpacing(5)
        coord_group.addWidget(self.lbl_coord_icon)
        coord_group.addWidget(self.lbl_coords)

        self.btn_start = QPushButton(self.config.get_message("button_start"))
        self.btn_start.setObjectName("ActionButton")
        self.btn_start.setProperty("type", "start")
        self.btn_start.clicked.connect(self.start_timers)

        self.btn_stop = QPushButton(self.config.get_message("button_stop"))
        self.btn_stop.setObjectName("ActionButton")
        self.btn_stop.setProperty("type", "stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.hide() 
        self.btn_stop.clicked.connect(self.stop_timers)

        # Theme Switcher (v1.0)
        self.btn_theme = QPushButton()
        self.btn_theme.setFixedSize(31, 31) # Circular
        self.btn_theme.setObjectName("IconButton")
        self.btn_theme.clicked.connect(self.toggle_theme)
        # Install hover filter for dynamic icon color (v2.3)
        self.btn_theme.installEventFilter(ThemeButtonHoverFilter(self))
        self.update_theme_icon()

        # Add to Coord Group (Position requirement)
        coord_group.addWidget(self.btn_theme)

        # 按组添加至主布局
        header_layout.addLayout(lang_group)
        header_layout.addWidget(self.btn_load)
        header_layout.addLayout(copy_group)
        header_layout.addLayout(coord_group) # Moved to left side
        header_layout.addStretch()
        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)

        # Initialize icons with correct colors (v9.7.2 Fix: Call after all components are defined)
        self.apply_theme()

        main_layout.addWidget(self.header_card)

        # --- Timer Workspace Card ---
        self.workspace_card = QFrame()
        self.workspace_card.setObjectName("TimerWorkspaceCard")
        workspace_layout = QVBoxLayout(self.workspace_card)
        workspace_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TimerScroll")
        
        self.timer_container = QWidget()
        self.timer_container.setObjectName("TimerContainer")
        self.timer_list_layout = QVBoxLayout(self.timer_container)
        self.timer_list_layout.setAlignment(Qt.AlignTop)
        self.timer_list_layout.setSpacing(2)
        
        scroll.setWidget(self.timer_container)
        workspace_layout.addWidget(scroll)
        
        main_layout.addWidget(self.workspace_card, 1)

        # --- Log Card ---
        self.log_card = QFrame()
        self.log_card.setObjectName("LogCard")
        log_inner_layout = QVBoxLayout(self.log_card)
        log_inner_layout.setContentsMargins(15, 10, 15, 10)
        log_inner_layout.setSpacing(5)

        self.lbl_log_header = QLabel(self.config.get_message("log"))
        self.lbl_log_header.setStyleSheet("font-weight: bold; color: #4A5568; font-size: 10pt;")
        log_inner_layout.addWidget(self.lbl_log_header)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFixedHeight(120)
        self.txt_log.setObjectName("LogText")
        log_inner_layout.addWidget(self.txt_log)
        
        main_layout.addWidget(self.log_card)

    def apply_theme(self):
        """Apply the global style theme (v1.0)."""
        template_path = self.config.get_resource_path("ui/styles/theme_template.qss")
        qss = self.theme_manager.get_qss(template_path)
        if qss:
            self.setStyleSheet(qss)
        
        # Apply Windows Title Bar Theme (v2.0)
        is_dark = self.theme_manager.current_theme == "Dark"
        self.theme_manager.set_title_bar_theme(self.winId(), is_dark)
        
        # Update dynamic icons
        self.update_header_icons(self.btn_start.isEnabled())
        self.update_theme_icon()
        for card in self.timer_cards:
            card.update_after_theme_change()

    def toggle_theme(self):
        new_theme = "Dark" if self.theme_manager.current_theme == "Light" else "Light"
        self.theme_manager.current_theme = new_theme
        self.config.theme = new_theme
        self.apply_theme()
        self.log(f"Theme changed to {new_theme}")

    def _draw_sun_icon(self, size, color):
        """Custom painted Sun icon based on user request (v2.1)."""
        from PySide6.QtGui import QPainter, QPen, QColor, QPixmap
        from PySide6.QtCore import QPoint
        
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Center and Radius calculation
        w, h = size.width(), size.height()
        center = QPoint(w // 2, h // 2) # Manual center calculation
        r = min(w, h) / 4 # Adjust radius ratio
        
        c = QColor(color)
        p.setPen(QPen(c, 1.5))
        p.setBrush(c) # Filled style (v2.2)
        
        # Draw central circle
        p.drawEllipse(center, r, r)
        
        # Draw rays
        p.translate(center)
        for _ in range(8):
            # Ray line segment relative to center (0,0)
            # Start just outside the circle, length 2-3px
            p.drawLine(0, -r-2, 0, -r-5) 
            p.rotate(45)
            
        p.end()
        return QIcon(pixmap)

    def update_theme_icon(self):
        is_light = self.theme_manager.current_theme == "Light"
        
        if is_light:
            # Custom Green Sun (Hollow + Rays)
            icon = self._draw_sun_icon(QSize(32, 32), '#26D07C')
            size = QSize(18, 18)
            # Light Mode Hover Effect (Gold/Warm Tone)
            self.btn_theme.setStyleSheet("""
                QPushButton {
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    background-color: #FFFFFF;
                }
                QPushButton:hover {
                    background-color: #FFFAF0;  /* Floral White (Light Gold) */
                    border: 1px solid #F6AD55;  /* Gold/Orange */
                }
            """)
        else:
            # Dark Mode: Blue Moon
            icon = qta.icon('fa5s.moon', color='#A3BFFA')
            size = QSize(18, 18)
            # Reset style to default (Standard IconButton QSS)
            self.btn_theme.setStyleSheet("")
            
        self.btn_theme.setIcon(icon)
        self.btn_theme.setIconSize(size)

    def load_initial_data(self):
        timers_data = self.config.timers_data
        if not timers_data:
            timers_data = [None] * 5
        
        for data in timers_data:
            self.add_timer_card(data)

    def add_timer_card(self, data=None, index=None):
        card = TimerCard(data=data, config=self.config)
        card.delete_requested.connect(self.delete_timer)
        card.insert_requested.connect(self.insert_timer)
        card.move_up_requested.connect(self.move_up)
        card.move_down_requested.connect(self.move_down)
        card.copy_requested.connect(self.copy_settings)
        
        if index is not None:
            self.timer_list_layout.insertWidget(index, card)
            self.timer_cards.insert(index, card)
        else:
            self.timer_list_layout.addWidget(card)
            self.timer_cards.append(card)

    def delete_timer(self, card):
        if len(self.timer_cards) <= 1: return
        self.timer_cards.remove(card)
        card.deleteLater()
        self.log(self.config.get_message("log_timer_row_deleted"))

    def insert_timer(self, card):
        idx = self.timer_cards.index(card)
        self.add_timer_card(index=idx + 1)
        self.log(self.config.get_message("log_timer_row_inserted"))

    def move_up(self, card):
        idx = self.timer_cards.index(card)
        if idx > 0:
            self.timer_cards.pop(idx)
            self.timer_cards.insert(idx - 1, card)
            self.refresh_list()

    def move_down(self, card):
        idx = self.timer_cards.index(card)
        if idx < len(self.timer_cards) - 1:
            self.timer_cards.pop(idx)
            self.timer_cards.insert(idx + 1, card)
            self.refresh_list()

    def refresh_list(self):
        # Remove all from layout then re-add
        for i in reversed(range(self.timer_list_layout.count())): 
            self.timer_list_layout.itemAt(i).widget().setParent(None)
        for card in self.timer_cards:
            self.timer_list_layout.addWidget(card)

    def copy_settings(self, source_card):
        idx = self.timer_cards.index(source_card)
        src_vals = source_card.get_values()
        copy_range = self.config.copy_range
        
        for i in range(1, copy_range + 1):
            target_idx = idx + i
            if target_idx < len(self.timer_cards):
                target_card = self.timer_cards[target_idx]
                
                # Calculate incrementing SS (Legacy HH:MM preserved, SS += offset)
                try:
                    h, m, s = int(src_vals['time'][0:2]), int(src_vals['time'][2:4]), int(src_vals['time'][4:6])
                    new_s = (s + i) % 60
                    new_time_str = f"{h:02d}{m:02d}{new_s:02d}"
                    
                    partial_data = {
                        "time": new_time_str,
                        "clicks": src_vals['clicks'] if not src_vals['show_desktop'] else None,
                        "interval": src_vals['interval'] if not src_vals['show_desktop'] else None
                    }
                    target_card.update_partial_values(partial_data)
                except:
                    pass

    def update_coords(self):
        try:
            pos = win32api.GetCursorPos()
            self.lbl_coords.setText(f"{pos}") # Value only
        except:
            pass

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{timestamp}] {message}")
        self.txt_log.moveCursor(QTextCursor.End)

    def start_timers(self):
        # v9.6: Update header icons color
        self.update_header_icons(False)
        # 1. Lock UI first to prevent double clicks (High priority in legacy parity)
        self.set_ui_locked(True)
        
        # 2. Start log
        self.log(self.config.get_message("log_timer_started"))
        
        tasks_info = []
        now = datetime.datetime.now()
        
        enabled_timers_indices = []
        for idx, card in enumerate(self.timer_cards):
            vals = card.get_values()
            if vals['enabled']:
                try:
                    t_str = vals['time']
                    scheduled_time = datetime.datetime.strptime(t_str, "%H%M%S")
                    scheduled_time = now.replace(hour=scheduled_time.hour, minute=scheduled_time.minute, second=scheduled_time.second, microsecond=0)
                    
                    if scheduled_time < now:
                        # Exact legacy message key: log_timer_time_passed
                        self.log(self.config.get_message("log_timer_time_passed", timer_no=idx+1))
                        continue
                    
                    enabled_timers_indices.append((idx, scheduled_time))
                except Exception as e:
                    self.log(f"Error Timer {idx+1}: {str(e)}")

        if not enabled_timers_indices:
            # Exact legacy message key: error_no_valid_timer
            self.log(self.config.get_message("error_no_valid_timer"))
            self.stop_timers() # This will unlock the UI
            return

        # Figure out which is the last timer to execute based on scheduled time
        last_scheduled = max(item[1] for item in enabled_timers_indices)
        
        for idx, scheduled_time in enabled_timers_indices:
            card = self.timer_cards[idx]
            vals = card.get_values()
            tasks_info.append({
                "timer_no": idx + 1,
                "scheduled_time": scheduled_time,
                "show_desktop": vals['show_desktop'],
                "x": int(vals['x']) if vals['x'] and not vals['show_desktop'] else 0,
                "y": int(vals['y']) if vals['y'] and not vals['show_desktop'] else 0,
                "clicks": int(vals['clicks']) if vals['clicks'] and not vals['show_desktop'] else 1,
                "interval": float(vals['interval']) if vals['interval'] and not vals['show_desktop'] else 1.0,
                "paste_text": vals['paste_text'] if not vals['show_desktop'] else "",
                "is_last": scheduled_time == last_scheduled
            })

        self.engine.start_tasks(tasks_info)

    def stop_timers(self):
        # v9.6: Update header icons color
        self.update_header_icons(True)
        self.engine.stop_all()
        self.set_ui_locked(False)
        self.log(self.config.get_message("log_stop_all_timer"))

    def on_task_finished(self, timer_no, is_last):
        if is_last:
            if self.config.auto_close_enabled:
                self.log(self.config.get_message("log_autoclose_countdown", delay=self.config.auto_close_delay_seconds))
                QTimer.singleShot(self.config.auto_close_delay_seconds * 1000, self.auto_close_procedure)
            else:
                self.set_ui_locked(False)

    def auto_close_procedure(self):
        self.log(self.config.get_message("log_autoclose_closing"))
        self.close()

    def set_ui_locked(self, locked):
        self.btn_start.setEnabled(not locked)
        self.btn_start.setVisible(not locked)
        self.btn_stop.setEnabled(locked)
        self.btn_stop.setVisible(locked)
        
        self.btn_load.setEnabled(not locked)
        self.combo_lang.setEnabled(not locked)
        self.combo_copy_range.setEnabled(not locked)
        for card in self.timer_cards:
            card.set_editing_enabled(not locked)

    def change_language(self, lang):
        self.config.selected_language = lang
        self.setWindowTitle(self.config.get_message("app_title"))
        # Update all labels
        self.btn_load.setToolTip(self.config.get_message("tooltip_btn_load_config"))
        self.btn_start.setText(self.config.get_message("button_start"))
        self.btn_stop.setText(self.config.get_message("button_stop"))
        self.lbl_lang_sel.setToolTip(self.config.get_message("tooltip_lang_sel"))
        self.combo_lang.setToolTip(self.config.get_message("tooltip_combo_lang"))
        self.lbl_copy_range_sel.setToolTip(self.config.get_message("tooltip_copy_range_icon"))
        self.combo_copy_range.setToolTip(self.config.get_message("tooltip_copy_range_combo"))
        self.lbl_coord_icon.setToolTip(self.config.get_message("tooltip_coord_icon"))
        self.lbl_coords.setToolTip(self.config.get_message("tooltip_coords"))
        self.btn_start.setToolTip(self.config.get_message("tooltip_btn_start"))
        self.btn_stop.setToolTip(self.config.get_message("tooltip_btn_stop"))
        self.lbl_log_header.setText(self.config.get_message("log"))
        
        # New: Retranslate all cards
        for card in self.timer_cards:
            card.retranslate_ui()
            
        self.log(f"Language changed to {lang}")

    def on_copy_range_changed(self, val):
        self.config.copy_range = int(val)

    def update_header_icons(self, active):
        """Update header icons (Language, Copy Range, Folder) based on app running state (v9.7.1 Plan A)."""
        color_active = self.theme_manager.get_color("ICON_COLOR")
        color_muted = self.theme_manager.get_color("ICON_COLOR_MUTED")
        
        color_lang = color_active if active else color_muted
        color_copy = color_active if active else color_muted
        color_folder = color_active if active else color_muted
        
        # 1. Labels (Direct Pixmap)
        self.lbl_lang_sel.setPixmap(qta.icon('fa5s.globe', color=color_lang).pixmap(22, 22))
        self.lbl_copy_range_sel.setPixmap(qta.icon('fa5s.copy', color=color_copy).pixmap(18, 18))
        
        # 2. Folder Button (Plan A: Force Disable Stage transparency override)
        pix = qta.icon('fa5s.folder-open', color=color_folder).pixmap(20, 20)
        icon = QIcon()
        icon.addPixmap(pix, QIcon.Normal)
        icon.addPixmap(pix, QIcon.Disabled)
        self.btn_load.setIcon(icon)
        self.btn_load.setIconSize(QSize(20, 20))

    def load_config_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.config.get_message("tooltip_btn_load_config"), "", "INI Files (*.ini)")
        if file_path:
            import configparser
            temp_config = configparser.ConfigParser()
            try:
                temp_config.read(file_path, encoding="utf-8")
                self.config.app_config = temp_config
                self.config.load_app_config(read_default_file=False)
                # Clear and Reload (Explicit Layout Clearing to fix refresh bug)
                while self.timer_list_layout.count():
                    item = self.timer_list_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                
                self.timer_cards = []
                self.load_initial_data()
                self.log(self.config.get_message("log_config_loaded", filename=os.path.basename(file_path)))
                self.combo_lang.setCurrentText(self.config.selected_language)
                self.change_language(self.config.selected_language)
            except Exception as e:
                self.log(f"Error loading config: {str(e)}")

    def closeEvent(self, event):
        # Stop engine first
        self.engine.stop_all()
        geo = {
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height()
        }
        timers_list = [card.get_values() for card in self.timer_cards]
        self.config.save_config(window_geo=geo, timers_list=timers_list)
        super().closeEvent(event)
