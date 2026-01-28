from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLabel, QMessageBox,
                             QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor
import qtawesome as qta
import os

class NotesEditorDialog(QDialog):
    """
    Modal dialog for editing long notes.
    Redesigned (v16.0) with Elevated Card & Action Buttons.
    """
    def __init__(self, current_text, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.result_text = current_text
        
        self.setWindowTitle(self.config.get_message("title_edit_note"))
        self.setFixedSize(520, 380) # Increased slightly for shadow margin
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setObjectName("NotesEditorDialog")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Raised Card Container for Editor
        self.card_frame = QFrame()
        self.card_frame.setObjectName("NotesEditorCard")
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(2, 2, 2, 2) # Inner breathing room
        
        # Apply Graphics Shadow for Elevation
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40)) # Subtle elevation shadow
        self.card_frame.setGraphicsEffect(shadow)

        # 2. Text Editor
        self.editor = QTextEdit()
        self.editor.setObjectName("NotesEditorField")
        self.editor.setPlainText(current_text)
        self.editor.setPlaceholderText(self.config.get_message("placeholder_notes") + "...")
        card_layout.addWidget(self.editor)
        
        layout.addWidget(self.card_frame)

        # 3. Action Buttons (Reusing ActionButton styles)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton(self.config.get_message("btn_cancel"))
        self.btn_cancel.setObjectName("ActionButton")
        self.btn_cancel.setProperty("type", "cancel") # Custom property for style
        self.btn_cancel.setFixedSize(120, 42)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton(self.config.get_message("btn_save"))
        self.btn_save.setObjectName("ActionButton")
        self.btn_save.setProperty("type", "start") # Reusing Aurora Green from Start button
        self.btn_save.setFixedSize(120, 42)
        self.btn_save.clicked.connect(self.save)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)

    def save(self):
        self.result_text = self.editor.toPlainText()
        self.accept()

    def get_text(self):
        return self.result_text
