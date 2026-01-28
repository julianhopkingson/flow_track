from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLabel, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import qtawesome as qta
import os

class NotesEditorDialog(QDialog):
    """
    Modal dialog for editing long notes.
    Designed per Feature_Design_Modal_Editor_v1.md.
    """
    def __init__(self, current_text, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.result_text = current_text
        
        self.setWindowTitle(self.config.get_message("title_edit_note"))
        self.setFixedSize(500, 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Apply theme manually since Dialogs might miss global styling sometimes
        self.setStyleSheet("""
            QDialog { background-color: #F7FAFC; }
            QTextEdit { 
                border: 1px solid #E2E8F0; 
                border-radius: 8px; 
                background: #FFFFFF;
                padding: 10px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 14px;
                color: #2D3748;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Editor Area
        self.editor = QTextEdit()
        self.editor.setPlainText(current_text)
        self.editor.setPlaceholderText("Enter your notes here...")
        layout.addWidget(self.editor)

        # Button Box
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton(self.config.get_message("btn_cancel"))
        self.btn_cancel.setStyleSheet("""
            QPushButton { 
                background-color: #CBD5E0; 
                color: #4A5568; 
                border: 1px solid #CBD5E0;
            }
            QPushButton:hover { background-color: #A0AEC0; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton(self.config.get_message("btn_save"))
        self.btn_save.setStyleSheet("""
            QPushButton { 
                background-color: #10B981; 
                color: white; 
                border: 1px solid #10B981;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_save.clicked.connect(self.save)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)

    def save(self):
        # Feature Design 4.1 R1: Adjusted - Preserve newlines for rich text pasting
        self.result_text = self.editor.toPlainText()
        self.accept()

    def get_text(self):
        return self.result_text
