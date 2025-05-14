# widgets.py
# This module defines the settings window for configuring yt-dlp download options,
# including tabs for format, file naming, subtitles, and more.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog,scrolledtext
import json
import os
from typing import Dict, Optional, Union

class SettingsWindow:
    """A window for configuring yt-dlp download settings with a tabbed interface."""

    def __init__(self, master: tk.Tk, initial_options: Optional[Dict] = None, global_change: bool = False) -> None:
        self.master = tk.Toplevel(master)
        if global_change:
            self.master.title("Global yt-dlp Settings")
        else:
            self.master.title("yt-dlp Settings")
        self.master.geometry("1000x700")
        self.master.transient(master)
        self.master.grab_set()

        self.widgets: Dict[str, Union[tk.Entry, tk.BooleanVar, Dict[str, tk.Spinbox], ttk.Combobox]] = {}
        self.initial_options = initial_options or {}
        self.is_loading = False
        self.preset_dir = "settings_presets"

        os.makedirs(self.preset_dir, exist_ok=True)

        self.main_panel = ttk.Panedwindow(self.master, orient=tk.HORIZONTAL)
        self.main_panel.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a left panel for Settings and buttons
        self.left_panel = ttk.Frame(self.main_panel)
        self.left_panel.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)

        # Create a right panel for preview
        self.right_panel = ttk.Frame(self.main_panel)
        self.right_panel.pack(side=tk.RIGHT, fill="both", padx=10, pady=10)
        self.main_panel.add(self.left_panel, weight=1)
        self.main_panel.add(self.right_panel, weight=1)

        # Create a preview ScrolledText box in the right panel
        self.preview_text = scrolledtext.ScrolledText(master=self.right_panel, wrap=tk.WORD,background="#222",foreground="white")
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_text.insert("1.0", "Settings Preview:\n")
        self.preview_text.insert("2.0", json.dumps(initial_options, indent=4) if initial_options else "No settings loaded.")
        self.preview_text.config(state="disabled")
        self.ydl_opts = initial_options or {}
        self.notebook_frame = ttk.Frame(self.left_panel)
        self.notebook_frame.pack(side=tk.TOP, fill="both", expand=True, padx=10, pady=10)
        # Create a frame for the buttons at the bottom of the window
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        #Buttons to save and load presets and to cancel the process in between
        ttk.Button(button_frame, text="Save Preset", command=self.save_preset).pack(side=tk.LEFT, padx=5)
        # Dropdown in button_frame
        self.preset_var = tk.StringVar()
        self.preset_dropdown = ttk.Combobox(button_frame, textvariable=self.preset_var, state="readonly")
        self.preset_dropdown.pack(side=tk.LEFT, padx=5)
        self.preset_dropdown.bind("<<ComboboxSelected>>", self.on_preset_selected)

        ttk.Button(button_frame, text="Save", command=self.save_and_close).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        # Bind the close event to save the settings
        self.master.protocol("WM_DELETE_WINDOW", self.cancel)
        # Create a frame for the notebook tabs
        # Initialize the notebook tabs
        self.notebook = ttk.Notebook(self.notebook_frame)        
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", lambda event: [self.load_values(), self.update_preview()])
        self.video_exts = ["mp4", "webm", "mkv", "flv", "avi"]
        self.audio_exts = ["mp3", "m4a", "aac", "wav", "ogg", "opus"]
        self.final_ext_options = ['original'] + self.video_exts + self.audio_exts
        # Create the tabs and add them to the notebook
        self.tabs = {
            "Format and Quality": ttk.Frame(self.notebook),
            "File and Naming Options": ttk.Frame(self.notebook),
            "Subtitles and Metadata": ttk.Frame(self.notebook),
            "Download Behavior": ttk.Frame(self.notebook),
            "SponsorBlock & Skipping": ttk.Frame(self.notebook),
            "Miscellaneous Settings": ttk.Frame(self.notebook)
        }

        for name, frame in self.tabs.items():
            self.notebook.add(frame, text=name)

        self.build_format_and_quality_tab()
        self.build_file_naming_tab()
        self.build_subtitles_metadata_tab()
        self.build_download_behavior_tab()
        self.build_sponsorblock_tab()
        self.build_miscellaneous_tab()
        self.refresh_preset_list()
        self.load_values()
        self.update_preview(initial_options)

    def refresh_preset_list(self):
        files = [f[:-5] for f in os.listdir(self.preset_dir) if f.endswith(".json")]
        self.preset_dropdown["values"] = files + ["New/Unsaved"]
        self.preset_var.set("New/Unsaved")
    def on_preset_selected(self, event=None):
        name = self.preset_var.get()
        if name == "New/Unsaved":
            return
        path = os.path.join(self.preset_dir, f"{name}.json")
        try:
            with open(path, "r") as f:
                self.is_loading = True
                self.ydl_opts = json.load(f)
            self.load_values()
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preset: {e}")
        finally:
            self.is_loading = False


    def add_browse_dir(self, parent, key, label, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent)
        entry.insert(0, self.ydl_opts.get(key, ""))
        entry.grid(row=row, column=1, sticky="ew", padx=10)
        parent.columnconfigure(1, weight=1)

        def browse():
            folder = filedialog.askdirectory()
            if folder:
                entry.delete(0, tk.END)
                entry.insert(0, folder)

        ttk.Button(parent, text="Browse", command=browse).grid(row=row, column=2, padx=5)
        self.widgets[key] = entry

    def add_labeled_entry(self, parent, label, row, default="", tooltip=""):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=2)
        entry = ttk.Entry(parent)
        entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="ew", padx=10)
        if tooltip:
            ttk.Label(parent, text=tooltip, foreground="gray", wraplength=500).grid(row=row+1, column=0, columnspan=2, sticky="w", padx=10)
        self.bind_live_update(entry)
        return entry

    def add_checkbox(self, parent, label, key, row, tooltip=""):
        var = tk.BooleanVar()
        chk = ttk.Checkbutton(parent, text=label, variable=var)
        chk.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        if tooltip:
            ttk.Label(parent, text=tooltip, foreground="gray", wraplength=500).grid(row=row+1, column=0, columnspan=2, sticky="w", padx=10)
        self.widgets[key] = var
        self.bind_live_update(var)
        return var
    
    def add_spinbox_entry(self, parent, key, label="", row=0, min_value=0, max_value=1000, default=0, tooltip=""):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=2)
        spinbox = tk.Spinbox(parent, from_=min_value, to=max_value, width=5)
        spinbox.delete(0, tk.END)
        spinbox.insert(0, str(default))
        spinbox.grid(row=row, column=1, sticky="ew", padx=10)
        if tooltip:
            ttk.Label(parent, text=tooltip, foreground="gray", wraplength=500).grid(row=row+1, column=0, columnspan=2, sticky="w", padx=10)
        self.widgets[key] = {"widget": spinbox, "default": default}
        self.bind_live_update(spinbox)
        return spinbox

    def build_format_and_quality_tab(self):

        tab = self.tabs["Format and Quality"]
        tab.columnconfigure(1, weight=1)
        row = 0

        ttk.Label(tab, text="Format:").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        format_options = {
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
            "Custom (enter below)": "Custom"
        }

        self.format_var = tk.StringVar(value="Best Video+Audio (Muxed)")
        self.bind_live_update(self.format_var)
        self.widgets['format_dropdown'] = ttk.Combobox(tab, textvariable=self.format_var, values=list(format_options.keys()))
        self.widgets['format_dropdown'].grid(row=row, column=1, sticky="ew", padx=10)
        row += 1

        # Tooltip
        ttk.Label(tab, text="Select how yt-dlp chooses formats. Use '+' to combine streams, '/' for fallback.", foreground="gray", wraplength=500).grid(row=row, column=0, columnspan=2, sticky="w", padx=10)
        row += 1

        # Custom format entry
        self.widgets['format'] = ttk.Entry(tab)
        self.widgets['format'].insert(0, format_options["Best (Video+Audio)"])
        self.widgets['format'].grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=2)
        row += 1

        # Final Extension Dropdown
        ttk.Label(tab, text="Final Extension:").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        self.final_ext_var = tk.StringVar(value="original")
        self.bind_live_update(self.final_ext_var)
        self.widgets['final_ext'] = ttk.Combobox(
            tab, textvariable=self.final_ext_var,
            values=self.final_ext_options,
            state="readonly"
        )
        self.widgets['final_ext'].grid(row=row, column=1, sticky="ew", padx=10)
        row += 1

        ttk.Label(tab, text="Expected final extension; helps detect when the file was already downloaded/converted.",
                  foreground="gray", wraplength=500).grid(row=row, column=0, columnspan=2, sticky="w", padx=10)
        row += 1


        # Sync dropdown and entry
        def update_format_entry(event=None):
            selected_label = self.format_var.get()
            value = format_options.get(selected_label, )
            if selected_label != "Custom (enter below)":
                self.widgets['format'].delete(0, tk.END)
                self.widgets['format'].insert(0, value)
            # Adapt final extension options
            if "Audio" in selected_label and not "Video" in selected_label:
                self.widgets['final_ext']['values'] = ["original"] + self.audio_exts
                self.widgets['final_ext'].set("original")  # Set default to "original"
            elif "Video" in selected_label or "Quality" in selected_label or "MP4" in selected_label:
                self.widgets['final_ext']['values'] = ["original"] + self.video_exts
                self.widgets['final_ext'].set("original")  # Set default to "original"
            else:
                self.widgets['final_ext']['values'] = ["original"] + self.video_exts + self.audio_exts  # fallback
                self.widgets['final_ext'].set("original")  # Set default to "original"
        self.widgets['format_dropdown'].bind("<<ComboboxSelected>>", update_format_entry)

        self.widgets['allow_unplayable_formats'] = self.add_checkbox(
            tab, "Allow unplayable formats", 'allow_unplayable_formats', row,
            tooltip="Allow unplayable formats to be extracted and downloaded."
        ); row += 2

        self.widgets['ignore_no_formats_error'] = self.add_checkbox(
            tab, "Ignore 'No video formats' error", 'ignore_no_formats_error', row,
            tooltip="Useful for extracting metadata even if the video is not downloadable."
        ); row += 2

        self.widgets['format_sort'] = self.add_labeled_entry(
            tab, "Format Sort:", row,
            tooltip="Comma-separated list of fields to sort formats. See 'Sorting Formats' in yt-dlp docs."
        ); row += 2

        self.widgets['format_sort_force'] = self.add_checkbox(
            tab, "Force format sort", 'format_sort_force', row,
            tooltip="Force use of the given format_sort over default sorting."
        ); row += 2

        self.widgets['prefer_free_formats'] = self.add_checkbox(
            tab, "Prefer free formats", 'prefer_free_formats', row,
            tooltip="Prefer free containers over non-free ones of the same quality."
        ); row += 2

        self.widgets['allow_multiple_video_streams'] = self.add_checkbox(
            tab, "Allow multiple video streams", 'allow_multiple_video_streams', row,
            tooltip="Merge multiple video streams into a single file."
        ); row += 2

        self.widgets['allow_multiple_audio_streams'] = self.add_checkbox(
            tab, "Allow multiple audio streams", 'allow_multiple_audio_streams', row,
            tooltip="Merge multiple audio streams into a single file."
        )

    def build_file_naming_tab(self):
        tab = self.tabs["File and Naming Options"]
        tab.columnconfigure(1, weight=1)
        row = 0

        # Custom folder override per file
        self.add_browse_dir(tab, "custom_file_path", "Per-file Custom Folder (Optional):", row)
        row += 2

        # Restrict filenames (ASCII only)
        self.add_checkbox(tab, key="restrictfilenames",label="Restrict file name", tooltip="Do not allow '&' and spaces in file names",row= row)
        row += 2

        # Windows-safe filenames
        self.add_checkbox(tab, label="Compatible with windows file naming system",key="windowsfilenames", tooltip="Use Windows-Compatible Filenames", row=row)
        row += 2

        # Trim filename to limit
        self.add_spinbox_entry(tab, key="trim_file_name",label="trim file name to characters", tooltip="Limit the filename length (excluding extension) to the specified number of characters", row=row)
        row += 2

        # Force exact filename
        self.add_labeled_entry(tab, "force_filename", tooltip="Force Output Filename (no ext):", row=row)
        row += 2


    def build_subtitles_metadata_tab(self):
        container = self.tabs["Subtitles and Metadata"]

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tab = scrollable_frame  # redirect tab to build into this
        tab.columnconfigure(1, weight=1)
        row = 0

        # Download subtitles checkbox
        self.add_checkbox(
            tab, "Download Subtitles", "writesubtitles", row,
            tooltip="Download subtitles if available."
        ); row += 2

        # Download auto-generated subtitles checkbox
        self.add_checkbox(
            tab, "Download Auto-generated Subtitles", "writeautomaticsub", row,
            tooltip="Download automatically generated subtitles (YouTube only)."
        ); row += 2

        # Embed subtitles checkbox
        self.add_checkbox(
            tab, "Embed Subtitles in Media File", "embedsubtitles", row,
            tooltip="Embed subtitles into the downloaded video file using ffmpeg."
        ); row += 2

        # Subtitle languages entry
        self.widgets['subtitleslangs'] = self.add_labeled_entry(
            tab, "Subtitle Languages:", row,
            tooltip="Comma-separated list of languages (e.g., en,es,fr). Use 'all' to download all available."
        ); row += 2

        # Write metadata checkbox
        self.add_checkbox(
            tab, "Add Metadata into file properties", "addmetadata", row,
            tooltip="Write metadata such as title, artist, etc. into the media file using ffmpeg."
        ); row += 2

        #write thumbnail checkbox
        self.add_checkbox(
            tab, "Write Thumbnail to File", "writethumbnail", row,
            tooltip="Download Thumbnail file in same folder as video file.\n Must select if Embed Thumbnail is selected."
        ); row += 2

        # Embed thumbnail checkbox
        self.add_checkbox(
            tab, "Embed Thumbnail in File", "embedthumbnail", row,
            tooltip=" Embed thumbnail image please select Write Thumbnail to file to avoid conflicts."
        ); row += 2

        # Write description checkbox
        self.add_checkbox(
            tab, "Write Video Description to File", "writedescription", row,
            tooltip="Write the full video description to a separate .description file."
        ); row += 2
    
        self.widgets['writeinfojson'] = self.add_checkbox(
            tab, "Write Metadata to JSON", "writeinfojson", row,
            tooltip="Write comments to a JSON file. Requires Download Comments to be enabled."
        ); row += 2

        # -- Download Comments Section --
        self.widgets['getcomments'] = self.add_checkbox(
            tab, "Download Comments (YouTube only)", "getcomments", row,
            tooltip="Fetch top-level YouTube comments. Requires Metadata to JSON to be enabled.\n May download a lot of data even after the max comments is set."
        ); row += 2

        self.add_spinbox_entry(
            tab, key="max_comments", label="Max Comments:", row=row,
            min_value=10, max_value=1000, default=100,
            tooltip="Limit number of top-level comments to fetch. Not always Work use with caution."
        ); row += 2
        self.add_spinbox_entry(
            tab,key="max_parents", label="Max Parent Comments:", row=row,default=10,
            tooltip="Limit number of parent comments to fetch. Not always Work use with caution."
        ); row += 2
        self.add_spinbox_entry(
            tab,key="max_replies", label="Max replies Comments:", row=row,default=10,
            tooltip="Limit number of replies to fetch. Not always Work use with caution."
        ); row += 2

        self.widgets['comments_sort'] = ttk.Combobox(tab, state="readonly", values=["top", "new", "relevance"])
        self.widgets['comments_sort'].set("top")
        ttk.Label(tab, text="Comment Sort Order:").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        self.widgets['comments_sort'].grid(row=row, column=1, sticky="ew", padx=10)
        self.bind_live_update(self.widgets['comments_sort']); row += 2

        # Write annotations (legacy)
        self.add_checkbox(
            tab, "Download Annotations (legacy)", "writeannotations", row,
            tooltip="Download video annotations (legacy YouTube support only)."
        ); row += 2

    def build_download_behavior_tab(self):
        tab = self.tabs["Download Behavior"]
        tab.columnconfigure(1, weight=1)
        row = 0

        self.add_checkbox(
            tab, "Continue Partially Downloaded Files", "continue_dl", row,
            tooltip="Resume partially downloaded files instead of starting over."
        ); row += 2

        self.widgets['download_archive'] = self.add_labeled_entry(
            tab, "Download Archive File Path:", row,
            tooltip="Path to a file where IDs of already downloaded videos are stored."
        ); row += 2

        self.add_spinbox_entry(
            tab, "retries", label="Retry Attempts:", row=row,
            min_value=0, max_value=10, default=3,
            tooltip="Number of times to retry for a failed download."
        ); row += 2

        self.add_spinbox_entry(
            tab, "fragment_retries", label="Fragment Retry Attempts:", row=row,
            min_value=0, max_value=10, default=3,
            tooltip="Number of retries for each video fragment (if segmented)."
        ); row += 2

        self.widgets['ratelimit'] = self.add_labeled_entry(
            tab, "Download Rate Limit (e.g., 500K or 2M):", row,
            tooltip="Limit download speed (e.g., 500K for 500 Kilobytes/sec, 2M for 2 Megabytes/sec)."
        ); row += 2

        self.add_checkbox(
            tab, "Skip Unavailable Fragments", "skip_unavailable_fragments", row,
            tooltip="If a video fragment is missing, skip it instead of failing."
        ); row += 2

    def build_miscellaneous_tab(self):
        tab = self.tabs["Miscellaneous Settings"]
        tab.columnconfigure(1, weight=1)
        row = 0
         # Verbose / Quiet output mode (radio buttons)
        ttk.Label(tab, text="Output Mode:").grid(row=row, column=0, sticky="w", padx=10, pady=(10, 0))
        self.output_mode = tk.StringVar(value="normal")
        output_modes = [("Normal Output", "normal"), ("Verbose Output", "verbose"), ("Quiet Output", "quiet")]
        for text, val in output_modes:
            ttk.Radiobutton(tab, text=text, variable=self.output_mode, value=val).grid(row=row, column=1, sticky="w", padx=10)
            row += 1

        self.widgets['output_mode'] = self.output_mode
        self.bind_live_update(self.output_mode)
        self.add_checkbox(
            tab, "Ignore Errors", "ignoreerrors", row,
            tooltip="Continue downloading even if some downloads fail."
        ); row += 2

        self.add_checkbox(
            tab, "No Overwrites", "nooverwrites", row,
            tooltip="Skip downloads if the file already exists."
        ); row += 2

        self.add_checkbox(
            tab, "Download in Background", "concurrent_fragment_downloads", row,
            tooltip="Allow downloading fragments in parallel to speed up downloads."
        ); row += 2

        self.widgets['user_agent'] = self.add_labeled_entry(
            tab, "Custom User Agent:", row,
            tooltip="Override the user-agent string sent with requests."
        ); row += 2

        self.widgets['referer'] = self.add_labeled_entry(
            tab, "Referer Header:", row,
            tooltip="Set a custom HTTP referer header. Useful for some sites."
        ); row += 2

        self.widgets['sleep_interval'] = self.add_spinbox_entry( parent=tab, key="sleep_interval", label="Sleep Interval:", row=row,
            min_value=0, default=0,tooltip="Number of seconds to sleep before each download."); row += 2

        self.widgets['source_address'] = self.add_labeled_entry(
            tab, "Source Address:", row,
            tooltip="Client-side IP address to bind to for outgoing connections."
        ); row += 2


    def build_sponsorblock_tab(self):
        tab = self.tabs["SponsorBlock & Skipping"]
        tab.columnconfigure(0, weight=1)

        # Create two separate frames: one for category checkboxes and one for inputs
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        middle_label = ttk.Label(tab, text="Adds chapter markers for selected segment types (e.g. sponsor, intro) without removing them.", font=("Arial", 8))
        middle_label.pack(pady=5)

        bottom_frame = ttk.Frame(tab)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=10)
        bottom_frame.columnconfigure(1, weight=1)

        categories = [
            "sponsor", "intro", "outro", "selfpromo", "interaction",
            "music_offtopic", "preview", "filler", "exclusive_access",
            "poi_highlight", "poi_nonhighlight"
        ]

        # SponsorBlock Remove
        row = 0
        ttk.Label(top_frame, text="Remove Categories:").grid(row=row, column=0, sticky="w", pady=5)
        self.widgets['sponsorblock_remove'] = {}
        column = 1
        for cat in categories:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(top_frame, text=cat, variable=var)
            self.bind_live_update(var)
            chk.grid(row=row, column=column, sticky="w", padx=5)
            self.widgets['sponsorblock_remove'][cat] = var
            column += 1
            if column > 5:
                column = 1
                row += 1
        row += 1

        # SponsorBlock Mark
        ttk.Label(top_frame, text="Mark Categories:").grid(row=row, column=0, sticky="w", pady=5)
        self.widgets['sponsorblock_mark'] = {}
        column = 1
        for cat in categories:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(top_frame, text=cat, variable=var)
            self.bind_live_update(var)
            chk.grid(row=row, column=column, sticky="w", padx=5)
            self.widgets['sponsorblock_mark'][cat] = var
            column += 1
            if column > 5:
                column = 1
                row += 1

        # Chapter title format
        self.widgets['sponsorblock_chapter_title'] = self.add_labeled_entry(
            bottom_frame, "Chapter Title Format:", 0,
            tooltip="Custom format for SponsorBlock chapters (e.g., [Sponsor: {start}–{end}])"
        )

        # Custom API endpoint
        self.widgets['sponsorblock_api'] = self.add_labeled_entry(
            bottom_frame, "SponsorBlock API URL:", 2,
            tooltip="Alternative API endpoint (default is https://sponsor.ajay.app)"
        )

        # Remove silent
        self.add_checkbox(
            bottom_frame, "Silent Remove if No Segments", "sponsorblock_remove_silent", 4,
            tooltip="Do not show error if SponsorBlock segments are not found."
        )

        # Allow querying
        self.add_checkbox(
            bottom_frame, "Allow SponsorBlock Querying", "sponsorblock_query", 6,
            tooltip="Enable SponsorBlock querying even if no removal/marking is specified."
        )

    # code for dynamic updating and saving of settings 
    def bind_live_update(self, widget: Union[tk.Entry, tk.BooleanVar, tk.Spinbox]) -> None:
        if isinstance(widget, ttk.Entry) or isinstance(widget, tk.Spinbox):
            widget.bind("<KeyRelease>", lambda e: self.save())
        elif isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", lambda e: self.save())
        elif isinstance(widget, tk.BooleanVar):
            widget.trace_add("write", lambda *args: self.save())
        
    def load_values(self):
        self.is_loading = True
        try:
            postprocessors = self.ydl_opts.get("postprocessors", [])
            pp_map = {pp["key"]: pp for pp in postprocessors if "key" in pp}

            # SponsorBlock categories — set early from top-level keys
            for sb_key in ("sponsorblock_remove", "sponsorblock_mark"):
                enabled = self.ydl_opts.get(sb_key, [])
                for cat_key, var in self.widgets.get(sb_key, {}).items():
                    var.set(cat_key in enabled)


            # Main widget loading
            for key, widget in self.widgets.items():
                if key in ("sponsorblock_remove", "sponsorblock_mark"):
                    continue  # already handled above

                value = self.ydl_opts.get(key)

                if key == "output_mode":
                    if self.ydl_opts.get("verbose"):
                        widget.set("verbose")
                    elif self.ydl_opts.get("quiet"):
                        widget.set("quiet")
                    else:
                        widget.set("normal")

                elif isinstance(widget, tk.BooleanVar):
                    widget.set(bool(value))

                elif isinstance(widget, ttk.Combobox):
                    if key == "format":
                        # Special handling for format dropdown
                        if value in self.format_var.get():
                            widget.set(value)
                        else:
                            widget.set("Custom (enter below)")
                    elif key == "final_ext":
                        widget.set(value if value and value in self.final_ext_options else "original")
                    else:
                        widget.set(str(value) if value is not None else "")

                elif isinstance(widget, ttk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, str(value) if value is not None else "")

                elif isinstance(widget, dict) and "widget" in widget and "default" in widget:
                    try:
                        spinbox = widget["widget"]
                        default_value = widget["default"]  # Fetch the default value from the dictionary
                        spinbox.delete(0, tk.END)
                        spinbox.insert(0, int(value) if value is not None else int(default_value))
                    except ValueError:
                        spinbox.delete(0, tk.END)
                        spinbox.insert(0, default_value)

            # Postprocessor-related states
            if "FFmpegMetadata" in pp_map:
                self.widgets.get("addmetadata", tk.BooleanVar()).set(pp_map["FFmpegMetadata"].get("add_metadata", False))
                self.widgets.get("add_chapters", tk.BooleanVar()).set(pp_map["FFmpegMetadata"].get("add_chapters", False))

            if "FFmpegExtractAudio" in pp_map:
                self.widgets.get("final_ext", ttk.Combobox()).set(pp_map["FFmpegExtractAudio"].get("preferredcodec", ""))

            elif "FFmpegVideoConvertor" in pp_map:
                self.widgets.get("final_ext", ttk.Combobox()).set(pp_map["FFmpegVideoConvertor"].get("preferedformat", ""))

            if "EmbedThumbnail" in pp_map:
                self.widgets.get("embedthumbnail", tk.BooleanVar()).set(True)
                self.widgets.get("writethumbnail", tk.BooleanVar()).set(True)

            # Load SponsorBlock API — from any matching pp with "api"
            for pp in postprocessors:
                if pp.get("key") == "SponsorBlock" and "api" in pp:
                    self.widgets.get("sponsorblock_api", ttk.Entry()).delete(0, tk.END)
                    self.widgets.get("sponsorblock_api", ttk.Entry()).insert(0, pp.get("api"))
                    break  # only load first matching one            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load values: {e}")
        finally:
            self.is_loading = False
            self.update_preview(self.ydl_opts)
            
    def get_ydl_opts(self):
        opts = {}
        postprocessors = []

        #Handling sponsorblock out of main loop
        sponsorblock_remove = []
        sponsorblock_mark = []
        for key, widget in self.widgets.get("sponsorblock_remove", {}).items():
            if widget.get():
                sponsorblock_remove.append(key)
        for key, widget in self.widgets.get("sponsorblock_mark", {}).items():
            if widget.get():
                sponsorblock_mark.append(key)
        if sponsorblock_remove:
            opts["sponsorblock_remove"] = sponsorblock_remove
        if sponsorblock_mark:
            opts["sponsorblock_mark"] = sponsorblock_mark
        # 1. Collect from widgets
        for key, widget in self.widgets.items():
            if key == "sponsorblock_remove" or key == "sponsorblock_mark":
                continue
            elif key == "output_mode":
                mode = widget.get()
                if mode == "verbose":
                    opts["verbose"] = True
                elif mode == "quiet":
                    opts["quiet"] = True

            elif key == "embedsubtitles" and widget.get() and not opts.get("writesubtitles"):
                opts["writesubtitles"] = True
                opts["embedsubtitles"] = True

            elif isinstance(widget, tk.BooleanVar):
                if isinstance(widget, tk.BooleanVar):
                    opts[key] = widget.get()
                
            elif isinstance(widget, dict) and "widget" in widget and "default" in widget:
                spinbox = widget["widget"]
                default_value = widget["default"]
                try:
                    opts[key] = int(spinbox.get().strip()) if spinbox.get().strip() else default_value
                except ValueError:
                    opts[key] = default_value

            elif isinstance(widget, ttk.Entry):
                value = widget.get().strip()
                if value:
                    opts[key] = value

            elif isinstance(widget, ttk.Combobox):
                value = widget.get().strip()
                if key == "final_ext" and value == "original":
                    opts[key] = None  # Explicitly set to None for "original"
                elif value:
                    opts[key] = value
        #manage commnets if getcomments is selected then only max_comments and comments_sort will be selected
        if opts.get("getcomments"):
            opts["writeinfojson"] = True
            opts["extractor_args"] = {
                "youtube": {
                    "max_comments": [
                        str(opts.get('max_comments','100')),# Max number of comments to fetch
                        str(opts.get('max_parents')),# Max number of parent comments to fetch
                        str(opts.get('max_replies')),# Max number of replies to fetch
                    ],
                }
            }

        else:
            opts.pop("max_comments", None)
            opts.pop("comments_sort", None)
        # 2. Postprocessors

        final_ext = opts.get("final_ext",None).lower()
        format_choice = opts.get("format", "").lower()

        if final_ext and final_ext != "original":
            if final_ext in self.audio_exts:
                quality = "5"
                if "best" in format_choice:
                    quality = "0"
                elif "smallest" in format_choice:
                    quality = "9"
                postprocessors.append({
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": final_ext,
                    "preferredquality": quality
                })
            elif final_ext in self.video_exts:
                postprocessors.append({
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": final_ext
                })
            elif final_ext == "original" or not final_ext:
                final_ext = None

        # Metadata
        if opts.get("addmetadata") or opts.get("add_chapters") or opts.get("sponsorblock_mark") or opts.get("sponsorblock_remove"):
            meta_pp = {"key": "FFmpegMetadata"}
            if opts.get("addmetadata"):
                meta_pp["add_metadata"] = True
            if opts.get("add_chapters") or opts.get("sponsorblock_mark") or opts.get("sponsorblock_remove"):
                meta_pp["add_metadata"] = True
                meta_pp["add_chapters"] = True
            postprocessors.append(meta_pp)

        #EmbedSubtitles
        if opts.get("embedsubtitles") and opts.get("writesubtitles"):
            postprocessors.append({
                'key': 'FFmpegEmbedSubtitle',
            })

        #Sponsorblock Segment ensuring we don't have empty values in the list and we do not Repeat same code Twice
        if opts.get("sponsorblock_remove") or opts.get("sponsorblock_mark"):
            postprocessors.append({
                "key": "SponsorBlock",
                "api": opts.get("sponsorblock_api", "https://sponsor.ajay.app"),
                "categories": opts.get("sponsorblock_mark", []) + opts.get("sponsorblock_remove", []),
                "when":"after_filter"
            })
            postprocessors.append({
                "key":"ModifyChapters",
                "sponsorblock_chapter_title":opts.get("sponsorblock_chapter_title",'[SponsorBlock]: %(category_names)l'),
                'remove_chapters_patterns': [],
                'remove_ranges': [],                
                'remove_sponsor_segments': opts.get("sponsorblock_remove", []),
            })

        # Embed
        if opts.get("embedthumbnail"):
            if not opts.get("writethumbnail", False):
                opts["writethumbnail"] = True
            postprocessors.append({"key": "EmbedThumbnail"})

        if postprocessors:
            opts["postprocessors"] = postprocessors

        return opts


    def update_preview(self, opts: Optional[Dict]=None):
        if hasattr(self, "preview_text"):
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", json.dumps(opts or self.ydl_opts, indent=4))
            self.preview_text.config(state="disabled")

    def save(self):
        if self.is_loading:
            return
        opts = self.get_ydl_opts()
        self.ydl_opts = opts
        self.update_preview(opts)
        self.mark_as_unsaved_if_modified()

    def save_and_close(self):
        self.save()
        self.master.destroy()

    def cancel(self):
        self.master.destroy()
        self.master.grab_release()
        self.ydl_opts = self.initial_options or {}

    def mark_as_unsaved_if_modified(self):
        current_name = self.preset_var.get()
        if current_name in ["New/Unsaved", ""]:
            return  # Already unsaved
        try:
            with open(os.path.join(self.preset_dir, f"{current_name}.json")) as f:
                saved_opts = json.load(f)
            if saved_opts != self.ydl_opts:
                self.preset_var.set("New/Unsaved")
        except:
            self.preset_var.set("New/Unsaved")
        
    def save_preset(self):
        name = self.preset_var.get()
        if name in ["", "New/Unsaved"]:
            name = tk.simpledialog.askstring("Save Preset", "Enter preset name:")
        if not name:
            return
        file_path = os.path.join(self.preset_dir, f"{name}.json")
        with open(file_path, "w") as f:
            json.dump(self.get_ydl_opts(), f, indent=4)
        messagebox.showinfo("Saved", f"Preset '{name}' saved successfully.")
        self.refresh_preset_list()
        self.preset_var.set(name)

def show_settings_window(master, initial_options: Optional[Dict] = None,is_global: bool =False) -> Dict:
    """
    Show the settings window and return the selected options.
    :param master: The parent window.
    :param initial_options: Initial options to load into the settings window.
    :param global_change: If True, the settings window will be treated as a global change.
    :return: The selected options from the settings window.
    """
    settings_window = SettingsWindow(master, initial_options,global_change=is_global)
    master.wait_window(settings_window.master)
    if settings_window.ydl_opts == {} or settings_window.ydl_opts == initial_options:
        return initial_options
    else:
    # Return the final options
        return settings_window.ydl_opts
    
# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    options = show_settings_window(root, is_global=True)
    print("Selected Options:", options)
    root.mainloop()