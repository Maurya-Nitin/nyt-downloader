import tkinter as tk
from typing import Optional

# Logger class for handling application logs with colored output
class Logger:
    def log(self, message: str, level: str = "info") -> None:
        """Improved Logging with Colors"""
        colors = {"info": "white", "success": "lightgreen", "warning": "orange", "error": "red"}
        
        self.log_text.insert(tk.END, message + "\n", level)
        self.log_text.tag_config(level, foreground=colors.get(level, "white"))
        if self.master.focus_get() == self.log_text:
            pass  # Don't auto-scroll if the log window is focused
        else:
            self.log_text.see(tk.END)  # Auto-scroll to the end

    def debug(self, msg: str) -> None:
        """Log a debug message"""
        self.log("[DEBUG] " + msg, "info")

    def success(self, msg: str) -> None:
        """Log a success message"""
        self.log("[SUCCESS] " + msg, "success")

    def warning(self, msg: str) -> None:
        """Log a warning message"""
        self.log("[WARNING] " + msg, "warning")

    def error(self, msg: str) -> None:
        """Log an error message"""
        self.log("[ERROR] " + msg, "error")

    def critical(self, msg: str) -> None:
        """Log a critical message"""
        self.log("[CRITICAL] " + msg, "error")