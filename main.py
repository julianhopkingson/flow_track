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

def check_autostart_schedule_guard() -> bool:
    """
    开机自启动静默守门检查：
    若由开机参数 --autostart 拉起，且今日未在用户设定的排程运行日中，直接返回 False 以触发秒级静默退出。
    """
    if "--autostart" not in sys.argv:
        return True  # 用户手动双击打开，放行
        
    try:
        import datetime
        from core.config_manager import ConfigManager
        config = ConfigManager()
        today_idx = datetime.datetime.now().weekday()  # 0:周一 ... 6:周日
        days_list = config.autostart_days
        
        # 判定今日是否在排程运行列表中
        if today_idx < len(days_list) and not days_list[today_idx]:
            return False  # 今日非排程日，拦截退出
    except Exception as e:
        # 异常兜底：若读取配置失败，安全放行
        print(f"[AutostartGuard] Error checking schedule: {e}")
        return True
        
    return True

def main():
    global _app_mutex
    
    # 0. 锁定工作目录至可执行文件或脚本物理所在目录（根治 Windows 注册表自启动默认 CWD 漂移至 System32 问题）
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    
    # 1. 开机排程守门：非设定运行日直接秒级退出，不初始化任何 UI 与互斥锁
    if not check_autostart_schedule_guard():
        sys.exit(0)
    
    # 2. 关键步骤：在加载任何UI前创建命名互斥锁
    # GUID 保证全局唯一性: {9D2A3B4C-FlowTrack-Mutex-v2.3}
    mutex_name = "Local\\FlowTrack_Instance_Mutex_9D2A3B4C-v2.3"
    
    # CreateMutex(security_attributes, initial_owner, name)
    _app_mutex = win32event.CreateMutex(None, False, mutex_name)
    last_error = win32api.GetLastError()
    
    # 3. Check: If mutex already exists, an instance is running
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
