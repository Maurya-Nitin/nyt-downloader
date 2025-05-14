import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox, scrolledtext
from tktooltip import ToolTip
from PIL import Image
from pystray import Icon as PyStrayIcon, MenuItem as TrayMenuItem, Menu
import sys
import threading
from typing import Dict, List, Optional, Union, Any, Tuple

from core.downloader import Downloader#type: ignore
from core.queue import QueueManager#type: ignore
from core.settings import SettingsManager#type: ignore

# Main application class for the NYT Downloader GUI
class DownloaderApp(Downloader, QueueManager, SettingsManager):
    def __init__(self, master: tk.Tk) -> None:
        # Initialize parent classes and set up the main window
        self.master: tk.Tk = master
        master.title("NYT Downloader")
        self.base_path: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            icon_path: str = os.path.join(self.base_path, "assets", "logo.ico")
            master.iconbitmap(icon_path)
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")
        master.state("zoomed")
        master.protocol("WM_DELETE_WINDOW", self.close_application)
        self.download_directory: str = ""
        self.handy_widgets: Dict[str, Union[ttk.Combobox, tk.Checkbutton]] = {}
        self.preset_dir: str = "settings_presets"
        os.makedirs(self.preset_dir, exist_ok=True)
        try:
            self.export_image: tk.PhotoImage = tk.PhotoImage(file=os.path.join(self.base_path, "assets", "export.png"))
            self.clear_image: tk.PhotoImage = tk.PhotoImage(file=os.path.join(self.base_path, "assets", "clear.png"))
            self.search_image: tk.PhotoImage = tk.PhotoImage(file=os.path.join(self.base_path, "assets", "search.png"))
            self.refresh_image: tk.PhotoImage = tk.PhotoImage(file=os.path.join(self.base_path, "assets", "refresh.png"))
            self.settings_image: tk.PhotoImage = tk.PhotoImage(file=os.path.join(self.base_path, "assets", "settings.png"))
            self.import_image: tk.PhotoImage = tk.PhotoImage(file=os.path.join(self.base_path, "assets", "import.png"))
        except tk.TclError as e:
            print(f"Error loading images: {e}")
            messagebox.showwarning("Image Load Error", "One or more image files (e.g., export.png) could not be loaded. Some buttons may appear without icons.")
            self.export_image = tk.PhotoImage()
            self.clear_image = tk.PhotoImage()
            self.search_image = tk.PhotoImage()
            self.refresh_image = tk.PhotoImage()
            self.settings_image = tk.PhotoImage()
            self.import_image = tk.PhotoImage()
        self.format_options: Dict[str, str] = {
            "All Available Formats": "all",
            "Best (Video+Audio)": "best",
            "Best Video+Audio (Muxed)": "bv*+ba/best",
            "Best ≤720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "Best ≤480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "Worst Video+Audio (Muxed)": "worst",
            "Best Video Only": "bestvideo",
            "Worst Video Only": "worstvideo",
            "Best Video (any stream)": "bestvideo*",
            "Worst Video (any stream)": "worstvideo*",
            "Best Audio Only": "bestaudio",
            "Worst Audio Only": "worstaudio",
            "Best Audio (any stream)": "bestaudio*",
            "Worst Audio (any stream)": "worstaudio*",
            "Smallest File": "best -S +size,+br,+res,+fps",
        }
        self.video_exts: List[str] = ["mp4", "webm", "mkv", "flv", "avi"]
        self.audio_exts: List[str] = ["mp3", "m4a", "aac", "wav", "ogg", "opus"]
        Downloader.__init__(self, self)
        QueueManager.__init__(self, self)
        SettingsManager.__init__(self, self)
        self.create_widgets()
        self.master.bind("<F2>", self.open_settings_window_for_selected)
        self.tray_icon: Optional[Any] = None

    # Create and configure all GUI widgets
    def create_widgets(self) -> None:
        self.panedwindow: tk.PanedWindow = tk.PanedWindow(self.master, orient=tk.HORIZONTAL, sashwidth=5)
        self.panedwindow.pack(fill=tk.BOTH, expand=1)

        self.left_main_frame: tk.Frame = tk.Frame(self.panedwindow, width=300, bg="lightgray")
        self.panedwindow.add(self.left_main_frame)

        self.left_scrollbar: tk.Scrollbar = tk.Scrollbar(self.left_main_frame, orient=tk.VERTICAL, bg="#169976")
        self.left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.left_canvas: tk.Canvas = tk.Canvas(self.left_main_frame, bg="lightgray", yscrollcommand=self.left_scrollbar.set)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_scrollbar.config(command=self.left_canvas.yview)

        self.left_frame: tk.Frame = tk.Frame(self.left_canvas, bg="lightgray")
        self.left_canvas.create_window((0, 0), window=self.left_frame, anchor="nw")

        # Update scroll region based on canvas content
        def update_scroll_region(event: Optional[tk.Event] = None) -> None:
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
            if self.left_frame.winfo_height() <= self.left_canvas.winfo_height():
                self.left_canvas.unbind_all("<MouseWheel>")
                self.left_scrollbar.pack_forget()
            else:
                self.left_canvas.bind_all("<MouseWheel>", lambda e: self.left_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
                self.left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.master.bind("<Configure>", update_scroll_region)
        self.left_canvas.bind("<Configure>", lambda e: self.left_canvas.itemconfig(self.left_canvas.find_withtag("all")[0], width=e.width))

        self.main_right_frame: tk.PanedWindow = tk.PanedWindow(self.panedwindow, width=300, orient=tk.VERTICAL, bg="lightgray")
        self.main_right_frame.pack(fill=tk.BOTH, expand=1)
        self.panedwindow.add(self.main_right_frame)
        self.right_frame: tk.Frame = tk.Frame(self.main_right_frame, width=300, bg="lightgray")
        self.main_right_frame.add(self.right_frame)
        self.bottom_frame: tk.Frame = tk.Frame(self.main_right_frame, bg="lightgray")
        self.main_right_frame.add(self.bottom_frame)

        # Create log frame and controls
        log_frame: tk.LabelFrame = tk.LabelFrame(self.bottom_frame, text="📜 Download Logs", font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        log_controls_frame: tk.Frame = tk.Frame(log_frame, bg="lightgray")
        log_controls_frame.pack(fill=tk.X, padx=5, pady=5)

        export_button: tk.Button = tk.Button(log_controls_frame, command=self.export_logs, image=self.export_image, relief="flat", bg="lightgray")
        export_button.pack(side=tk.LEFT, padx=5, pady=5)
        ToolTip(export_button, msg="Export logs to a file can be useful for sharing problems.\n Shift to verbose output in Full settings for detailed logs.", delay=0.5)

        clear_logs_button: tk.Button = tk.Button(log_controls_frame, command=lambda: self.log_text.delete("1.0", tk.END), image=self.clear_image, relief="flat", bg="lightgray")
        clear_logs_button.pack(side=tk.LEFT, padx=5, pady=5)
        ToolTip(clear_logs_button, msg="Clear all logs from the log window.\nThis action cannot be undone, so ensure you have exported the logs if needed.", delay=0.5)

        search_entry: tk.Entry = tk.Entry(log_controls_frame, font=("Arial", 8))
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        search_entry.bind("<Return>", lambda e: search_logs() if self.master.focus_get() == search_entry else None)
        ToolTip(search_entry, msg="Press Enter to search logs after typing. It highlights Text into yellow.", delay=0.5)

        # Search logs and highlight matches
        def search_logs() -> None:
            self.log_text.tag_remove("highlight", "1.0", tk.END)
            query: str = search_entry.get().strip()
            if query:
                start_pos: str = "1.0"
                while True:
                    start_pos = self.log_text.search(query, start_pos, stopindex=tk.END, nocase=True)
                    if not start_pos:
                        break
                    end_pos: str = f"{start_pos}+{len(query)}c"
                    self.log_text.tag_add("highlight", start_pos, end_pos)
                    start_pos = end_pos
            self.log_text.tag_config("highlight", background="yellow", foreground="black")

        search_button: tk.Button = tk.Button(log_controls_frame, command=search_logs, image=self.search_image, borderwidth=0, relief="flat", bg="lightgray")
        search_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.log_text: scrolledtext.ScrolledText = scrolledtext.ScrolledText(log_frame, bg="#222", fg="white", font=("Consolas", 10), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.bind("<Control-a>", lambda e: self.log_text.tag_add("sel", "1.0", tk.END) or "break")
        self.log_text.bind("<Key>", lambda e: None if e.state & 4 and e.keysym in ('a', 'A', 'c', 'C') else "break")

        # Create input frame for URL/query
        input_frame: tk.LabelFrame = tk.LabelFrame(self.left_frame, text="🎥 Input", font=("Arial", 10, "bold"))
        input_frame.pack(fill=tk.X, padx=10, pady=5, expand=True)

        self.query_entry: tk.Entry = tk.Entry(input_frame, width=45, font=("Arial", 10))
        self.query_entry.pack(pady=5, padx=10, fill=tk.X, expand=True)
        ToolTip(self.query_entry, msg="Enter URL of any supported websites(check yt_dlp docs) or Search Query in YouTube.\nPress Enter to add to queue.", delay=0.5)
        self.query_entry.bind("<Return>", self.add_to_queue)
        tk.Label(input_frame, text="Please use (Any Stream) format for other than ytsites.", font=("Arial", 8), fg="gray").pack(pady=5, padx=10, fill=tk.X)
        add_button: tk.Button = tk.Button(input_frame, text="➕ Add to Queue", command=self.add_to_queue, bg="#28a745", fg="white", font=("Arial", 10, "bold"))
        add_button.pack(pady=5, padx=10, fill=tk.X)
        ToolTip(add_button, msg="Click to add the URL or Search Query to the download queue.\n Note: It just adds to queue and not start downloads.\n Press Start Download Manually.", delay=0.5)

        # Create frame for loading spreadsheet
        csv_frame: tk.LabelFrame = tk.LabelFrame(self.left_frame, text="📂 Load Spreadsheet", font=("Arial", 10, "bold"))
        csv_frame.pack(fill=tk.X, padx=10, pady=5)
        select_file_button: tk.Button = tk.Button(csv_frame, text="📄 Select Spreadsheet File", command=self.load_spreadsheet_threaded, bg="#007bff", fg="white", font=("Arial", 10))
        select_file_button.pack(pady=5, padx=10, fill=tk.X)
        ToolTip(select_file_button, msg="Load CSV (Comma-separated Values) or Spreadsheet file containing URLs or Search Queries.\nIt will add all entries to the download queue.", delay=0.5)
        format_label: tk.Label = tk.Label(csv_frame, text="Supported Formats:\n- CSV: Comma-separated URLs or Queries\n- Excel: Columns 'Query' or 'URL' (Optional: 'Preset')", font=("Arial", 8), fg="gray", justify="left")
        format_label.pack(pady=5, padx=10, fill=tk.X)

        # Create frame for selecting download directory
        dir_frame: tk.LabelFrame = tk.LabelFrame(self.left_frame, text="📁 Download Directory", font=("Arial", 10, "bold"))
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        dir_button: tk.Button = tk.Button(dir_frame, text="📂 Select Folder", command=self.select_directory, bg="#ff9800", fg="white", font=("Arial", 10))
        dir_button.pack(pady=5, padx=10, fill=tk.X)
        self.dir_label: tk.Label = tk.Label(dir_frame, text="No directory selected", font=("Arial", 9), fg="gray")
        self.dir_label.pack(pady=5)
        ToolTip(dir_button, msg="Click to select the folder where you want to save the downloaded files.\nIt will be used as default download location.\n You can edit download location for single file even after queueing in File and Naming option Tab", delay=0.5)

        # Create frame for handy settings
        handy_frame: tk.LabelFrame = tk.LabelFrame(self.left_frame, text="🛠️ Handy Settings", font=("Arial", 10, "bold"))
        handy_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(handy_frame, text="Select Preset:", font=("Arial", 10)).grid(row=0, column=0, padx=5, sticky="w")
        self.preset_var: tk.StringVar = tk.StringVar()
        self.preset_dropdown: ttk.Combobox = ttk.Combobox(handy_frame, textvariable=self.preset_var, state="readonly")
        self.preset_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.preset_dropdown.bind("<<ComboboxSelected>>", self.on_preset_selected)
        try:
            files: List[str] = [f[:-5] for f in os.listdir(self.preset_dir) if f.endswith(".json")]
        except FileNotFoundError:
            files = []
        self.preset_dropdown["values"] = files + ["New/Unsaved"]
        if "default" in files:
            self.preset_dropdown.set("default")
        else:
            self.preset_dropdown.set("New/Unsaved")
        ToolTip(self.preset_dropdown, msg="Select a preset to load its settings.\nYou can also create new presets from the settings window.", delay=0.5)

        tk.Label(handy_frame, text="Select Format:", font=("Arial", 10)).grid(row=1, column=0, padx=5, sticky="w")

        # Update file extension options based on selected format
        def update_format_entry(event: Optional[tk.Event] = None) -> None:
            selected_label: str = self.format_var.get()
            if "Audio" in selected_label and "Video" not in selected_label:
                self.handy_widgets['final_ext']['values'] = ["original"] + self.audio_exts
                self.handy_widgets['final_ext'].set("original")
            elif "Video" in selected_label or "Quality" in selected_label or "MP4" in selected_label:
                self.handy_widgets['final_ext']['values'] = ["original"] + self.video_exts
                self.handy_widgets['final_ext'].set("original")
            else:
                self.handy_widgets['final_ext']['values'] = ["original"] + self.video_exts + self.audio_exts
                self.handy_widgets['final_ext'].set("original")

        self.format_var: tk.StringVar = tk.StringVar(value="Best Video+Audio (Muxed)")
        self.handy_widgets["format_dropdown"] = ttk.Combobox(master=handy_frame, textvariable=self.format_var, values=list(self.format_options.keys()), state="readonly")
        self.handy_widgets["format_dropdown"].grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.handy_widgets['format_dropdown'].bind("<<ComboboxSelected>>", update_format_entry)
        ToolTip(self.handy_widgets["format_dropdown"], msg="Select a format for the download.\n Please select Any stream format if face format error.\n Also you can manually type any legal format in settings Window.\nIt will automatically adapt the final extension options.", delay=0.5)

        tk.Label(handy_frame, text="Select Extension:", font=("Arial", 10)).grid(row=2, column=0, padx=5, sticky="w")
        final_ext_options: List[str] = ["original"] + self.video_exts
        self.final_ext_var: tk.StringVar = tk.StringVar(value="original")
        self.handy_widgets["final_ext"] = ttk.Combobox(master=handy_frame, textvariable=self.final_ext_var, values=final_ext_options, state="readonly")
        self.handy_widgets["final_ext"].grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ToolTip(self.handy_widgets["final_ext"], msg="Select the final file extension for the download.\n It will be used as default extension for all downloads.\n Custom formats will be converted on your Machine and that is Resource taking process.", delay=0.5)

        self.embed_subtitles_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.handy_widgets["embedsubtitles"] = tk.Checkbutton(handy_frame, text="Embed Subtitles", variable=self.embed_subtitles_var, font=("Arial", 10))
        self.handy_widgets["embedsubtitles"].grid(row=3, column=0, padx=5, sticky="w")
        ToolTip(self.handy_widgets["embedsubtitles"], msg="Embed subtitles into the video file.\n Full Control over it in Settings Window.", delay=0.5)

        self.embed_thumbnail_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.handy_widgets["embedthumbnail"] = tk.Checkbutton(handy_frame, text="Embed Thumbnail", variable=self.embed_thumbnail_var, font=("Arial", 10))
        self.handy_widgets["embedthumbnail"].grid(row=3, column=1, padx=5, sticky="w")
        ToolTip(self.handy_widgets["embedthumbnail"], msg="Embed thumbnail into the video file.", delay=0.5)

        self.writeautomaticsub_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.handy_widgets["writeautomaticsub"] = tk.Checkbutton(handy_frame, text="Include Auto subs", variable=self.writeautomaticsub_var, font=("Arial", 10))
        self.handy_widgets["writeautomaticsub"].grid(row=4, column=0, padx=5, sticky="w")
        ToolTip(self.handy_widgets["writeautomaticsub"], msg="Include auto-generated subtitles in the download.\n Full Control over it in Settings Window.", delay=0.5)

        self.metadata_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.handy_widgets["addmetadata"] = tk.Checkbutton(handy_frame, text="Add Metadata", variable=self.metadata_var, font=("Arial", 10))
        self.handy_widgets["addmetadata"].grid(row=4, column=1, padx=5, sticky="w")
        ToolTip(self.handy_widgets["addmetadata"], msg="Add metadata to the downloaded file.\n Metadata includes title, author, etc. data.", delay=0.5)

        tk.Label(handy_frame, text="Sponsorblock:", font=("Arial", 10)).grid(row=5, column=0, padx=5, sticky="w")
        self.sponsorblock_var: tk.StringVar = tk.StringVar(value="mark")
        self.mark_all_radio: tk.Radiobutton = tk.Radiobutton(handy_frame, text="Mark All", variable=self.sponsorblock_var, value="mark", font=("Arial", 10))
        self.mark_all_radio.grid(row=6, column=0, padx=5, sticky="w")
        ToolTip(self.mark_all_radio, msg="Mark all sponsorblock segments in the video.\n Full Control over it in Settings Window.", delay=0.5)
        self.remove_all_radio: tk.Radiobutton = tk.Radiobutton(handy_frame, text="Remove All", variable=self.sponsorblock_var, value="remove", font=("Arial", 10))
        self.remove_all_radio.grid(row=6, column=1, padx=5, sticky="w")
        ToolTip(self.remove_all_radio, msg="Remove all sponsorblock segments from the video.\n Full Control over it in Settings Window.", delay=0.5)
        self.other_radio: tk.Radiobutton = tk.Radiobutton(handy_frame, text="Custom", variable=self.sponsorblock_var, value="Other", font=("Arial", 10))
        self.other_radio.grid(row=6, column=1, sticky="e")
        ToolTip(self.other_radio, msg="Custom Sponsorblock settings.\n If not any preset selected and not opted anything,\n in Settings window it sets to do nothing.", delay=0.5)

        self.format_var.trace_add("write", lambda *args: self.save_handy_settings_into_global())
        self.final_ext_var.trace_add("write", lambda *args: self.save_handy_settings_into_global())
        self.embed_thumbnail_var.trace_add("write", lambda *args: self.save_handy_settings_into_global())
        self.metadata_var.trace_add("write", lambda *args: self.save_handy_settings_into_global())
        self.sponsorblock_var.trace_add("write", lambda *args: self.save_handy_settings_into_global())
        self.embed_subtitles_var.trace_add("write", lambda *args: self.save_handy_settings_into_global())
        self.writeautomaticsub_var.trace_add("write", lambda *args: self.save_handy_settings_into_global())

        if self.global_ydl_opts != {}:
            self.load_handy_settings()
        else:
            self.save_handy_settings_into_global()

        tk.Label(handy_frame, text="If not autosaved :", font=("Arial", 10)).grid(row=9, column=0, padx=5, sticky="w")
        tk.Button(handy_frame, text="💾 Save Settings", command=self.save_handy_settings_into_global, bg="#007bff", fg="white", font=("Arial", 10)).grid(row=9, column=1, padx=10, pady=5, sticky="ew")
        self.settings_button: tk.Button = tk.Button(handy_frame, text="⚙️ Full Settings", command=self.open_settings_window, bg="#007bff", fg="white", font=("Arial", 10))
        ToolTip(self.settings_button, msg="Click to open the full settings window.\n You can customize various options for downloads.\n It will be saved as default template.\n press F2 as shortcut can edit individual task settings via it also.", delay=0.5)
        self.settings_button.grid(row=10, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Create actions frame
        actions_frame: tk.LabelFrame = tk.LabelFrame(self.left_frame, text="⚡ Actions", font=("Arial", 10, "bold"))
        actions_frame.pack(fill=tk.X, padx=10, pady=5)

        download_button: tk.Button = tk.Button(actions_frame, text="🚀 Start Downloads", command=self.start_downloads, bg="#dc3545", fg="white", font=("Arial", 12, "bold"))
        download_button.pack(pady=10, padx=10, fill=tk.X)
        ToolTip(download_button, msg="Click to start the downloads in the queue.\n It will start downloading all the items in the queue.\n It starts 4 concurrent downloads for now.", delay=0.5)

        bg_button: tk.Button = tk.Button(actions_frame, text="🛡️ Run in Background", bg="#444", fg="white", command=self.minimize_to_tray)
        bg_button.pack(pady=10, padx=10, fill=tk.X)
        ToolTip(bg_button, msg="Click to minimize the app to the system tray.\n You can restore it from the tray icon.", delay=0.5)

        # Create download queue frame
        queue_frame: tk.LabelFrame = tk.LabelFrame(self.right_frame, text="📥 Download Queue", font=("Arial", 10, "bold"))
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.queue_table: ttk.Treeview = ttk.Treeview(queue_frame, columns=("Index", "Status", "Query", "Progress"), show="headings", height=18, selectmode="extended")
        self.queue_table.heading("Index", text="Sr. No.", anchor="center")
        self.queue_table.heading("Query", text="📄 Title / Query", anchor="w")
        self.queue_table.heading("Status", text="🔄 Status", anchor="center")
        self.queue_table.heading("Progress", text="Progress", anchor="center")

        self.queue_table.column("Index", width=25, anchor="center")
        self.queue_table.column("Query", width=250, anchor="w")
        self.queue_table.column("Status", width=100, anchor="center")
        self.queue_table.column("Progress", width=150, anchor="center")

        scrollbar: ttk.Scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_table.yview)
        self.queue_table.configure(yscroll=scrollbar.set)
        h_scrollbar: ttk.Scrollbar = ttk.Scrollbar(queue_frame, orient=tk.HORIZONTAL, command=self.queue_table.xview)
        self.queue_table.configure(xscroll=h_scrollbar.set)

        button_frame: tk.Frame = tk.Frame(queue_frame)
        button_frame.grid(row=2, column=0, padx=5, pady=0, sticky="ew")

        self.refresh_button: tk.Button = tk.Button(button_frame, image=self.refresh_image, command=self.update_queue_listbox_threadsafe, borderwidth=0, relief="flat")
        self.refresh_button.pack(side=tk.LEFT, padx=10)
        ToolTip(self.refresh_button, msg="Refresh\nRefresh the queue list although it refreshes automatically. You can press it to manually refresh.\nIt will not remove any item from the queue.", delay=0.5)

        self.export_button: tk.Button = tk.Button(button_frame, image=self.export_image, command=self.export_queue, borderwidth=0, relief="flat")
        self.export_button.pack(side=tk.LEFT, padx=10)
        ToolTip(self.export_button, msg="Export\nExport the pending downloads with all settings saved into JSON format.\nThis can be useful for sharing or using it later via the Import button.", delay=0.5)

        self.import_button: tk.Button = tk.Button(button_frame, image=self.import_image, command=self.import_queue, borderwidth=0, relief="flat")
        self.import_button.pack(side=tk.LEFT, padx=10)
        ToolTip(self.import_button, msg="Import\nImport a JSON file containing download items.\nIt will add all entries to the download queue.", delay=0.5)

        self.clear_button: tk.Button = tk.Button(button_frame, image=self.clear_image, command=self.clear_queue, borderwidth=0, relief="flat")
        self.clear_button.pack(side=tk.LEFT, padx=10)
        ToolTip(self.clear_button, msg="Clear\nClear all items from the download queue if none are selected, or clear only the selected items.\nNote: This action cannot be undone.", delay=0.5)

        self.settings_button: tk.Button = tk.Button(button_frame, image=self.settings_image, command=self.open_settings_window_for_selected, borderwidth=0, relief="flat")
        self.settings_button.pack(side=tk.LEFT, padx=10)
        ToolTip(self.settings_button, msg="⚙️ Settings (F2)\nOpen settings for the selected item(s) in the queue.\nIf more than one item is selected, it changes settings for all in common.\nIf no item is selected, it opens Global settings.\nYou can customize various options for specific downloads.", delay=0.5)

        self.queue_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        tk.Label(queue_frame, text="🔍 Click to select individual, Shift+Click to select range, Ctrl+click to select multiple randomly, Ctrl+A to select all", font=("Arial", 10), fg="gray", justify='center').grid(row=3, column=0, sticky="nsew", padx=5, pady=0)
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(0, weight=1)

        self.queue_table.bind("<Shift-Button-1>", self.on_shift_click)
        self.queue_table.bind("<B1-Motion>", self.on_drag_select)
        self.queue_table.bind("<Control-a>", self.select_all)
        self.queue_table.bind("<Delete>", self.del_key)
        self.queue_table.bind("backspace", self.del_key)

    # Handle shift-click selection in queue table
    def on_shift_click(self, event: tk.Event) -> None:
        selected: Tuple[str, ...] = self.queue_table.selection()
        last_clicked: str = self.queue_table.identify_row(event.y)
        if not selected:
            return
        if last_clicked:
            self.last_selected_index: int = self.queue_table.index(last_clicked)
            first_index: int = self.queue_table.index(selected[0])
            last_index: int = self.queue_table.index(last_clicked)
            for i in range(min(first_index, last_index), max(first_index, last_index) + 1):
                self.queue_table.selection_add(self.queue_table.get_children()[i])

    # Handle drag selection in queue table
    def on_drag_select(self, event: tk.Event) -> None:
        row_id: str = self.queue_table.identify_row(event.y)
        if row_id:
            self.queue_table.selection_add(row_id)

    # Select all items in queue table
    def select_all(self, event: Optional[tk.Event] = None) -> str:
        if self.queue_table == self.master.focus_get():
            self.queue_table.selection_set(self.queue_table.get_children())
            return "break"
        return "break"

    # Handle delete key press in queue table
    def del_key(self, event: tk.Event) -> None:
        if self.master.focus_get() == self.queue_table:
            self.clear_queue()

    # Update queue table in a thread-safe manner
    def update_queue_listbox_threadsafe(self) -> None:
        def update_queue_listbox() -> None:
            existing_iids: set = set(self.queue_table.get_children())
            expected_iids: set = set()

            for i, task in enumerate(self.queue):
                iid: str = f"item_{i}"
                expected_iids.add(iid)

                status: str = task["status"]
                progress: str = task.get("progress", "0% | --:--")
                values: Tuple[int, str, str, str] = (i + 1, status, task["query"], progress)

                color: str = "gray"
                if status == "Downloading":
                    color = "blue"
                elif status == "Completed":
                    color = "green"
                elif status.startswith("Failed"):
                    color = "red"

                if self.queue_table.exists(iid):
                    old_values: Tuple[int, str, str, str] = self.queue_table.item(iid, "values")
                    if old_values != values:
                        self.queue_table.item(iid, values=values, tags=(color,))
                else:
                    self.queue_table.insert("", "end", iid=iid, values=values, tags=(color,))

            for iid in existing_iids - expected_iids:
                self.queue_table.delete(iid)

            self.queue_table.tag_configure("gray", foreground="gray")
            self.queue_table.tag_configure("blue", foreground="blue")
            self.queue_table.tag_configure("green", foreground="green")
            self.queue_table.tag_configure("red", foreground="red")

        self.master.after(100, update_queue_listbox)

    # Export logs to a file
    def export_logs(self) -> None:
        file_path: Optional[str] = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for line in self.log_text.get("1.0", tk.END).splitlines():
                    f.write(line + "\n")
            self.log(f"✅ Log exported to {file_path}")
        except Exception as e:
            self.log(f"❌ Error exporting log: {e}", level="error")

    # Select download directory
    def select_directory(self) -> None:
        directory: Optional[str] = filedialog.askdirectory(title="Select Download Directory")
        if directory:
            self.download_directory = directory
            self.dir_label.config(text=directory)

    # Handle application closure
    def close_application(self) -> None:
        active_downloads: bool = any(task["status"] == "Downloading" for task in self.queue)
        if active_downloads:
            confirm: Optional[bool] = messagebox.askyesnocancel(
                "Downloads in Progress",
                "⚠️ Some downloads are still running!\n\n"
                "Do you want to store queue and exit?"
            )
            if confirm is None:
                return
            if confirm:
                self.log("🔴 Storing queue and exiting...")
                self.queue = [task for task in self.queue if task["status"] != "Completed"]
                self.export_queue()
                self.update_queue_listbox_threadsafe()
                self.log("🔴 Exiting application...")
                for thread in threading.enumerate():
                    if thread is not threading.current_thread():
                        thread.join(timeout=0.1)
                sys.exit()
            else:
                self.log("🔴 Exiting without saving")
                for thread in threading.enumerate():
                    if thread is not threading.current_thread():
                        thread.join(timeout=0.1)
                sys.exit()
        self.log("🔴 Closing application...")
        self.master.destroy()
        sys.exit()

    # Minimize application to system tray
    def minimize_to_tray(self) -> None:
        self._show_tray_icon()
        self.master.withdraw()

    # Show system tray icon
    def _show_tray_icon(self) -> None:
        icon_path: str = os.path.join(self.base_path, "assets", "logo.ico")
        try:
            image: Image.Image = Image.open(icon_path)
            menu: Menu = Menu(
                TrayMenuItem('Show App', self._restore_window, default=True),
                TrayMenuItem('Exit', self.close_application),
            )
            self.tray_icon = PyStrayIcon("YT-DLP GUI", image, "Running in Background", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except FileNotFoundError as e:
            self.log(f"❌ Error loading tray icon: {e}", level="error")
            messagebox.showerror("Error", f"Could not load tray icon: {e}\nThe application will continue without a system tray icon.")
            self.master.deiconify()

    # Restore window from system tray
    def _restore_window(self, icon: Any, item: Any) -> None:
        self.master.after(0, self.master.deiconify)
        self.master.after(0, self.master.focus_force)
        self.master.state('zoomed')
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None