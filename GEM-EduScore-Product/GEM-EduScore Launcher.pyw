"""Double-click launcher for GEM-EduScore on Windows.

It starts Streamlit without a terminal window, opens the browser, and keeps a
small controller window available so the user can stop the local server.
"""

from __future__ import annotations

import importlib.util
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


APP_DIR = Path(__file__).resolve().parent
APP_FILE = APP_DIR / "app.py"
REQUIREMENTS = APP_DIR / "requirements.txt"
PORT = 8501
LOCAL_URL = f"http://localhost:{PORT}"
HEALTH_URL = f"{LOCAL_URL}/_stcore/health"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class Launcher:
    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.owns_server = False

        self.root = tk.Tk()
        self.root.title("GEM-EduScore")
        self.root.geometry("570x340")
        self.root.resizable(False, False)
        self.root.configure(bg="#f7f8fc")
        self.root.protocol("WM_DELETE_WINDOW", self.stop_and_close)

        tk.Label(
            self.root,
            text="G",
            font=("Segoe UI", 25, "bold"),
            fg="white",
            bg="#4f46e5",
            width=2,
            height=1,
        ).pack(pady=(30, 10))
        tk.Label(
            self.root,
            text="GEM-EduScore",
            font=("Segoe UI", 19, "bold"),
            fg="#17233d",
            bg="#f7f8fc",
        ).pack()
        tk.Label(
            self.root,
            text="AI-powered Education Practice Evaluation",
            font=("Segoe UI", 9),
            fg="#60708c",
            bg="#f7f8fc",
        ).pack(pady=(3, 18))

        self.status = tk.StringVar(value="正在检查运行环境……")
        tk.Label(
            self.root,
            textvariable=self.status,
            font=("Microsoft YaHei UI", 9),
            fg="#52617a",
            bg="#f7f8fc",
        ).pack(pady=(0, 18))

        self.share_url = tk.StringVar(value="局域网分享地址将在启动后显示")
        tk.Label(
            self.root,
            textvariable=self.share_url,
            font=("Segoe UI", 8),
            fg="#7c879b",
            bg="#f7f8fc",
        ).pack(pady=(0, 12))

        button_frame = tk.Frame(self.root, bg="#f7f8fc")
        button_frame.pack()
        self.open_button = tk.Button(
            button_frame,
            text="在浏览器中打开",
            command=self.open_browser,
            state=tk.DISABLED,
            font=("Microsoft YaHei UI", 9, "bold"),
            fg="white",
            bg="#4f46e5",
            activebackground="#4338ca",
            activeforeground="white",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        )
        self.open_button.pack(side=tk.LEFT, padx=5)
        self.copy_button = tk.Button(
            button_frame,
            text="复制局域网地址",
            command=self.copy_network_url,
            state=tk.DISABLED,
            font=("Microsoft YaHei UI", 9),
            fg="#4338ca",
            bg="#eef2ff",
            activebackground="#e0e7ff",
            relief=tk.FLAT,
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
        tk.Button(
            button_frame,
            text="停止并退出",
            command=self.stop_and_close,
            font=("Microsoft YaHei UI", 9),
            fg="#475569",
            bg="#e9edf5",
            activebackground="#dfe4ee",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)

        threading.Thread(target=self.prepare_and_start, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()

    def set_status(self, text: str) -> None:
        self.root.after(0, self.status.set, text)

    def prepare_and_start(self) -> None:
        try:
            missing = [
                name
                for name in ("streamlit", "plotly", "openai", "docx", "reportlab", "pypdf", "pptx", "bs4", "httpx")
                if importlib.util.find_spec(name) is None
            ]
            if missing:
                self.set_status("首次启动：正在安装必要组件，请稍候……")
                completed = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True,
                    creationflags=CREATE_NO_WINDOW,
                    timeout=300,
                )
                if completed.returncode != 0:
                    detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "未知安装错误"
                    raise RuntimeError(f"依赖安装失败：{detail}")

            if self.is_healthy():
                self.set_ready("应用已经在运行；文档组件已就绪")
                return

            self.set_status("正在启动本地应用……")
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "streamlit",
                    "run",
                    str(APP_FILE),
                    "--server.headless",
                    "true",
                    "--server.port",
                    str(PORT),
                ],
                cwd=APP_DIR,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
            )
            self.owns_server = True

            for _ in range(80):
                if self.is_healthy():
                    self.set_ready("应用已就绪；关闭本窗口将停止服务")
                    self.root.after(0, self.open_browser)
                    return
                if self.process.poll() is not None:
                    raise RuntimeError("应用启动失败，请检查 Python 环境。")
                time.sleep(0.5)
            raise RuntimeError("应用启动超时，请重新启动。")
        except Exception as exc:
            self.set_status("启动失败")
            self.root.after(0, lambda: messagebox.showerror("GEM-EduScore 启动失败", str(exc)))

    def set_ready(self, text: str) -> None:
        self.set_status(text)
        self.root.after(0, lambda: self.open_button.config(state=tk.NORMAL))
        network_url = self.get_network_url()
        self.root.after(0, self.share_url.set, f"同一网络可尝试访问：{network_url}")
        self.root.after(0, lambda: self.copy_button.config(state=tk.NORMAL))

    def is_healthy(self) -> bool:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1.2) as response:
                return response.status == 200
        except Exception:
            return False

    def open_browser(self) -> None:
        webbrowser.open(LOCAL_URL)

    def get_network_url(self) -> str:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            address = sock.getsockname()[0]
            sock.close()
        except OSError:
            try:
                address = socket.gethostbyname(socket.gethostname())
            except OSError:
                address = "localhost"
        return f"http://{address}:{PORT}"

    def copy_network_url(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self.get_network_url())
        self.status.set("局域网地址已复制；是否可访问取决于防火墙和网络设置")

    def stop_and_close(self) -> None:
        if self.owns_server and self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.root.destroy()


if __name__ == "__main__":
    Launcher().run()
