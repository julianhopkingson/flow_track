import os
import sys
import configparser

class ConfigManager:
    LANGUAGE_FILE = "assets/language.ini"
    CONFIG_FILE = "config/config.ini"

    def __init__(self):
        self.lang_config = configparser.ConfigParser()
        self.app_config = configparser.ConfigParser()
        self.selected_language = "中文"
        
        # Default settings
        self.window_x = None
        self.window_y = None
        self.window_width = 800
        self.window_height = 600
        self.timer_canvas_height = 200
        self.copy_range = 7
        self.auto_close_enabled = False
        self.auto_close_delay_seconds = 10
        self.timers_data = []

        self.load_language()
        self.load_app_config()

    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def load_language(self):
        lang_path = self.get_resource_path(self.LANGUAGE_FILE)
        if os.path.exists(lang_path):
            self.lang_config.read(lang_path, encoding="utf-8")

    def get_lang_texts(self):
        if self.selected_language in self.lang_config:
            return dict(self.lang_config[self.selected_language])
        return {}

    def get_message(self, key, **kwargs):
        texts = self.get_lang_texts()
        template = texts.get(key, key)
        try:
            return template.format(**kwargs)
        except:
            return template

    def load_app_config(self):
        if os.path.exists(self.CONFIG_FILE):
            self.app_config.read(self.CONFIG_FILE, encoding="utf-8")
        
        # Ensure General section exists
        if not self.app_config.has_section("General"):
            self.app_config.add_section("General")

        self.selected_language = self.app_config.get("General", "language", fallback="中文")
        self.window_x = self.app_config.getint("General", "window_x", fallback=None)
        self.window_y = self.app_config.getint("General", "window_y", fallback=None)
        self.window_width = self.app_config.getint("General", "window_width", fallback=800)
        self.window_height = self.app_config.getint("General", "window_height", fallback=600)
        self.timer_canvas_height = self.app_config.getint("General", "timer_canvas_height", fallback=200)
        self.copy_range = self.app_config.getint("General", "copy_range", fallback=7)
        self.auto_close_enabled = self.app_config.getboolean("General", "auto_close_enabled", fallback=False)
        self.auto_close_delay_seconds = self.app_config.getint("General", "auto_close_delay_seconds", fallback=10)

        self.timers_data = []
        # Clear existing Timer_ sections to rebuild cleanly if needed, 
        # but here we load them for the initial UI
        for section in self.app_config.sections():
            if section.startswith("Timer_"):
                data = {
                    "enabled": self.app_config.getboolean(section, "enabled", fallback=False),
                    "x": self.app_config.get(section, "x", fallback=""),
                    "y": self.app_config.get(section, "y", fallback=""),
                    "time": self.app_config.get(section, "time", fallback="000000"),
                    "show_desktop": self.app_config.getboolean(section, "show_desktop", fallback=False),
                    "clicks": self.app_config.get(section, "clicks", fallback="1"),
                    "interval": self.app_config.get(section, "interval", fallback="1"),
                    "paste_text": self.app_config.get(section, "paste_text", fallback="")
                }
                self.timers_data.append(data)

    def save_config(self, window_geo=None, timers_list=None):
        # Update General section in self.app_config
        self.app_config.set("General", "language", self.selected_language)
        self.app_config.set("General", "copy_range", str(self.copy_range))
        self.app_config.set("General", "auto_close_enabled", str(self.auto_close_enabled).lower())
        self.app_config.set("General", "auto_close_delay_seconds", str(self.auto_close_delay_seconds))
        self.app_config.set("General", "timer_canvas_height", str(self.timer_canvas_height))
        
        if window_geo:
            self.app_config.set("General", "window_x", str(window_geo.get('x', '')))
            self.app_config.set("General", "window_y", str(window_geo.get('y', '')))
            self.app_config.set("General", "window_width", str(window_geo.get('width', '')))
            self.app_config.set("General", "window_height", str(window_geo.get('height', '')))
        
        # Clear old Timer_ sections to avoid leftovers if count decreased
        for section in self.app_config.sections():
            if section.startswith("Timer_"):
                self.app_config.remove_section(section)

        if timers_list:
            for idx, timer in enumerate(timers_list):
                section = f"Timer_{idx}"
                self.app_config.add_section(section)
                self.app_config.set(section, "enabled", "1" if timer.get('enabled') else "0")
                self.app_config.set(section, "x", str(timer.get('x', '')))
                self.app_config.set(section, "y", str(timer.get('y', '')))
                self.app_config.set(section, "time", str(timer.get('time', '000000')))
                self.app_config.set(section, "show_desktop", "1" if timer.get('show_desktop') else "0")
                self.app_config.set(section, "clicks", str(timer.get('clicks', '1')))
                self.app_config.set(section, "interval", str(timer.get('interval', '1')))
                self.app_config.set(section, "paste_text", timer.get('paste_text', ''))

        config_dir = os.path.dirname(self.CONFIG_FILE)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            self.app_config.write(f)
