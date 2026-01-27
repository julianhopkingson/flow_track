import os
import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QScrollArea, 
                             QTextEdit, QFrame, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QTextCursor
import qtawesome as qta
import win32api

from core.config_manager import ConfigManager
from core.timer_engine import TimerEngine
from ui.components.timer_card import TimerCard

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
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
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["中文", "English"])
        self.combo_lang.setCurrentText(self.config.selected_language)
        self.combo_lang.currentTextChanged.connect(self.change_language)
        
        self.btn_load = QPushButton(qta.icon('fa5s.folder-open'), "")
        self.btn_load.setToolTip(self.config.get_message("button_load_config"))
        self.btn_load.clicked.connect(self.load_config_dialog)

        self.combo_copy_range = QComboBox()
        self.combo_copy_range.addItems([str(i) for i in range(1, 11)])
        self.combo_copy_range.setCurrentText(str(self.config.copy_range))
        self.combo_copy_range.currentTextChanged.connect(self.on_copy_range_changed)

        self.lbl_coords = QLabel("Coords: (0, 0)")
        self.lbl_coords.setObjectName("CoordinateLabel") # For QSS

        self.btn_start = QPushButton(self.config.get_message("button_start"))
        self.btn_start.setObjectName("ActionButton")
        self.btn_start.clicked.connect(self.start_timers)

        self.btn_stop = QPushButton(self.config.get_message("button_stop"))
        self.btn_stop.setObjectName("ActionButton")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_timers)

        self.lbl_lang_sel = QLabel(self.config.get_message("label_option_language"))
        header_layout.addWidget(self.lbl_lang_sel)
        header_layout.addWidget(self.combo_lang)
        header_layout.addWidget(self.btn_load)
        self.lbl_copy_range_sel = QLabel(self.config.get_message("label_copy_range"))
        header_layout.addWidget(self.lbl_copy_range_sel)
        header_layout.addWidget(self.combo_copy_range)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_coords)
        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)

        main_layout.addLayout(header_layout)

        # --- Timer List Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("TimerScroll")
        
        self.timer_container = QWidget()
        self.timer_list_layout = QVBoxLayout(self.timer_container)
        self.timer_list_layout.setAlignment(Qt.AlignTop)
        self.timer_list_layout.setSpacing(5)
        
        scroll.setWidget(self.timer_container)
        main_layout.addWidget(scroll, 1)

        # --- Log Panel ---
        log_layout = QVBoxLayout()
        self.lbl_log_header = QLabel(self.config.get_message("log"))
        log_layout.addWidget(self.lbl_log_header)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFixedHeight(120)
        self.txt_log.setStyleSheet("background: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; padding: 5px;")
        log_layout.addWidget(self.txt_log)
        
        main_layout.addLayout(log_layout)

        # Apply Global Style
        style_path = self.config.get_resource_path("ui/styles/theme.qss")
        try:
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except:
            pass

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
            self.lbl_coords.setText(f"{self.config.get_message('label_coordinate')} {pos}")
        except:
            pass

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{timestamp}] {message}")
        self.txt_log.moveCursor(QTextCursor.End)

    def start_timers(self):
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
        self.btn_stop.setEnabled(locked)
        self.btn_load.setEnabled(not locked)
        self.combo_lang.setEnabled(not locked)
        self.combo_copy_range.setEnabled(not locked)
        for card in self.timer_cards:
            card.set_editing_enabled(not locked)

    def change_language(self, lang):
        self.config.selected_language = lang
        self.setWindowTitle(self.config.get_message("app_title"))
        # Update all labels
        self.btn_load.setToolTip(self.config.get_message("button_load_config"))
        self.btn_start.setText(self.config.get_message("button_start"))
        self.btn_stop.setText(self.config.get_message("button_stop"))
        self.lbl_lang_sel.setText(self.config.get_message("label_option_language"))
        self.lbl_copy_range_sel.setText(self.config.get_message("label_copy_range"))
        self.lbl_log_header.setText(self.config.get_message("log"))
        
        # New: Retranslate all cards
        for card in self.timer_cards:
            card.retranslate_ui()
            
        self.log(f"Language changed to {lang}")

    def on_copy_range_changed(self, val):
        self.config.copy_range = int(val)

    def load_config_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.config.get_message("button_load_config"), "", "INI Files (*.ini)")
        if file_path:
            import configparser
            temp_config = configparser.ConfigParser()
            try:
                temp_config.read(file_path, encoding="utf-8")
                self.config.app_config = temp_config
                self.config.load_app_config()
                # Clear and Reload
                for card in self.timer_cards: card.deleteLater()
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
