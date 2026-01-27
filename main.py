import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # Handle DPI Scaling for Windows
    if os.name == 'nt':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
        
    app = QApplication(sys.argv)
    app.setApplicationName("Flow Track")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
