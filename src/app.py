import tkinter as tk
from ui.main_window import DownloaderApp


def main() -> None:
    """Initialize and start the Tkinter application."""
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()