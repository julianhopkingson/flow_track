import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# [v2.2] Single Instance Mechanism (Lead Architect Design)
import win32event
import win32api
import winerror

# Global mutex reference to prevent GC
_app_mutex = None

def main():
    global _app_mutex
    
    # 1. Critical: Create Named Mutex before any UI loading
    # GUID ensures global uniqueness: {9D2A3B4C-FlowTrack-Mutex-v2.2}
    mutex_name = "Local\\FlowTrack_Instance_Mutex_9D2A3B4C-v2.2"
    
    # CreateMutex(security_attributes, initial_owner, name)
    _app_mutex = win32event.CreateMutex(None, False, mutex_name)
    last_error = win32api.GetLastError()
    
    # 2. Check: If mutex already exists, an instance is running
    if last_error == winerror.ERROR_ALREADY_EXISTS:
        # Silent exit: prevent multiple windows from piling up
        sys.exit(0)

    # 3. Handle DPI Scaling for Windows
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
