# Desktop user interface for the AMU memory system.

import json
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox

import requests
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw




# =========================
# config
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "tray_config.json")

DEFAULT_API_URL = "http://127.0.0.1:8800/save"
HEALTH_URL = "http://127.0.0.1:8800/health"
SHUTDOWN_URL = "http://127.0.0.1:8800/shutdown"

backend_process = None
settings_window = None


# =========================
# config write and read
# =========================
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"apiUrl": DEFAULT_API_URL}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"apiUrl": DEFAULT_API_URL}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# =========================
# Backend control
# =========================
def is_backend_running():
    try:
        r = requests.get(HEALTH_URL, timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def start_backend():
    global backend_process

    if is_backend_running():
        return

    # Prefer venv
    venv_python = os.path.join(BASE_DIR, "venv", "Scripts", "pythonw.exe")

    if os.path.exists(venv_python):
        cmd = [venv_python, "api.py"]
    else:
        # use PATH python
        cmd = ["python", "api.py"]

    try:
        backend_process = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print("error:", e)


def stop_backend():
    try:
        requests.post(SHUTDOWN_URL, timeout=2)
    except Exception:
        pass


# =========================
# Create tray icon
# =========================
def create_image():

    return Image.open("memory-system.ico")


# =========================
# Setting windows
# =========================
def open_settings():
    global settings_window

    if settings_window and settings_window.winfo_exists():
        settings_window.lift()
        return

    config = load_config()

    settings_window = tk.Tk()
    settings_window.title("API Settings")
    settings_window.geometry("360x150")
    settings_window.resizable(False, False)

    tk.Label(settings_window, text="API 地址").pack(pady=(12, 4))

    api_var = tk.StringVar(value=config.get("apiUrl"))

    entry = tk.Entry(settings_window, textvariable=api_var, width=45)
    entry.pack()

    def save_action():
        config["apiUrl"] = api_var.get().strip()
        save_config(config)
        messagebox.showinfo("提示", "已保存")

    def close_action():
        settings_window.destroy()

    frame = tk.Frame(settings_window)
    frame.pack(pady=10)

    tk.Button(frame, text="保存", command=save_action).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="关闭", command=close_action).pack(side=tk.LEFT, padx=5)

    settings_window.mainloop()


def open_settings_thread(icon=None, item=None):
    threading.Thread(target=open_settings, daemon=True).start()


# =========================
# Tray menu
# =========================
def view_action(icon, item):
    open_settings_thread()


def quit_action(icon, item):
    stop_backend()
    icon.stop()


# =========================
# Main
# =========================
def main():
    start_backend()

    icon = pystray.Icon(
        "MemoryAPI",
        create_image(),
        "Memory API",
        menu=pystray.Menu(
            item("View", view_action),
            item("Quit", quit_action),
        ),
    )

    icon.run()


if __name__ == "__main__":
    main()