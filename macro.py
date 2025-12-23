import ctypes
import time
from pynput import mouse, keyboard
from pynput.keyboard import Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
import tkinter as tk
import threading
import sys

if sys.platform == 'win32':
    from ctypes import windll
    winmm = windll.winmm
    winmm.timeBeginPeriod(1)

    _qpf = ctypes.c_int64()
    windll.kernel32.QueryPerformanceFrequency(ctypes.byref(_qpf))
    QPC_FREQUENCY = _qpf.value

    def time_ns():
        c = ctypes.c_int64()
        windll.kernel32.QueryPerformanceCounter(ctypes.byref(c))
        return (c.value * 1_000_000_000) // QPC_FREQUENCY
else:
    def time_ns():
        return time.perf_counter_ns()

PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MouseInput)]

LEFT_DOWN = Input(0, MouseInput(0, 0, 0, 0x0002, 0, None))
LEFT_UP   = Input(0, MouseInput(0, 0, 0, 0x0004, 0, None))

SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(Input), ctypes.c_int]

def send_click():
    SendInput(1, ctypes.byref(LEFT_DOWN), ctypes.sizeof(Input))
    SendInput(1, ctypes.byref(LEFT_UP), ctypes.sizeof(Input))

class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jadn's Python Macro")
        self.root.configure(bg="#0b0b0b")
        self.root.resizable(False, False)

        self.trigger_key = None
        self.trigger_type = None
        self.setting_trigger = False

        self.pressed_keys = set()
        self.mouse_pressed = False

        self.current_cps = 100.0
        self.macro_enabled = False
        self.running = False

        self.stop_clicking = threading.Event()

        frame = tk.Frame(root, bg="#0b0b0b")
        frame.pack(padx=20, pady=20)

        tk.Label(
            frame,
            text="Jadn's Python Macro",
            fg="white",
            bg="#0b0b0b",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 10))

        self.trigger_label = tk.Label(
            frame,
            text="Trigger: Not Set",
            fg="white",
            bg="#0b0b0b",
            font=("Segoe UI", 11)
        )
        self.trigger_label.pack(pady=6)

        tk.Button(
            frame,
            text="Set Trigger",
            command=self.set_trigger,
            width=18,
            bg="#000000",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            activebackground="#333333",
            activeforeground="white"
        ).pack(pady=6)

        cps_frame = tk.Frame(frame, bg="#0b0b0b")
        cps_frame.pack(pady=10)

        tk.Label(
            cps_frame,
            text="CPS",
            fg="white",
            bg="#0b0b0b",
            font=("Segoe UI", 11)
        ).pack(side=tk.LEFT, padx=5)

        self.cps_entry = tk.Entry(
            cps_frame,
            width=8,
            font=("Consolas", 11),
            justify="center",
            bg="white",
            fg="black",
            insertbackground="white"
        )
        self.cps_entry.insert(0, "100")
        self.cps_entry.pack(side=tk.LEFT)
        self.cps_entry.bind("<Return>", self.update_cps)

        self.apply_button = tk.Button(
            cps_frame,
            text="Apply",
            command=self.update_cps,
            bg="#000000",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            activebackground="#333333",
            activeforeground="white",
            highlightbackground="white",
            highlightcolor="white",
            highlightthickness=1
        )
        self.apply_button.pack(side=tk.LEFT, padx=6)

        self.cps_label = tk.Label(
            frame,
            text="Current CPS: 100",
            fg="white",
            bg="#0b0b0b",
            font=("Segoe UI", 10)
        )
        self.cps_label.pack(pady=4)

        self.toggle_var = tk.BooleanVar()
        tk.Checkbutton(
            frame,
            text="Enable/Disable Macro",
            variable=self.toggle_var,
            command=self.toggle_macro,
            fg="white",
            bg="#0b0b0b",
            selectcolor="#0b0b0b",
            font=("Segoe UI", 11, "bold"),
            activebackground="#0b0b0b",
            activeforeground="white"
        ).pack(pady=10)

        self.status_label = tk.Label(
            frame,
            text="Status: Disabled",
            fg="white",
            bg="#0b0b0b",
            font=("Segoe UI", 11, "bold")
        )
        self.status_label.pack(pady=5)

        footer = tk.Frame(frame, bg="#0b0b0b")
        footer.pack(fill="x", pady=(10, 0))

        tk.Label(
            footer,
            text="Discord: 7jadn",
            fg="gray",
            bg="#0b0b0b",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        self.key_listener = KeyboardListener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.mouse_listener = MouseListener(
            on_click=self.on_mouse_click
        )
        self.key_listener.start()
        self.mouse_listener.start()

        self.update_loop()

        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def set_trigger(self):
        self.setting_trigger = True
        self.trigger_label.config(text="Press key or mouse...", fg="white")
        self.status_label.config(text="Status: Waiting", fg="white")

    def on_key_press(self, key):
        if self.setting_trigger:
            if key == keyboard.Key.esc:
                self.setting_trigger = False
                self.trigger_label.config(text="Trigger: Not Set", fg="white")
                self.status_label.config(text="Status: Cancelled", fg="white")
                return

            self.trigger_key = key
            self.trigger_type = "keyboard"
            self.setting_trigger = False
            self.trigger_label.config(
                text=f"Trigger: {str(key).replace('Key.', '')}",
                fg="white"
            )
            self.status_label.config(text="Status: Ready", fg="white")
            return

        self.pressed_keys.add(key)

    def on_key_release(self, key):
        self.pressed_keys.discard(key)

    def on_mouse_click(self, x, y, button, pressed):
        if self.setting_trigger and pressed:
            self.trigger_key = button
            self.trigger_type = "mouse"
            self.setting_trigger = False
            self.trigger_label.config(text=f"Trigger: {button}", fg="white")
            self.status_label.config(text="Status: Ready", fg="white")
            return

        if self.trigger_type == "mouse" and button == self.trigger_key:
            self.mouse_pressed = pressed

    def should_click(self):
        if self.trigger_type == "mouse":
            return self.mouse_pressed
        return self.trigger_key in self.pressed_keys

    def update_cps(self, event=None):
        try:
            cps = float(self.cps_entry.get())
            if cps <= 0:
                raise ValueError
            self.current_cps = cps
            self.cps_label.config(
                text=f"Current CPS: {cps}",
                fg="white"
            )
        except:
            self.cps_label.config(text="Invalid CPS", fg="white")

    def toggle_macro(self):
        self.macro_enabled = self.toggle_var.get()
        if self.macro_enabled and self.trigger_key:
            self.status_label.config(text="Status: Ready", fg="white")
        elif self.macro_enabled:
            self.toggle_var.set(False)
            self.macro_enabled = False
            self.status_label.config(text="Status: No Trigger", fg="white")
        else:
            self.stop_clicking.set()
            self.running = False
            self.status_label.config(text="Status: Disabled", fg="white")

    def click_loop(self):
        interval = int(1_000_000_000 / self.current_cps)
        next_time = time_ns()

        while not self.stop_clicking.is_set():
            if time_ns() >= next_time:
                send_click()
                next_time += interval

    def update_loop(self):
        if self.macro_enabled and self.trigger_key and self.should_click():
            if not self.running:
                self.running = True
                self.stop_clicking.clear()
                threading.Thread(
                    target=self.click_loop,
                    daemon=True
                ).start()
                self.status_label.config(
                    text="Status: Clicking",
                    fg="white"
                )
        else:
            if self.running:
                self.running = False
                self.stop_clicking.set()
                self.status_label.config(
                    text="Status: Ready",
                    fg="white"
                )

        self.root.after(5, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.mainloop()
