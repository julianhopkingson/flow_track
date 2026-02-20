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
        # 方案 C: 不需要做任何额外操作。cancel_event 会立刻打断所有的 wait() 阻塞。

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
            # 方案 C: 削减冗余跨线程信号，防止死锁
            # 取消时仅发必须要发的日志，不发 finished(.., False) 以外的多余信号
            self.log.emit(self.get_msg("log_timer_cancel", timer_no=timer_no))
            self.finished.emit(timer_no, False)
            return

        # --- Execution logic (Legacy Parity) ---
        try:
            if show_desktop:
                self.log.emit(self.get_msg("log_timer_show_desktop", timer_no=timer_no))
                win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
                win32api.keybd_event(ord('D'), 0, 0, 0)
                
                # 方案 C: 将微秒级 time.sleep 也替换为等效的 wait(), 并允许一键击穿
                if self.cancel_event.wait(0.05): return
                
                win32api.keybd_event(ord('D'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                if self.cancel_event.wait(0.5): return
                
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
                        
                        # 微步休眠
                        if self.cancel_event.wait(0.1): break
                        
                        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                        self.log.emit(self.get_msg("log_timer_paste_completed", timer_no=timer_no))
                    
                    if i < clicks - 1:
                        # 方案 C 核心：将致命的 time.sleep(interval) 升级为可瞬间打断的微步轮询
                        if self.cancel_event.wait(interval):
                            self.log.emit(self.get_msg("log_timer_cancel", timer_no=timer_no))
                            break
                
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
        # 方案 C: 废弃线程接管池 (Zombie Trap Safe-house)
        # 引用保留，以免底层 C++ QThread 被 Python GC 过早误杀，引发 Fatal Crash
        self._zombie_pool = []
        self._pool_lock = threading.Lock()

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
            
            # 方案 C: 在真正终结时，从废弃池中安全移除引用
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(lambda t=thread: self._clean_zombie(t))
            
            worker.log.connect(self.log_signal.emit)
            worker.error.connect(lambda t_no, msg: self.log_signal.emit(self.config.get_message("error_timer_generic", timer_no=t_no, error=msg)))
            
            self.threads.append(thread)
            self.workers.append(worker)
            thread.start()

    def _clean_zombie(self, thread):
        """线程确实完结后做最终的引用释放"""
        with self._pool_lock:
            if thread in self._zombie_pool:
                self._zombie_pool.remove(thread)

    def stop_all(self):
        """
        方案 C 核心：异步非阻塞放养退出 (Main-Thread Unobstructing)
        绝不在主线程调用 thread.wait() 导致同步死锁。
        """
        for worker in self.workers:
            try:
                # 微步休眠被一键击穿，线程将在底层迅速跑到终点
                worker.stop()
            except RuntimeError:
                pass
            
        with self._pool_lock:
            for thread in self.threads:
                try:
                    thread.quit()
                    # 扔进僵尸接管池，防止此时的 lists 置空导致立刻 GC 闪退
                    self._zombie_pool.append(thread)
                except RuntimeError:
                    # 线程对应的 C++ 对象已经被 Qt GC (如通过 deleteLater) 清理完毕
                    # 这是自动完成定时任务之后的正常现象，予以静默忽略
                    pass
                
        self.threads = []
        self.workers = []

