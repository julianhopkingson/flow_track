import time
import datetime
import threading
import win32api
import win32con
import pyperclip
from PySide6.QtCore import QObject, Signal, QThread

class TimerWorker(QObject):
    finished = Signal(int, bool)  # timer_no, is_last
    log = Signal(str)
    error = Signal(int, str) # timer_no, error_msg

    def __init__(self, timer_data, config=None):
        super().__init__()
        self.data = timer_data
        self.config = config
        self._is_running = True
        self.cancel_event = threading.Event()

    def get_msg(self, key, **kwargs):
        if self.config:
            return self.config.get_message(key, **kwargs)
        return key

    def stop(self):
        self._is_running = False
        self.cancel_event.set()

    def run_task(self):
        timer_no = self.data['timer_no']
        scheduled_time = self.data['scheduled_time']
        show_desktop = self.data['show_desktop']
        is_last = self.data.get('is_last', False)
        
        # --- Wait logic (Legacy Parity) ---
        mode_log_key = "log_timer_mode_desktop" if show_desktop else "log_timer_mode_clickpaste"
        self.log.emit(self.get_msg(mode_log_key, timer_no=timer_no))

        while not self.cancel_event.is_set():
            now = datetime.datetime.now()
            wait_seconds = (scheduled_time - now).total_seconds()
            if wait_seconds <= 0:
                break
            
            self.log.emit(self.get_msg("log_timer_wait", timer_no=timer_no, seconds=int(wait_seconds)))
            
            # Legacy adaptive sleep algorithm
            sleep_duration = 0.5
            if wait_seconds > 15: sleep_duration = 10
            if wait_seconds > 60: sleep_duration = 30
            if wait_seconds > 660: sleep_duration = max(int(wait_seconds / 10) - 60, 600)
            
            self.cancel_event.wait(min(sleep_duration, wait_seconds))

        if self.cancel_event.is_set():
            self.log.emit(self.get_msg("log_timer_cancel", timer_no=timer_no))
            self.finished.emit(timer_no, False)
            return

        # --- Execution logic (Legacy Parity) ---
        try:
            if show_desktop:
                self.log.emit(self.get_msg("log_timer_show_desktop", timer_no=timer_no))
                win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
                win32api.keybd_event(ord('D'), 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(ord('D'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)
                self.log.emit(self.get_msg("log_timer_show_desktop_done", timer_no=timer_no))
            else:
                self.log.emit(self.get_msg("log_timer_begin", timer_no=timer_no))
                x, y = self.data['x'], self.data['y']
                clicks = self.data['clicks']
                interval = self.data['interval']
                paste_text = self.data['paste_text']
                
                for i in range(clicks):
                    if self.cancel_event.is_set(): 
                        self.log.emit(self.get_msg("error_timer_click_interrupt", timer_no=timer_no))
                        break
                    
                    win32api.SetCursorPos((x, y))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                    self.log.emit(self.get_msg("log_timer_click", timer_no=timer_no, count=i + 1))
                    
                    if paste_text:
                        self.log.emit(self.get_msg("log_timer_paste_begin", timer_no=timer_no))
                        pyperclip.copy(paste_text)
                        time.sleep(0.1)
                        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                        self.log.emit(self.get_msg("log_timer_paste_completed", timer_no=timer_no))
                    
                    if i < clicks - 1:
                        time.sleep(interval)
                
                self.log.emit(self.get_msg("log_timer_completed", timer_no=timer_no))
        except Exception as e:
            self.error.emit(timer_no, str(e))
        
        self.finished.emit(timer_no, is_last)

class TimerEngine(QObject):
    log_signal = Signal(str)
    task_finished = Signal(int, bool) # timer_no, is_last

    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.threads = []
        self.workers = []

    def start_tasks(self, tasks_info):
        self.stop_all()
        
        if not tasks_info:
            return

        for info in tasks_info:
            thread = QThread()
            worker = TimerWorker(info, self.config)
            worker.moveToThread(thread)
            
            thread.started.connect(worker.run_task)
            worker.finished.connect(thread.quit)
            worker.finished.connect(self.task_finished.emit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            
            worker.log.connect(self.log_signal.emit)
            worker.error.connect(lambda t_no, msg: self.log_signal.emit(f"Error Timer {t_no}: {msg}"))
            
            self.threads.append(thread)
            self.workers.append(worker)
            thread.start()

    def stop_all(self):
        for worker in self.workers:
            worker.stop()
        for thread in self.threads:
            thread.quit()
            thread.wait()
        self.threads = []
        self.workers = []
