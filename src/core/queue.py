import asyncio
import aiofiles
import os
import pandas as pd
from tkinter import filedialog, messagebox
import yt_dlp as youtube_dl
import tkinter as tk
from core.logger import Logger#type: ignore
import threading
import json

from typing import Any, Dict, List, Optional


class QueueManager(Logger):
    def __init__(self, app: Any) -> None:
        self.app = app
        self.queue: List[Dict[str, Any]] = []

    def add_to_queue(self, event: Optional[Any] = None) -> None:
        """Adds a video or playlist to the queue."""
        query: str = self.app.query_entry.get().strip()
        if not query and self.app.master.focus_get() == self.app.query_entry:
            messagebox.showwarning("Warning", "Please enter a YouTube link or search query.")
            return

        if "playlist?" in query or "list=" in query:
            def fetch_playlist() -> None:
                self.log(f"Fetching videos from playlist: {query}")

                ydl_opts = {
                    'quiet': True,
                    'extract_flat': True,
                    'force_generic_extractor': True,
                }

                try:
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        playlist_info = ydl.extract_info(query, download=False)

                    if 'entries' in playlist_info:
                        for video in playlist_info['entries']:
                            if 'url' in video and 'title' in video:
                                task = {
                                    "query": video['url'],
                                    "status": "Queued",
                                    "ydl_opts": self.app.global_ydl_opts.copy(),
                                }
                                self.queue.append(task)
                                self.log(f"Added video to queue: {video['title']}")
                        self.log(f"Added {len(playlist_info['entries'])} videos to the queue.")
                    else:
                        self.log("⚠️ No videos found in playlist!", level="warning")
                    self.app.update_queue_listbox_threadsafe()
                except Exception as e:
                    self.log(f"❌ Error fetching playlist: {e}", level="error")
                    self.app.update_queue_listbox_threadsafe()

            threading.Thread(target=fetch_playlist, daemon=True).start()
        else:
            task = {
                "query": query,
                "status": "Queued",
                "ydl_opts": self.app.global_ydl_opts.copy()
            }
            self.queue.append(task)

        self.app.update_queue_listbox_threadsafe()
        self.app.query_entry.delete(0, tk.END)
        self.log(f"✅ Added to queue: {query}")
        self.app.query_entry.focus_set()

    def clear_queue(self) -> None:
        """Clears selected items or entire queue, with download-aware logic."""
        selected_items = self.app.queue_table.selection()

        if selected_items:
            indices: List[int] = []
            for item in selected_items:
                try:
                    if self.app.queue_table.item(item, "values")[1] == "Downloading":
                        query = self.app.queue_table.item(item, "values")[2]
                        self.log(f"⚠️ Cannot remove downloading item: {query}", level="warning")
                        continue
                    else:
                        index = int(self.app.queue_table.item(item, "values")[0]) - 1
                        indices.append(index)
                except Exception as e:
                    self.log(f"Error retrieving index for item {item}: {e}", level="error")
            indices = sorted(set(indices), reverse=True)
            for index in indices:
                del self.queue[index]
            self.app.update_queue_listbox_threadsafe()
            self.log(f"✅ Removed {len(indices)} selected items from queue.")
        else:
            confirmation = messagebox.askyesno("Warning", "Do you want to clear the entire queue?")
            if confirmation:
                active_downloads = any(task["status"] == "Downloading" for task in self.queue)
                if active_downloads:
                    ask = messagebox.askyesnocancel(
                        "Warning",
                        "Some downloads are still running and you cannot cancel them!\n\n"
                        "Press 'Yes' to keep the downloads running in background and clear them from the queue\n"
                        "Press 'No' to clear the other queue except leaving the downloads running\n"
                        "Press 'Cancel' to keep the queue as it is"
                    )
                    if ask:
                        self.queue.clear()
                        self.app.update_queue_listbox_threadsafe()
                        self.log("✅ Cleared the entire queue while downloading items running in background.")
                    elif ask is False:
                        self.queue[:] = [task for task in self.queue if task["status"] == "Downloading"]
                        self.app.update_queue_listbox_threadsafe()
                        self.log("✅ Cleared the entire queue except the Downloading items.")
                else:
                    self.queue.clear()
                    self.app.update_queue_listbox_threadsafe()
                    self.log("✅ Cleared the entire queue.")

    def import_queue(self) -> None:
        """Imports a queue from a JSON file."""
        file_path = filedialog.askopenfilename(title="Select Queue File", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "r") as f:
                self.queue = json.load(f)
                self.app.update_queue_listbox_threadsafe()
            self.log(f"✅ Loaded queue from {file_path}")
        except Exception as e:
            self.log(f"❌ Error loading queue: {e}", level="error")

    def export_queue(self) -> None:
        """Exports queued items to a JSON file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "w") as f:
                self.queue = [task for task in self.queue if task["status"] == "Queued"]
                json.dump(self.queue, f, indent=4)
            self.log(f"✅ Exported queue to {file_path}")
        except Exception as e:
            self.log(f"❌ Error exporting queue: {e}", level="error")

    async def load_spreadsheet_async(self) -> None:
        """Asynchronously loads a spreadsheet (CSV or Excel) into the queue."""
        file_path = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: filedialog.askopenfilename(filetypes=[("Spreadsheet Files", "*.csv *.xlsx *.xls")])
        )
        if not file_path:
            return

        try:
            ext: str = os.path.splitext(file_path)[-1].lower()
            valid_count: int = 0

            if ext == ".csv":
                async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                    raw_content: str = await f.read()
                queries = [q.strip() for q in raw_content.split(",") if q.strip()]

                for query in queries:
                    task = {
                        "query": query,
                        "status": "Queued",
                        "ydl_opts": self.app.global_ydl_opts.copy()
                    }
                    self.queue.append(task)
                    await asyncio.get_event_loop().run_in_executor(None, self.app.update_queue_listbox_threadsafe)
                    valid_count += 1

            elif ext in (".xlsx", ".xls"):
                df = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: pd.read_excel(file_path)
                )
                df.columns = [col.strip().lower() for col in df.columns]

                for _, row in df.iterrows():
                    query = row.get('query') or row.get('url')
                    if isinstance(query, (int, float)):
                        query = str(query)
                    elif not isinstance(query, str) or not query.strip():
                        continue

                    query = query.strip()
                    preset = str(row.get('preset')).strip() if row.get('preset') else ""

                    if preset and preset.lower() != "default":
                        preset_path = os.path.join(self.app.preset_dir, f"{preset}.json")
                        if os.path.exists(preset_path):
                            async with aiofiles.open(preset_path, mode='r') as f:
                                ydl_opts = json.loads(await f.read())
                        else:
                            preset = "New/Unsaved"
                            ydl_opts = self.app.global_ydl_opts.copy()
                    else:
                        ydl_opts = self.app.global_ydl_opts.copy()

                    task = {
                        "query": query,
                        "status": "Queued",
                        "ydl_opts": ydl_opts
                    }
                    self.queue.append(task)
                    self.log(f"Added {query} with preset {preset} to queue.")
                    await asyncio.get_event_loop().run_in_executor(None, self.app.update_queue_listbox_threadsafe)
                    valid_count += 1

            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: messagebox.showerror("Unsupported Format", "Please select a CSV or Excel file.")
                )
                return

            if valid_count == 0:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: messagebox.showerror("No Valid Entries", "No valid queries or URLs found.")
                )
            else:
                self.log(f"✅ Loaded {valid_count} entries from {os.path.basename(file_path)}.")

        except Exception as e:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: messagebox.showerror("Error", f"Failed to process file:\n{e}")
            )

    def load_spreadsheet_threaded(self) -> None:
        """Runs the async load_spreadsheet_async method in a thread."""
        def run_async() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.load_spreadsheet_async())
            finally:
                loop.close()

        threading.Thread(target=run_async, daemon=True).start()
