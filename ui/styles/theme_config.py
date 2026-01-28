import re
import os
from PySide6.QtGui import QColor, QFontDatabase
import qtawesome as qta
import ctypes
from ctypes import wintypes
import sys

class ThemeManager:
    THEMES = {
        "Light": {
            "BG_WINDOW": "#EDF2F7",
            "BG_CARD": "#F8FAFC",
            "BG_ITEM": "#FFFFFF",
            "BORDER_LIGHT": "#FFFFFF",
            "BORDER_SHADOW": "#CBD5E0",
            "TEXT_PRIMARY": "#1A202C",
            "TEXT_SECONDARY": "#4A5568",
            "ACCENT_GREEN": "#26D07C",
            "ACCENT_RED": "#E53E3E",
            "ACCENT_ORANGE": "#ED8936",
            "ACCENT_GRAY": "#718096",
            "INPUT_BORDER": "#E2E8F0",
            "CHECKBOX_BG": "#FFFFFF",
            "CHECKBOX_RING": "#FFFFFF",
            "BG_COORD": "#E2FBEB",        # Restore original pale green
            "ICON_COLOR": "#26D07C",      # Main active icon color
            "ICON_COLOR_ALT": "#4A5568",  # Alt buttons (up/down)
            "ICON_COLOR_MUTED": "#CBD5E0" # Disabled/Locked color
        },
        "Dark": {
            "BG_WINDOW": "#0F172A",
            "BG_CARD": "#1E293B",
            "BG_ITEM": "#334155",
            "BORDER_LIGHT": "#334155",
            "BORDER_SHADOW": "#020617",
            "TEXT_PRIMARY": "#F8FAFC",
            "TEXT_SECONDARY": "#94A3B8",
            "ACCENT_GREEN": "#22C55E",
            "ACCENT_RED": "#F87171",
            "ACCENT_ORANGE": "#F59E0B",
            "ACCENT_GRAY": "#64748B",
            "INPUT_BORDER": "#475569",
            "CHECKBOX_BG": "#1E293B",
            "CHECKBOX_RING": "#F8FAFC",
            "BG_COORD": "#14532D",        # Dark Green for dark mode
            "ICON_COLOR": "#22C55E",      # Vibrant green for dark mode
            "ICON_COLOR_ALT": "#94A3B8",
            "ICON_COLOR_MUTED": "#475569"
        }
    }

    _instance = None
    _current_theme = "Light"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
        return cls._instance

    @property
    def current_theme(self):
        return self._current_theme

    @current_theme.setter
    def current_theme(self, value):
        if value in self.THEMES:
            self._current_theme = value

    def get_color(self, key):
        return self.THEMES[self._current_theme].get(key, "#000000")

    def get_qss(self, template_path):
        """Read template and inject current theme colors."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            theme = self.THEMES[self._current_theme]
            for key, value in theme.items():
                template = template.replace(f"[[{key}]]", value)
                
            return template
        except Exception as e:
            print(f"Error loading QSS template: {e}")
            return ""

    @staticmethod
    def set_title_bar_theme(win_id, is_dark):
        """
        Uses Windows DWM API to switch title bar color.
        win_id: PySide6/Qt window ID (int or WId)
        is_dark: Boolean
        """
        if sys.platform != "win32":
            return
            
        try:
            hwnd = int(win_id)
            dwmapi = ctypes.windll.dwmapi
            
            # 1. Immersive Dark Mode (Classic approach for Win10+)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            val_dark = ctypes.c_int(1 if is_dark else 0)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val_dark), ctypes.sizeof(val_dark))

            # 2. Custom Caption Color (Windows 11 Build 22000+)
            # Target Dark: #0B192C (RGB: 11, 25, 44) -> COLORREF: 0x002C190B (BGR)
            DWMWA_CAPTION_COLOR = 35
            # DWMWA_TEXT_COLOR = 36
            DWMWA_COLOR_DEFAULT = 0xFFFFFFFF
            
            if is_dark:
                color_ref = 0x002C190B # #0B192C
            else:
                color_ref = DWMWA_COLOR_DEFAULT
                
            val_color = ctypes.c_int(color_ref)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(val_color), ctypes.sizeof(val_color))
            
        except Exception as e:
            # Attribute 35 might fail on older Windows 10, which is fine (graceful degradation)
            # print(f"Failed to set title bar theme: {e}") 
            pass
