import os
import json
from tkinter import messagebox
from core.logger import Logger
from ui.widgets import show_settings_window
from typing import Optional, Dict, Any


class SettingsManager(Logger):
    def __init__(self, app: Any) -> None:
        self.app = app
        self.preset_dir: str = "settings_presets"
        try:
            with open(f"{self.preset_dir}/default.json", "r") as f:
                self.global_ydl_opts: Dict[str, Any] = json.load(f)
        except FileNotFoundError:
            self.global_ydl_opts = {}

        self.is_loading: bool = False
        self.categories: list[str] = [
            "sponsor", "intro", "outro", "selfpromo", "interaction",
            "music_offtopic", "preview", "filler", "exclusive_access",
            "poi_highlight", "poi_nonhighlight"
        ]

    def save_handy_settings_into_global(self) -> None:
        """Save settings from the UI into global_ydl_opts."""
        if self.is_loading:
            return

        postprocessors: list[Dict[str, Any]] = self.global_ydl_opts.get('postprocessors', [])
        selected_label: str = self.app.format_var.get()
        value: str = self.app.format_options.get(selected_label, "Custom")
        selected_ext: str = self.app.final_ext_var.get()
        embed_thumbnail: bool = self.app.embed_thumbnail_var.get()
        add_metadata: bool = self.app.metadata_var.get()
        sponsorblock: str = self.app.sponsorblock_var.get()
        embed_subtitles: bool = self.app.embed_subtitles_var.get()
        write_auto_subs: bool = self.app.writeautomaticsub_var.get()

        self.global_ydl_opts['format_dropdown'] = selected_label
        self.global_ydl_opts['format'] = value

        self.global_ydl_opts['final_ext'] = None if selected_ext == "original" else selected_ext

        self.global_ydl_opts['embedthumbnail'] = embed_thumbnail
        self.global_ydl_opts['writethumbnail'] = embed_thumbnail

        self.global_ydl_opts['addmetadata'] = add_metadata

        self.global_ydl_opts['writesubtitles'] = embed_subtitles
        self.global_ydl_opts['embedsubtitles'] = embed_subtitles

        self.global_ydl_opts['writeautomaticsub'] = write_auto_subs
        if write_auto_subs:
            self.global_ydl_opts['embedsubtitles'] = True

        def update_postprocessor(processors: list[Dict[str, Any]], new_pp: Dict[str, Any]) -> None:
            for i, pp in enumerate(processors):
                if pp.get("key") == new_pp.get("key"):
                    processors[i] = new_pp
                    return
            processors.append(new_pp)

        # Postprocessors
        if add_metadata:
            update_postprocessor(postprocessors, {"key": "FFmpegMetadata", "add_metadata": True, "add_chapters": True})
        else:
            postprocessors = [pp for pp in postprocessors if pp.get("key") != "FFmpegMetadata"]

        if selected_ext:
            if selected_ext in self.app.audio_exts:
                quality = "0" if "best" in value else "9" if "smallest" in value else "5"
                update_postprocessor(postprocessors, {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": selected_ext,
                    "preferredquality": quality
                })
                postprocessors = [pp for pp in postprocessors if pp.get("key") != "FFmpegVideoConvertor"]
            elif selected_ext in self.app.video_exts:
                update_postprocessor(postprocessors, {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": selected_ext
                })
            else:
                postprocessors = [pp for pp in postprocessors if pp.get("key") not in [
                    "FFmpegExtractAudio", "FFmpegVideoConvertor"]]

        if embed_thumbnail:
            update_postprocessor(postprocessors, {"key": "EmbedThumbnail"})
        else:
            postprocessors = [pp for pp in postprocessors if pp.get("key") != "EmbedThumbnail"]

        if embed_subtitles:
            update_postprocessor(postprocessors, {'key': 'FFmpegEmbedSubtitle'})
        else:
            postprocessors = [pp for pp in postprocessors if pp.get("key") != "FFmpegEmbedSubtitle"]

        # SponsorBlock logic
        if sponsorblock == "mark":
            self.global_ydl_opts.update({
                'sponsorblock_mark': self.categories,
                'sponsorblock_remove': [],
                'add_chapters': True
            })
            update_postprocessor(postprocessors, {
                "key": "SponsorBlock",
                "categories": self.categories,
                "when": 'after_filter',
            })
            update_postprocessor(postprocessors, {
                "key": "ModifyChapters",
                "sponsorblock_chapter_title": self.global_ydl_opts.get('sponsorblock_chapter_title', '[SponsorBlock]: %(category_names)l')
            })
            update_postprocessor(postprocessors, {
                "key": "FFmpegMetadata",
                "add_metadata": add_metadata,
                "add_chapters": True,
            })

        elif sponsorblock == "remove":
            self.global_ydl_opts.update({
                'sponsorblock_remove': self.categories,
                'add_chapters': True,
                'sponsorblock_mark': []
            })
            update_postprocessor(postprocessors, {
                "key": "SponsorBlock",
                "categories": self.categories,
                "when": 'after_filter',
            })
            update_postprocessor(postprocessors, {
                "key": "ModifyChapters",
                'remove_chapters_patterns': [],
                'remove_ranges': [],
                "sponsorblock_chapter_title": '[SponsorBlock]: %(category_names)l',
                'remove_sponsor_segments': self.categories
            })
            update_postprocessor(postprocessors, {
                "key": "FFmpegMetadata",
                "add_metadata": add_metadata,
                "add_chapters": True,
            })

        elif sponsorblock == "Other":
            if self.global_ydl_opts.get('sponsorblock_mark') == self.categories:
                self.global_ydl_opts['sponsorblock_mark'] = []
            if self.global_ydl_opts.get('sponsorblock_remove') == self.categories:
                self.global_ydl_opts['sponsorblock_remove'] = []
            # Temizle
            for key in ("SponsorBlock", "ModifyChapters"):
                postprocessors = [pp for pp in postprocessors if pp.get("key") != key]

        if postprocessors:
            self.global_ydl_opts['postprocessors'] = postprocessors

        self.mark_as_unsaved_if_modified()

    def load_handy_settings(self) -> None:
        """Load settings from global_ydl_opts into the UI fields."""
        if self.is_loading:
            return
        try:
            self.is_loading = True
            self.app.format_var.set(self.global_ydl_opts.get('format_dropdown', "Best (Video+Audio)"))
            self.app.final_ext_var.set(self.global_ydl_opts.get('final_ext', "original"))
            self.app.embed_thumbnail_var.set(self.global_ydl_opts.get('embedthumbnail', False))
            self.app.metadata_var.set(self.global_ydl_opts.get('addmetadata', False))
            self.app.embed_subtitles_var.set(self.global_ydl_opts.get('embedsubtitles', False))
            self.app.writeautomaticsub_var.set(self.global_ydl_opts.get('writeautomaticsub', False))

            sb_mark = self.global_ydl_opts.get('sponsorblock_mark')
            sb_remove = self.global_ydl_opts.get('sponsorblock_remove')
            if sb_mark == self.categories:
                self.app.sponsorblock_var.set("mark")
            elif sb_remove == self.categories:
                self.app.sponsorblock_var.set("remove")
            else:
                self.app.sponsorblock_var.set("Other")
        except Exception as e:
            self.log(f"Error loading settings: {e}", level="error")
        finally:
            self.is_loading = False

    def mark_as_unsaved_if_modified(self) -> None:
        """Mark the current settings as 'New/Unsaved' if changed from the preset."""
        current_name: str = self.app.preset_var.get()
        if current_name in ["New/Unsaved", ""]:
            return
        try:
            with open(os.path.join(self.preset_dir, f"{current_name}.json")) as f:
                saved_opts = json.load(f)
            if saved_opts != self.global_ydl_opts:
                self.app.preset_var.set("New/Unsaved")
        except Exception:
            self.app.preset_var.set("New/Unsaved")

    def on_preset_selected(self, event: Optional[Any] = None) -> None:
        """Load selected preset and apply its settings."""
        name = self.app.preset_var.get()
        if name == "New/Unsaved":
            return
        path = os.path.join(self.preset_dir, f"{name}.json")
        try:
            with open(path, "r") as f:
                self.is_loading = True
                self.ydl_opts = json.load(f)
                self.global_ydl_opts = self.ydl_opts.copy()
                self.load_handy_settings()
            self.log(f"✅ Loaded preset: {name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preset: {e}")
        finally:
            self.is_loading = False

    def open_settings_window(self, initial_options: Optional[Dict[str, Any]] = None, global_change: bool = True) -> Optional[Dict[str, Any]]:
        """Open settings GUI and update internal config."""
        if initial_options is None:
            initial_options = self.global_ydl_opts
        settings = show_settings_window(self.app.master, initial_options=initial_options, is_global=global_change)
        if settings != initial_options and global_change:
            self.global_ydl_opts = settings
            self.load_handy_settings()
            self.log("🔧 Settings Updated and saved to default template.")
        elif global_change and settings == initial_options:
            self.log("⚠️ No settings were changed.")
        else:
            return settings

    def open_settings_window_for_selected(self, event: Optional[Any] = None) -> None:
        """Open settings window for selected queue items or globally."""
        selected_items = self.app.queue_table.selection()
        if selected_items:
            if len(selected_items) > 1:
                new_ydl_opts = self.open_settings_window(initial_opts=self.global_ydl_opts, global_change=False)
                for item in selected_items:
                    index = int(self.app.queue_table.item(item, "values")[0]) - 1
                    task = self.app.queue[index]
                    if task["status"] == "Downloading":
                        self.log(f"⚠️ Cannot modify settings for downloading item: {task['query']}", level="warning")
                        continue
                    elif task["status"] in ["Completed", "Failed", "Queued"]:
                        try:
                            task["ydl_opts"] = new_ydl_opts
                            self.log(f"🔧 Settings Updated for {task['query']}", level="success")
                        except Exception as e:
                            self.log(f"⚠️ Error updating settings: {e}", level="error")
            else:
                item = selected_items[0]
                index = int(self.app.queue_table.item(item, "values")[0]) - 1
                task = self.app.queue[index]
                if task["status"] == "Downloading":
                    self.log(f"⚠️ Cannot modify settings for downloading item: {task['query']}", level="warning")
                    return
                if task["status"] in ["Queued", "Completed", "Failed"]:
                    new_ydl_opts = self.open_settings_window(initial_opts=task['ydl_opts'], global_change=False)
                    if new_ydl_opts != task['ydl_opts']:
                        try:
                            task["ydl_opts"] = new_ydl_opts
                            self.log(f"🔧 Settings Updated for {task['query']}", level="success")
                        except Exception as e:
                            self.log(f"⚠️ Error updating settings: {e}", level="error")
                    else:
                        self.log("⚠️ No settings were changed.")
        else:
            self.open_settings_window(initial_opts=self.global_ydl_opts, global_change=True)