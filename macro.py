import ctypes
import time
from pynput import mouse, keyboard
from pynput.keyboard import Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
import tkinter as tk
import threading
import sys

# High precision timing functions
if sys.platform == 'win32':
    # Windows high-resolution timer
    from ctypes import windll
    winmm = windll.winmm
    winmm.timeBeginPeriod(1)  # Set minimum timer resolution to 1ms
    
    # QueryPerformanceCounter for nanosecond precision
    _qpf = ctypes.c_int64()
    ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(_qpf))
    QPC_FREQUENCY = _qpf.value
    
    def time_ns():
        counter = ctypes.c_int64()
        ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(counter))
        return (counter.value * 1_000_000_000) // QPC_FREQUENCY
else:
    # Fallback for other platforms
    def time_ns():
        return time.perf_counter_ns()

PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MouseInput)]

MOUSE_DOWN_FLAGS = {
    mouse.Button.left: 0x0002,
    mouse.Button.right: 0x0008,
    mouse.Button.middle: 0x0020,
    mouse.Button.x1: 0x0080,
    mouse.Button.x2: 0x0100,
}
MOUSE_UP_FLAGS = {
    mouse.Button.left: 0x0004,
    mouse.Button.right: 0x0010,
    mouse.Button.middle: 0x0040,
    mouse.Button.x1: 0x0080,
    mouse.Button.x2: 0x0100,
}

# Pre-create all mouse inputs for maximum speed
MOUSE_INPUTS = {
    'left_down': Input(type=0, mi=MouseInput(0, 0, 0, MOUSE_DOWN_FLAGS[mouse.Button.left], 0, None)),
    'left_up': Input(type=0, mi=MouseInput(0, 0, 0, MOUSE_UP_FLAGS[mouse.Button.left], 0, None)),
    'right_down': Input(type=0, mi=MouseInput(0, 0, 0, MOUSE_DOWN_FLAGS[mouse.Button.right], 0, None)),
    'right_up': Input(type=0, mi=MouseInput(0, 0, 0, MOUSE_UP_FLAGS[mouse.Button.right], 0, None)),
}

# Optimized SendInput call
SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(Input), ctypes.c_int]
SendInput.restype = ctypes.c_uint

def send_click_nanosecond():
    """Ultra-fast click function using direct SendInput calls"""
    # Send mouse down and up in rapid succession
    SendInput(1, ctypes.byref(MOUSE_INPUTS['left_down']), ctypes.sizeof(Input))
    SendInput(1, ctypes.byref(MOUSE_INPUTS['left_up']), ctypes.sizeof(Input))

def send_click_burst(count=2):
    """Send multiple clicks in a burst for extreme CPS"""
    for _ in range(count):
        SendInput(1, ctypes.byref(MOUSE_INPUTS['left_down']), ctypes.sizeof(Input))
        SendInput(1, ctypes.byref(MOUSE_INPUTS['left_up']), ctypes.sizeof(Input))

