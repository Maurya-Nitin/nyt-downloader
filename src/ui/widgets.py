# widgets.py
# This module defines the settings window for configuring yt-dlp download options,
# including tabs for format, file naming, subtitles, and more.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
from typing import Dict, Optional, Union


class SettingsWindow:
    """A window for configuring yt-dlp download settings with a tabbed interface."""
    
    def __init__(self, parent: tk.Tk, initial_options: Optional[Dict] = None, is_global: bool = False) -> None:
        """Initialize the settings window with tabs and controls."""
        self.window = tk.Toplevel(parent)
        self.window.title("Global yt-dlp Settings" if is_global else "yt-dlp Settings")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.widgets: Dict[str, Union[tk.Entry, tk.BooleanVar, Dict[str, tk.Spinbox], ttk.Combobox]] = {}
        self.initial_options = initial_options or {}
        self.is_loading = False
        self.preset_directory = "settings_presets"
        os.makedirs(self.preset_directory, exist_ok=True)
        
        self.main_panel = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        self.main_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.left_panel = ttk.Frame(self.main_panel)
        self.left_panel.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)
        
        self.right_panel = ttk.Frame(self.main_panel)
        self.right_panel.pack(side=tk.RIGHT, fill="both", padx=10, pady=10)
        
        self.main_panel.add(self.left_panel, weight=1)
        self.main_panel.add(self.right_panel, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(master=self.right_panel, wrap=tk.WORD, background="#222", foreground="white")
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_text.insert("1.0", "Settings Preview:\n")
        self.preview_text.insert("2.0", json.dumps(initial_options, indent=4) if initial_options else "No settings loaded.")
        self.preview_text.config(state="disabled")
        
        self.ydl_options = initial_options or {}
        
        self.notebook_frame = ttk.Frame(self.left_panel)
        self.notebook_frame.pack(side=tk.TOP, fill="both", expand=True, padx=10, pady=10)
        
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save Preset", command=self._save_preset).pack(side=tk.LEFT, padx=5)
        self.preset_var = tk.StringVar()
        self.preset_dropdown = ttk.Combobox(button_frame, textvariable=self.preset_var, state="readonly")
        self.preset_dropdown.pack(side=tk.LEFT, padx=5)
        self.preset_dropdown.bind("<<ComboboxSelected>>", self._on_preset_selected)
        
        ttk.Button(button_frame, text="Save", command=self._save_and_close).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=5)
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)
        
        self.notebook = ttk.Notebook(self.notebook_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", lambda event: [self._load_values(), self._update_preview()])
        
        self.video_extensions = ["mp4", "webm", "mkv", "flv", "avi"]
        self.audio_extensions = ["mp3", "m4a", "aac", "wav", "ogg", "opus"]
        self.final_extension_options = ['original'] + self.video_extensions + self.audio_extensions
        
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
        
        self._build_format_and_quality_tab()
        self._build_file_naming_tab()
        self._build_subtitles_metadata_tab()
        self._build_download_behavior_tab()
        self._build_sponsorblock_tab()
        self._build_miscellaneous_tab()
        self._refresh_preset_list()
        self._load_values()
        self._update_preview(initial_options)

    def _refresh_preset_list(self) -> None:
        """Update the preset dropdown with available preset files."""
        files = [f[:-5] for f in os.listdir(self.preset_directory) if f.endswith(".json")]
        self.preset_dropdown["values"] = files + ["New/Unsaved"]
        self.preset_var.set("New/Unsaved")

    def _on_preset_selected(self, event: Optional[tk.Event] = None) -> None:
        """Load settings from the selected preset file."""
        name = self.preset_var.get()
        if name == "New/Unsaved":
            return
        path = os.path.join(self.preset_directory, f"{name}.json")
        try:
            with open(path, "r") as f:
                self.is_loading = True
                self.ydl_options = json.load(f)
            self._load_values()
            self._update_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preset: {e}")
        finally:
            self.is_loading = False

    def _add_browse_directory(self, parent: ttk.Frame, key: str, label: str, row: int) -> None:
        """Add a directory selection widget with a browse button."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent)
        entry.insert(0, self.ydl_options.get(key, ""))
        entry.grid(row=row, column=1, sticky="ew", padx=10)
        parent.columnconfigure(1, weight=1)
        
        def _browse() -> None:
            folder = filedialog.askdirectory()
            if folder:
                entry.delete(0, tk.END)
                entry.insert(0, folder)
        
        ttk.Button(parent, text="Browse", command=_browse).grid(row=row, column=2, padx=5)
        self.widgets[key] = entry

    def _add_labeled_entry(self, parent: ttk.Frame, label: str, row: int, default: str = "", tooltip: str = "") -> tk.Entry:
        """Add a labeled text entry widget."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=2)
        entry = ttk.Entry(parent)
        entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="ew", padx=10)
        if tooltip:
            ttk.Label(parent, text=tooltip, foreground="gray", wraplength=500).grid(row=row+1, column=0, columnspan=2, sticky="w", padx=10)
        self._bind_live_update(entry)
        return entry

    def _add_checkbox(self, parent: ttk.Frame, label: str, key: str, row: int, tooltip: str = "") -> tk.BooleanVar:
        """Add a checkbox widget."""
        var = tk.BooleanVar()
        chk = ttk.Checkbutton(parent, text=label, variable=var)
        chk.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        if tooltip:
            ttk.Label(parent, text=tooltip, foreground="gray", wraplength=500).grid(row=row+1, column=0, columnspan=2, sticky="w", padx=10)
        self.widgets[key] = var
        self._bind_live_update(var)
        return var

    def _add_spinbox_entry(self, parent: ttk.Frame, key: str, label: str = "", row: int = 0, min_value: int = 0, max_value: int = 1000, default: int = 0, tooltip: str = "") -> tk.Spinbox:
        """Add a spinbox widget for numeric input."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=2)
        spinbox = tk.Spinbox(parent, from_=min_value, to=max_value, width=5)
        spinbox.delete(0, tk.END)
        spinbox.insert(0, str(default))
        spinbox.grid(row=row, column=1, sticky="ew", padx=10)
        if tooltip:
            ttk.Label(parent, text=tooltip, foreground="gray", wraplength=500).grid(row=row+1, column=0, columnspan=2, sticky="w", padx=10)
        self.widgets[key] = {"widget": spinbox, "default": default}
        self._bind_live_update(spinbox)
        return spinbox

    def _build_format_and_quality_tab(self) -> None:
        """Configure the Format and Quality settings tab."""
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
            "Custom": "custom"
        }
        
        self.widgets["format_dropdown"] = ttk.Combobox(tab, values=list(format_options.keys()), state="readonly")
        self.widgets["format_dropdown"].grid(row=row, column=1, sticky="ew", padx=10)
        
        self.widgets["format"] = self._add_labeled_entry(
            tab, "Custom Format:", row + 2, default=self.ydl_options.get("format", ""),
            tooltip="Enter a custom yt-dlp format string (e.g., 'bestvideo+bestaudio')."
        )
        row += 4
        
        self.widgets["final_extension"] = ttk.Combobox(tab, values=self.final_extension_options, state="readonly")
        ttk.Label(tab, text="Final Extension:").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        self.widgets["final_extension"].grid(row=row, column=1, sticky="ew", padx=10)
        row += 2
        
        self.widgets["format_dropdown"].bind("<<ComboboxSelected>>", self._on_format_selected)
        
        def _update_final_extension_options(event: Optional[tk.Event] = None) -> None:
            """Update available file extensions based on selected format."""
            selected_format = self.widgets["format_dropdown"].get()
            if "Audio" in selected_format and "Video" not in selected_format:
                self.widgets["final_extension"]["values"] = ["original"] + self.audio_extensions
            elif "Video" in selected_format or selected_format in ["Best ≤720p", "Best ≤480p", "Best (Video+Audio)", "Worst Video+Audio (Muxed)"]:
                self.widgets["final_extension"]["values"] = ["original"] + self.video_extensions
            else:
                self.widgets["final_extension"]["values"] = self.final_extension_options
            self.widgets["final_extension"].set("original")
        
        self.widgets["format_dropdown"].bind("<<ComboboxSelected>>", _update_final_extension_options)
        
        self.widgets["no_streams"] = self._add_checkbox(
            tab, "No Streams", "no_streams", row,
            tooltip="Prevent automatic stream selection."
        )
        row += 2
        
        self.widgets["merge_output_format"] = self._add_labeled_entry(
            tab, "Merge Output Format:", row, default=self.ydl_options.get("merge_output_format", ""),
            tooltip="Specify the format for merged output files (e.g., mp4, mkv)."
        )

    def _on_format_selected(self, event: Optional[tk.Event] = None) -> None:
        """Update the format field based on the selected format option."""
        selected = self.widgets["format_dropdown"].get()
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
            "Custom": self.widgets["format"].get() or "best"
        }
        if selected != "Custom":
            self.widgets["format"].delete(0, tk.END)
            self.widgets["format"].insert(0, format_options.get(selected, "best"))
        self._update_ydl_options()
        self._update_preview()

    def _build_file_naming_tab(self) -> None:
        """Configure the File and Naming Options tab."""
        tab = self.tabs["File and Naming Options"]
        tab.columnconfigure(1, weight=1)
        row = 0
        self._add_browse_directory(tab, "custom_file_path", "Custom File Path:", row)
        row += 1
        self.widgets["output_template"] = self._add_labeled_entry(
            tab, "Output Template:", row, default=self.ydl_options.get("outtmpl", "%(title)s.%(ext)s"),
            tooltip="Define the output filename template (e.g., '%(title)s-%(id)s.%(ext)s')."
        )
        row += 2
        self.widgets["restrict_filenames"] = self._add_checkbox(
            tab, "Restrict Filenames", "restrict_filenames", row,
            tooltip="Restrict filenames to ASCII characters and avoid special characters."
        )
        row += 2
        self.widgets["no_overwrites"] = self._add_checkbox(
            tab, "No Overwrites", "no_overwrites", row,
            tooltip="Prevent overwriting existing files."
        )
        row += 2
        self.widgets["force_overwrites"] = self._add_checkbox(
            tab, "Force Overwrites", "force_overwrites", row,
            tooltip="Force overwriting existing files."
        )

    def _build_subtitles_metadata_tab(self) -> None:
        """Configure the Subtitles and Metadata tab."""
        tab = self.tabs["Subtitles and Metadata"]
        tab.columnconfigure(1, weight=1)
        row = 0
        self.widgets["write_subtitles"] = self._add_checkbox(
            tab, "Write Subtitles", "write_subtitles", row,
            tooltip="Download available subtitles."
        )
        row += 2
        self.widgets["write_auto_subtitles"] = self._add_checkbox(
            tab, "Write Automatic Subtitles", "write_auto_subtitles", row,
            tooltip="Download automatically generated subtitles."
        )
        row += 2
        self.widgets["embed_subtitles"] = self._add_checkbox(
            tab, "Embed Subtitles", "embed_subtitles", row,
            tooltip="Embed subtitles into the video file."
        )
        row += 2
        self.widgets["subtitle_languages"] = self._add_labeled_entry(
            tab, "Subtitle Languages:", row, default=self.ydl_options.get("subtitle_languages", "en"),
            tooltip="Comma-separated list of subtitle languages (e.g., 'en,fr')."
        )
        row += 2
        self.widgets["write_thumbnail"] = self._add_checkbox(
            tab, "Write Thumbnail", "write_thumbnail", row,
            tooltip="Download and save the video thumbnail."
        )
        row += 2
        self.widgets["embed_thumbnail"] = self._add_checkbox(
            tab, "Embed Thumbnail", "embed_thumbnail", row,
            tooltip="Embed the thumbnail into the media file."
        )
        row += 2
        self.widgets["add_metadata"] = self._add_checkbox(
            tab, "Add Metadata", "add_metadata", row,
            tooltip="Add metadata to the downloaded file."
        )
        row += 2
        self.widgets["write_info_json"] = self._add_checkbox(
            tab, "Write Info JSON", "write_info_json", row,
            tooltip="Write video metadata to a .info.json file."
        )
        row += 2
        self.widgets["extract_comments"] = self._add_checkbox(
            tab, "Extract Comments", "extract_comments", row,
            tooltip="Extract video comments and save to a file."
        )

    def _build_download_behavior_tab(self) -> None:
        """Configure the Download Behavior tab."""
        tab = self.tabs["Download Behavior"]
        tab.columnconfigure(1, weight=1)
        row = 0
        self.widgets["no_playlist"] = self._add_checkbox(
            tab, "No Playlist", "no_playlist", row,
            tooltip="Download only the video, not the entire playlist."
        )
        row += 2
        self.widgets["ignore_errors"] = self._add_checkbox(
            tab, "Ignore Errors", "ignore_errors", row,
            tooltip="Continue downloading even if some videos fail."
        )
        row += 2
        self.widgets["retries"] = self._add_spinbox_entry(
            tab, "retries", "Retries:", row, min_value=0, max_value=100, default=self.ydl_options.get("retries", 10),
            tooltip="Number of retries for failed downloads."
        )
        row += 2
        self.widgets["fragment_retries"] = self._add_spinbox_entry(
            tab, "fragment_retries", "Fragment Retries:", row, min_value=0, max_value=100, default=self.ydl_options.get("fragment_retries", 10),
            tooltip="Number of retries for failed fragments."
        )
        row += 2
        self.widgets["extractor_retries"] = self._add_spinbox_entry(
            tab, "extractor_retries", "Extractor Retries:", row, min_value=0, max_value=100, default=self.ydl_options.get("extractor_retries", 3),
            tooltip="Number of retries for extractor failures."
        )

    def _build_sponsorblock_tab(self) -> None:
        """Configure the SponsorBlock & Skipping tab."""
        tab = self.tabs["SponsorBlock & Skipping"]
        tab.columnconfigure(1, weight=1)
        row = 0
        categories = [
            "sponsor", "intro", "outro", "selfpromo", "interaction",
            "music_offtopic", "preview", "filler", "exclusive_access",
            "poi_highlight", "poi_nonhighlight"
        ]
        ttk.Label(tab, text="SponsorBlock Categories to Mark:").grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1
        for i, category in enumerate(categories):
            var = tk.BooleanVar()
            ttk.Checkbutton(tab, text=category, variable=var).grid(row=row, column=0, columnspan=2, sticky="w", padx=20)
            self.widgets[f"sponsorblock_mark_{category}"] = var
            self._bind_live_update(var)
            row += 1
        ttk.Label(tab, text="SponsorBlock Categories to Remove:").grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1
        for i, category in enumerate(categories):
            var = tk.BooleanVar()
            ttk.Checkbutton(tab, text=category, variable=var).grid(row=row, column=0, columnspan=2, sticky="w", padx=20)
            self.widgets[f"sponsorblock_remove_{category}"] = var
            self._bind_live_update(var)
            row += 1
        self.widgets["sponsorblock_chapter_title"] = self._add_labeled_entry(
            tab, "SponsorBlock Chapter Title:", row, default=self.ydl_options.get("sponsorblock_chapter_title", "[SponsorBlock]: %(category_names)l"),
            tooltip="Template for SponsorBlock chapter titles."
        )

    def _build_miscellaneous_tab(self) -> None:
        """Configure the Miscellaneous Settings tab."""
        tab = self.tabs["Miscellaneous Settings"]
        tab.columnconfigure(1, weight=1)
        row = 0
        self.widgets["verbose"] = self._add_checkbox(
            tab, "Verbose Output", "verbose", row,
            tooltip="Enable verbose output for debugging."
        )
        row += 2
        self.widgets["quiet"] = self._add_checkbox(
            tab, "Quiet Mode", "quiet", row,
            tooltip="Suppress non-error messages."
        )
        row += 2
        self.widgets["no_warnings"] = self._add_checkbox(
            tab, "No Warnings", "no_warnings", row,
            tooltip="Suppress warning messages."
        )
        row += 2
        self.widgets["simulate"] = self._add_checkbox(
            tab, "Simulate Download", "simulate", row,
            tooltip="Simulate the download without actually downloading."
        )
        row += 2
        self.widgets["keep_temp"] = self._add_checkbox(
            tab, "Keep Temporary Files", "keep_temp", row,
            tooltip="Keep temporary files after download."
        )

    def _bind_live_update(self, widget: Union[tk.Entry, tk.BooleanVar, tk.Spinbox]) -> None:
        """Bind widget changes to update ydl options and preview."""
        if isinstance(widget, tk.Entry):
            widget.bind("<KeyRelease>", lambda e: [self._update_ydl_options(), self._update_preview()])
        elif isinstance(widget, tk.BooleanVar):
            widget.trace_add("write", lambda *args: [self._update_ydl_options(), self._update_preview()])
        elif isinstance(widget, tk.Spinbox):
            widget.bind("<KeyRelease>", lambda e: [self._update_ydl_options(), self._update_preview()])
            widget.bind("<ButtonRelease-1>", lambda e: [self._update_ydl_options(), self._update_preview()])

    def _update_ydl_options(self) -> None:
        """Update the ydl options dictionary based on widget values."""
        if self.is_loading:
            return
        self.ydl_options = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, tk.Entry):
                value = widget.get().strip()
                if value:
                    self.ydl_options[key] = value
            elif isinstance(widget, tk.BooleanVar):
                self.ydl_options[key] = widget.get()
            elif isinstance(widget, dict) and "widget" in widget:
                try:
                    value = int(widget["widget"].get())
                    self.ydl_options[key] = value
                except ValueError:
                    self.ydl_options[key] = widget["default"]
            elif isinstance(widget, ttk.Combobox):
                value = widget.get()
                if value and key != "format_dropdown":
                    self.ydl_options[key] = value
        
        sponsorblock_mark = []
        sponsorblock_remove = []
        categories = [
            "sponsor", "intro", "outro", "selfpromo", "interaction",
            "music_offtopic", "preview", "filler", "exclusive_access",
            "poi_highlight", "poi_nonhighlight"
        ]
        for category in categories:
            if self.widgets.get(f"sponsorblock_mark_{category}", tk.BooleanVar()).get():
                sponsorblock_mark.append(category)
            if self.widgets.get(f"sponsorblock_remove_{category}", tk.BooleanVar()).get():
                sponsorblock_remove.append(category)
        
        if sponsorblock_mark:
            self.ydl_options["sponsorblock_mark"] = sponsorblock_mark
        if sponsorblock_remove:
            self.ydl_options["sponsorblock_remove"] = sponsorblock_remove
        
        postprocessors = []
        if self.ydl_options.get("add_metadata"):
            postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True, "add_chapters": True})
        if self.ydl_options.get("embed_thumbnail"):
            postprocessors.append({"key": "EmbedThumbnail"})
        if self.ydl_options.get("embed_subtitles"):
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})
        
        final_extension = self.ydl_options.get("final_extension")
        format_value = self.ydl_options.get("format")
        if final_extension and final_extension != "original":
            if final_extension in self.audio_extensions:
                quality = "5"
                if "best" in format_value:
                    quality = "0"
                elif "smallest" in format_value:
                    quality = "9"
                postprocessors.append({
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": final_extension,
                    "preferredquality": quality
                })
            elif final_extension in self.video_extensions:
                postprocessors.append({
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": final_extension
                })
        
        if sponsorblock_mark or sponsorblock_remove:
            postprocessors.append({
                "key": "SponsorBlock",
                "categories": sponsorblock_mark or sponsorblock_remove,
                "when": "after_filter"
            })
            postprocessors.append({
                "key": "ModifyChapters",
                "sponsorblock_chapter_title": self.ydl_options.get("sponsorblock_chapter_title", "[SponsorBlock]: %(category_names)l"),
                "remove_sponsor_segments": sponsorblock_remove if sponsorblock_remove else []
            })
        
        if postprocessors:
            self.ydl_options["postprocessors"] = postprocessors
        self.ydl_options["format_dropdown"] = self.widgets["format_dropdown"].get()

    def _load_values(self) -> None:
        """Load widget values from the current ydl options."""
        self.is_loading = True
        try:
            for key, widget in self.widgets.items():
                if isinstance(widget, ttk.Combobox):
                    value = self.ydl_options.get(key, "original")
                    values = widget.cget("values")
                    if value in values:
                        widget.set(value)
                    else:
                        widget.set("original")
                elif isinstance(widget, tk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, self.ydl_options.get(key, ""))
                elif isinstance(widget, tk.BooleanVar):
                    widget.set(self.ydl_options.get(key, False))
                elif isinstance(widget, dict) and "widget" in widget:
                    w = widget["widget"]
                    w.delete(0, tk.END)
                    w.insert(0, str(self.ydl_options.get(key, widget["default"])))

            categories = [
                "sponsor", "intro", "outro", "selfpromo", "interaction",
                "music_offtopic", "preview", "filler", "exclusive_access",
                "poi_highlight", "poi_nonhighlight"
            ]
            sponsorblock_mark = self.ydl_options.get("sponsorblock_mark", [])
            sponsorblock_remove = self.ydl_options.get("sponsorblock_remove", [])
            for category in categories:
                mark_var = self.widgets.get(f"sponsorblock_mark_{category}")
                if mark_var:
                    mark_var.set(category in sponsorblock_mark)
                remove_var = self.widgets.get(f"sponsorblock_remove_{category}")
                if remove_var:
                    remove_var.set(category in sponsorblock_remove)
        finally:
            self.is_loading = False

    def _update_preview(self, options: Optional[Dict] = None) -> None:
        """Update the preview text with the current ydl options."""
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", "Settings Preview:\n")
        self.preview_text.insert("2.0", json.dumps(self.ydl_options, indent=4))
        self.preview_text.config(state="disabled")

    def _save_preset(self) -> None:
        """Save the current settings as a preset file."""
        name = tk.simpledialog.askstring("Save Preset", "Enter preset name:", parent=self.window)
        if not name:
            return
        path = os.path.join(self.preset_directory, f"{name}.json")
        try:
            with open(path, "w") as f:
                json.dump(self.ydl_options, f, indent=4)
            self._refresh_preset_list()
            self.preset_var.set(name)
            messagebox.showinfo("Success", f"Preset '{name}' saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save preset: {e}")

    def _save_and_close(self) -> None:
        """Save the current settings and close the window."""
        self._update_ydl_options()
        self.window.destroy()
        self.initial_options = self.ydl_options

    def _cancel(self) -> None:
        """Cancel changes and close the window."""
        self.ydl_options = self.initial_options
        self.window.destroy()


def show_settings_window(parent: tk.Tk, initial_options: Optional[Dict] = None, is_global: bool = False) -> Dict:
    """Display the settings window and return the selected options."""
    settings_window = SettingsWindow(parent, initial_options, is_global)
    parent.wait_window(settings_window.window)
    return settings_window.ydl_options