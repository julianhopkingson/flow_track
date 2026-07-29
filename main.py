import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# [v2.3] 单例运行机制 (首席架构师设计)
import win32event
import win32api
import winerror

# 全局互斥锁对象引用，防止被垃圾回收
_app_mutex = None

def main():
    global _app_mutex
    
    # 1. 关键步骤：在加载任何UI前创建命名互斥锁
    # GUID 保证全局唯一性: {9D2A3B4C-FlowTrack-Mutex-v2.3}
    mutex_name = "Local\\FlowTrack_Instance_Mutex_9D2A3B4C-v2.3"
    
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