class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Macro - Ryzen (Nano-optimized)")
        self.root.configure(bg='black')
        
        # Set higher priority for the window process
        try:
            import psutil
            import os
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        except:
            pass
        
        self.main_frame = tk.Frame(root, bg='black')
        self.main_frame.pack(padx=10, pady=10, fill='both', expand=True)
        
        title_label = tk.Label(self.main_frame, text=r"""
 ██▓███ ▓██   ██▓▄▄▄█████▓ ██░ ██  ▒█████   ███▄    █     ███▄ ▄███▓ ▄▄▄       ▄████▄   ██▀███   ▒█████  
▓██░  ██▒▒██  ██▒▓  ██▒ ▓▒▓██░ ██▒▒██▒  ██▒ ██ ▀█   █    ▓██▒▀█▀ ██▒▒████▄    ▒██▀ ▀█  ▓██ ▒ ██▒▒██▒  ██▒
▓██░ ██▓▒ ▒██ ██░▒ ▓██░ ▒░▒██▀▀██░▒██░  ██▒▓██  ▀█ ██▒   ▓██    ▓██░▒██  ▀█▄  ▒▓█    ▄ ▓██ ░▄█ ▒▒██░  ██▒
▒██▄█▓▒ ▒ ░ ▐██▓░░ ▓██▓ ░ ░▓█ ░██ ▒██   ██░▓██▒  ▐▌██▒   ▒██    ▒██ ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▒██▀▀█▄  ▒██   ██░
▒██▒ ░  ░ ░ ██▒▓░  ▒██▒ ░ ░▓█▒░██▓░ ████▓▒░▒██░   ▓██░   ▒██▒   ░██▒ ▓█   ▓██▒▒ ▓███▀ ░░██▓ ▒██▒░ ████▓▒░
▒▓▒░ ░  ░  ██▒▒▒   ▒ ░░    ▒ ░░▒░▒░ ▒░▒░▒░ ░ ▒░   ▒ ▒    ░ ▒░   ░  ░ ▒▒   ▓▒█░░ ░▒ ▒  ░░ ▒▓ ░▒▓░░ ▒░▒░▒░ 
░▒ ░     ▓██ ░▒░     ░     ▒ ░▒░ ░  ░ ▒ ▒░ ░ ░░   ░ ▒░   ░  ░      ░  ▒   ▒▒ ░  ░  ▒     ░▒ ░ ▒░  ░ ▒ ▒░ 
░░       ▒ ▒ ░░    ░       ░  ░░ ░░ ░ ░ ▒     ░   ░ ░    ░      ░     ░   ▒   ░          ░░   ░ ░ ░ ░ ▒  
         ░ ░               ░  ░  ░    ░ ░           ░           ░         ░  ░░ ░         ░         ░ ░  
         ░ ░                                                                  ░                          
                                                                                                         
        """, font=('Courier', 8, 'bold'), fg='white', bg='black')
        title_label.pack(pady=10)
        
        # Version label
        version_label = tk.Label(self.main_frame, text="Nano-Optimized v2.0", font=('Arial', 10),
                                fg='cyan', bg='black')
        version_label.pack(pady=5)
        
        self.trigger_label = tk.Label(self.main_frame, text="Trigger: Not Set", font=('Arial', 12),
                                     fg='white', bg='black')
        self.trigger_label.pack(pady=10)
        
        set_trigger_btn = tk.Button(self.main_frame, text="Set Trigger", command=self.set_trigger,
                                   bg='white', fg='black', font=('Arial', 10, 'bold'))
        set_trigger_btn.pack(pady=10)
        
        # CPS control frame
        cps_frame = tk.Frame(self.main_frame, bg='black')
        cps_frame.pack(pady=10)
        
        tk.Label(cps_frame, text="CPS:", font=('Arial', 12),
                fg='white', bg='black').pack(side=tk.LEFT, padx=5)
        
        self.cps_entry = tk.Entry(cps_frame, bg='white', fg='black', font=('Arial', 10), width=10)
        self.cps_entry.pack(side=tk.LEFT)
        self.cps_entry.insert(0, "100")  # Default to 100 CPS
        self.cps_entry.bind('<Return>', self.update_cps)
        
        # Extreme CPS button
        extreme_cps_btn = tk.Button(cps_frame, text="Max (1000)", command=self.set_max_cps,
                                   bg='red', fg='white', font=('Arial', 8, 'bold'))
        extreme_cps_btn.pack(side=tk.LEFT, padx=5)
        
        apply_cps_btn = tk.Button(cps_frame, text="Apply", command=self.update_cps,
                                 bg='green', fg='white', font=('Arial', 8, 'bold'))
        apply_cps_btn.pack(side=tk.LEFT, padx=5)
        
        # Advanced settings frame
        adv_frame = tk.Frame(self.main_frame, bg='black')
        adv_frame.pack(pady=5)
        
        tk.Label(adv_frame, text="Burst Mode:", font=('Arial', 10),
                fg='white', bg='black').pack(side=tk.LEFT, padx=5)
        
        self.burst_var = tk.BooleanVar(value=False)
        burst_check = tk.Checkbutton(adv_frame, text="Enabled", variable=self.burst_var,
                                    bg='black', fg='white', selectcolor='black')
        burst_check.pack(side=tk.LEFT, padx=5)
        
        tk.Label(adv_frame, text="Burst Count:", font=('Arial', 10),
                fg='white', bg='black').pack(side=tk.LEFT, padx=5)
        
        self.burst_entry = tk.Entry(adv_frame, bg='white', fg='black', font=('Arial', 10), width=5)
        self.burst_entry.pack(side=tk.LEFT)
        self.burst_entry.insert(0, "2")
        
        self.current_cps_label = tk.Label(self.main_frame, text="Current CPS: 100.0", font=('Arial', 10),
                                         fg='light green', bg='black')
        self.current_cps_label.pack(pady=5)
        
        # Performance monitor
        self.performance_label = tk.Label(self.main_frame, text="Avg. Jitter: 0.0ms", font=('Arial', 9),
                                         fg='yellow', bg='black')
        self.performance_label.pack(pady=2)
        
        self.toggle_var = tk.BooleanVar(value=False)
        self.toggle_btn = tk.Checkbutton(self.main_frame, text="⚡ ENABLE MACRO ⚡", variable=self.toggle_var,
                                        command=self.toggle_macro, bg='black', fg='white',
                                        font=('Arial', 12, 'bold'), selectcolor='black')
        self.toggle_btn.pack(pady=10)
        
        self.status_label = tk.Label(self.main_frame, text="Status: Disabled", font=('Arial', 12),
                                    fg='red', bg='black')
        self.status_label.pack(pady=10)
        
        # Click counter
        self.click_counter = 0
        self.counter_label = tk.Label(self.main_frame, text="Clicks: 0", font=('Arial', 10),
                                     fg='cyan', bg='black')
        self.counter_label.pack(pady=5)
        
        # Initialize variables
        self.trigger_key = None
        self.trigger_type = None
        self.pressed_keys = set()
        self.mouse_pressed = False
        self.running = False
        self.click_thread = None
        self.stop_clicking = threading.Event()
        self.macro_enabled = False
        self.setting_trigger = False
        self.current_cps = 100.0
        self.burst_mode = False
        self.burst_count = 2
        
        # Performance tracking
        self.last_click_time = 0
        self.jitter_history = []
        self.click_times = []
        
        # Start listeners
        self.key_listener = KeyboardListener(on_press=self.on_key_press, 
                                            on_release=self.on_key_release)
        self.key_listener.start()
        
        self.mouse_listener = MouseListener(on_click=self.on_mouse_click)
        self.mouse_listener.start()
        
        # Footer
        footer_frame = tk.Frame(self.main_frame, bg='black')
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        made_by_label = tk.Label(footer_frame, text="Made by Ryzen", font=('Arial', 8),
                                fg='gray', bg='black')
        made_by_label.pack(side=tk.LEFT)
        
        discord_label = tk.Label(footer_frame, text="Discord: 17ryzfr", font=('Arial', 8),
                                fg='gray', bg='black')
        discord_label.pack(side=tk.RIGHT)
        
        # Set window size
        self.root.update_idletasks()
        width = self.main_frame.winfo_reqwidth() + 20
        height = self.main_frame.winfo_reqheight() + 20
        self.root.geometry(f"{width}x{height}")
        
        self.root.eval('tk::PlaceWindow . center')
        
        # Start update loop
        self.update_loop()
    
    def set_max_cps(self):
        """Set CPS to maximum value"""
        self.cps_entry.delete(0, tk.END)
        self.cps_entry.insert(0, "1000")
        self.update_cps()
    
    def toggle_macro(self):
        self.macro_enabled = self.toggle_var.get()
        if self.macro_enabled:
            if self.trigger_key is None:
                self.toggle_var.set(False)
                self.macro_enabled = False
                self.status_label.config(text="Status: No Trigger Set", fg='orange')
            else:
                self.status_label.config(text="Status: Ready", fg='yellow')
                self.click_counter = 0
                self.counter_label.config(text="Clicks: 0")
        else:
            self.stop_clicking.set()
            self.running = False
            self.status_label.config(text="Status: Disabled", fg='red')
    
    def update_cps(self, event=None):
        """Update CPS with validation"""
        try:
            new_cps = float(self.cps_entry.get())
            if new_cps <= 0:
                self.current_cps_label.config(text="Error: CPS must be > 0", fg='red')
                return
            
            if new_cps > 1000:
                self.current_cps_label.config(text="Warning: Extreme CPS!", fg='orange')
            elif new_cps > 500:
                self.current_cps_label.config(text=f"Current CPS: {new_cps} (High)", fg='orange')
            else:
                self.current_cps_label.config(text=f"Current CPS: {new_cps}", fg='light green')
            
            self.current_cps = new_cps
            
            # Update burst mode
            self.burst_mode = self.burst_var.get()
            try:
                self.burst_count = max(1, int(self.burst_entry.get()))
            except:
                self.burst_count = 2
            
            # Restart clicking if active
            if self.running:
                self.stop_clicking.set()
                time.sleep(0.01)
                if self.macro_enabled and self.should_click():
                    self.stop_clicking.clear()
                    self.click_thread = threading.Thread(target=self.click_loop_nanosecond, daemon=True)
                    self.click_thread.start()
                    
        except ValueError:
            self.current_cps_label.config(text="Error: Invalid CPS value", fg='red')
    
    def set_trigger(self):
        self.setting_trigger = True
        self.trigger_label.config(text="Press any key or mouse button...")
        self.root.update()
        
        self.mouse_listener.stop()
        
        old_trigger = self.trigger_key
        
        self.trigger_key = None
        self.trigger_type = None
        
        if old_trigger and hasattr(old_trigger, 'char'):
            self.pressed_keys.discard(old_trigger)

        def on_mouse_click(x, y, button, pressed):
            if pressed:
                self.trigger_key = button
                self.trigger_type = "mouse"
                return False

        def on_key_press(key):
            self.trigger_key = key
            self.trigger_type = "keyboard"
            return False
        
        mouse_listener = MouseListener(on_click=on_mouse_click)
        keyboard_listener = KeyboardListener(on_press=on_key_press)
        
        mouse_listener.start()
        keyboard_listener.start()
        
        start_time = time.time()
        while self.trigger_key is None and (time.time() - start_time) < 10:
            time.sleep(0.001)  # Faster polling
        
        mouse_listener.stop()
        keyboard_listener.stop()
        
        if self.trigger_key is not None:
            if self.trigger_type == "mouse":
                self.trigger_label.config(text=f"Trigger: {self.trigger_key}")
            else:
                key_name = str(self.trigger_key).replace('Key.', '')
                self.trigger_label.config(text=f"Trigger: {key_name}")
            
            if self.macro_enabled:
                self.status_label.config(text="Status: Ready", fg='yellow')
        else:
            self.trigger_label.config(text="Trigger: Not Set")
        
        self.mouse_listener = MouseListener(on_click=self.on_mouse_click)
        self.mouse_listener.start()
        
        self.setting_trigger = False
    
    def on_key_press(self, key):
        self.pressed_keys.add(key)
    
    def on_key_release(self, key):
        self.pressed_keys.discard(key)
    
    def on_mouse_click(self, x, y, button, pressed):
        if self.trigger_type == "mouse" and button == self.trigger_key:
            self.mouse_pressed = pressed
    
    def should_click(self):
        """Check if we should be clicking based on current trigger state"""
        if self.trigger_type == "mouse":
            return self.mouse_pressed
        else:
            return self.trigger_key in self.pressed_keys
    
    def click_loop_nanosecond(self):
        """Ultra-precise click loop with nanosecond timing and burst mode"""
        try:
            cps = self.current_cps
            if cps <= 0:
                return
            
            target_interval_ns = int(1_000_000_000 / cps)
            next_click_time_ns = time_ns()
            click_count = 0
            start_time_ns = time_ns()
            
            # Pre-calculate burst mode settings
            burst_mode = self.burst_mode
            burst_count = self.burst_count
            
            while not self.stop_clicking.is_set():
                current_time_ns = time_ns()
                
                if current_time_ns >= next_click_time_ns:
                    # Record timing for jitter calculation
                    if self.last_click_time > 0:
                        jitter_ns = abs((current_time_ns - self.last_click_time) - target_interval_ns)
                        self.jitter_history.append(jitter_ns / 1_000_000)  # Convert to ms
                        if len(self.jitter_history) > 100:
                            self.jitter_history.pop(0)
                    
                    self.last_click_time = current_time_ns
                    
                    # Execute click(s)
                    if burst_mode and burst_count > 1:
                        send_click_burst(burst_count)
                        click_count += burst_count
                    else:
                        send_click_nanosecond()
                        click_count += 1
                    
                    # Update click counter in GUI thread
                    if click_count % 10 == 0:  # Update less frequently for performance
                        self.root.after(0, lambda: self.counter_label.config(text=f"Clicks: {click_count}"))
                    
                    # Schedule next click
                    next_click_time_ns += target_interval_ns
                    
                    # If we're behind schedule, catch up
                    if current_time_ns - next_click_time_ns > target_interval_ns:
                        next_click_time_ns = current_time_ns + target_interval_ns
                
                # Calculate sleep time with nanosecond precision
                sleep_time_ns = next_click_time_ns - time_ns()
                
                if sleep_time_ns > 1_000_000:  # > 1ms
                    time.sleep(sleep_time_ns / 1_000_000_000)
                elif sleep_time_ns > 10_000:  # > 10μs
                    # Busy wait for ultra-short intervals
                    pass
                    
        except Exception as e:
            print(f"Error in click loop: {e}")
    
    def update_loop(self):
        """Main update loop with performance monitoring"""
        if self.trigger_key is not None and self.macro_enabled and not self.setting_trigger:
            should_click = self.should_click()
            
            if should_click:
                if not self.running:
                    self.running = True
                    self.stop_clicking.clear()
                    self.click_thread = threading.Thread(target=self.click_loop_nanosecond, daemon=True)
                    self.click_thread.start()
                    self.status_label.config(text="Status: Clicking", fg='green')
            else:
                if self.running:
                    self.running = False
                    self.stop_clicking.set()
                    self.status_label.config(text="Status: Ready", fg='yellow')
        
        # Update performance metrics
        if self.jitter_history:
            avg_jitter = sum(self.jitter_history) / len(self.jitter_history)
            self.performance_label.config(text=f"Avg. Jitter: {avg_jitter:.2f}ms")
        
        # Schedule next update with minimal delay
        self.root.after(1, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerGUI(root)
    
    # Set window to stay on top
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    
    root.mainloop()
