# helpers.py
# This module provides utility functions for checking and installing FFmpeg,
# a dependency required for the application.

import subprocess
import sys
import os
import shutil
from tkinter import messagebox
from typing import Optional


def check_and_install_ffmpeg() -> bool:
    """Check if FFmpeg is installed and prompt the user to install it if not found."""
    try:
        # Verify FFmpeg installation
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # FFmpeg not found; prompt for installation
        response = messagebox.askyesno(
            "FFmpeg Not Found",
            "FFmpeg is required for this application but was not found on your system.\n"
            "Would you like to attempt to install FFmpeg now?\n\n"
            "Note: This requires an internet connection and may take a few minutes."
        )
        if response:
            try:
                if sys.platform.startswith('win'):
                    # Windows: Install FFmpeg using winget
                    subprocess.run(['winget', 'install', '--id', 'Gyan.FFmpeg', '-e'], check=True)
                    messagebox.showinfo("Success", "FFmpeg has been installed successfully. Please restart the application.")
                    return True
                elif sys.platform.startswith('linux'):
                    # Linux: Install FFmpeg using apt (Debian/Ubuntu)
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], check=True)
                    messagebox.showinfo("Success", "FFmpeg has been installed successfully. Please restart the application.")
                    return True
                elif sys.platform.startswith('darwin'):
                    # macOS: Install FFmpeg using Homebrew
                    if not shutil.which('brew'):
                        messagebox.showerror("Error", "Homebrew is not installed. Please install Homebrew first, then install FFmpeg manually using 'brew install ffmpeg'.")
                        return False
                    subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
                    messagebox.showinfo("Success", "FFmpeg has been installed successfully. Please restart the application.")
                    return True
                else:
                    messagebox.showerror("Error", f"Unsupported platform: {sys.platform}. Please install FFmpeg manually.")
                    return False
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Installation Failed", f"Failed to install FFmpeg: {e}\nPlease install FFmpeg manually.")
                return False
            except FileNotFoundError as e:
                messagebox.showerror("Error", f"Package manager not found: {e}\nPlease install FFmpeg manually.")
                return False
        else:
            messagebox.showwarning("Warning", "FFmpeg is required for this application to function properly. Please install FFmpeg manually.")
            return False