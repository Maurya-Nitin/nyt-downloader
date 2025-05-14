import os
import json
import queue
import threading
import yt_dlp as youtube_dl
from typing import Dict, Any, Optional
from core.logger import Logger #type: ignore
from tkinter import filedialog
from core.queue import QueueManager #type: ignore

"""Downloader module for handling video/audio downloads using yt-dlp."""


class Downloader(Logger):
    def __init__(self, app: Any) -> None:
        self.app = app
        self.download_queue: queue.Queue = queue.Queue()
        self.max_threads: int = 4

    def start_downloads(self) -> None:
        """Start the download process using multiple threads."""
        if not self.app.download_directory:
            self.app.messagebox.showwarning("Warning", "Please select a download directory first.")
            return
        if not self.app.queue:
            self.app.messagebox.showwarning("Warning", "The download queue is empty.")
            return

        for task in self.app.queue:
            if task["status"] == "Queued":
                self.download_queue.put(task)

        for _ in range(self.max_threads):
            thread = threading.Thread(target=self.worker, daemon=True)
            thread.start()

    def worker(self) -> None:
        """Worker thread to download tasks from the queue."""
        while not self.download_queue.empty():
            task: Dict[str, Any] = self.download_queue.get()
            self.download_task(task)
            self.download_queue.task_done()

    def download_task(self, task: Dict[str, Any]) -> None:
        """Download a single video/audio item based on the task configuration."""
        task["status"] = "Downloading"
        task["progress"] = "0% | --:--"
        self.app.update_queue_listbox_threadsafe()
        self.log(f"🔄 Starting download: {task['query']}")

        search_query: str = task["query"]

        if not (search_query.startswith("http://") or search_query.startswith("https://")):
            search_query = f"ytsearch:{search_query}"

        ydl_opts: Dict[str, Any] = task['ydl_opts']

        try:
            custom_path: Optional[str] = ydl_opts.get('custom_file_path')
            if custom_path:
                ydl_opts['outtmpl'] = os.path.join(custom_path, '%(title)s.%(ext)s')
            else:
                raise KeyError("No custom path provided.")
        except KeyError:
            ydl_opts['outtmpl'] = os.path.join(self.app.download_directory, '%(title)s.%(ext)s')
        except Exception as e:
            self.log(f"Failed to set custom path. Using default. Error: {e}", level="error")
            ydl_opts['outtmpl'] = os.path.join(self.app.download_directory, '%(title)s.%(ext)s')

        ydl_opts.update({
            'progress_hooks': [lambda progress_data: self.progress_hook(progress_data, task)],
            'logger': self,
            'noplaylist': True
        })

        if ydl_opts.get('final_ext') == "original":
            ydl_opts.pop('final_ext')

        if ydl_opts.get('extract_comments', False):
            ydl_opts['extract_comments'] = True
            ydl_opts['writeinfojson'] = True

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([search_query])
            task["status"] = "Completed"
            task["progress"] = "100% | Done"
        except Exception as e:
            task["status"] = "Failed"
            task["progress"] = "❌ Error"
            self.log(f"❌ Error downloading {search_query}: {e}", level="error")

        self.app.update_queue_listbox_threadsafe()

    def progress_hook(self, progress_data: Dict[str, Any], task: Dict[str, Any]) -> None:
        """Update task progress and ETA during download."""
        status: str = progress_data.get('status', '')

        if status == 'downloading':
            percent = progress_data.get('_percent_str', '0%').strip()
            eta = progress_data.get('_eta_str', '--:--')
            task["progress"] = f"{percent} | {eta}"
        elif status == 'finished':
            if task["ydl_opts"].get('getcomments', False):
                self.extract_comments_postprocessor(progress_data)
            task["status"] = "Completed"
            task["progress"] = "100% | Done"

        self.app.update_queue_listbox_threadsafe()

    def extract_comments_postprocessor(self, progress_data: Dict[str, Any]) -> None:
        """Extract and format YouTube comments including replies."""

        def extract_comments() -> None:
            info_json_path: str = os.path.splitext(progress_data['filename'])[0] + ".info.json"
            if progress_data.get('filename') and os.path.exists(info_json_path):
                with open(info_json_path, 'r', encoding='utf-8') as file:
                    info: Dict[str, Any] = json.load(file)

                comments = info.get('comments', [])
                formatted_comments = []

                for idx, comment in enumerate(comments, 1):
                    text = comment.get('text', 'No text available')
                    author = comment.get('author', 'Unknown Author')
                    timestamp = comment.get('timestamp', 'Unknown Timestamp')
                    formatted_comments.append(f"{idx}. [{timestamp}] {author}: {text}")

                    for reply_idx, reply in enumerate(comment.get('replies', []), 1):
                        reply_text = reply.get('text', 'No text available')
                        reply_author = reply.get('author', 'Unknown Author')
                        reply_timestamp = reply.get('timestamp', 'Unknown Timestamp')
                        formatted_comments.append(
                            f"    ↳ {idx}.{reply_idx} [{reply_timestamp}] {reply_author}: {reply_text}"
                        )

                comments_file = os.path.splitext(progress_data['filename'])[0] + "_comments.txt"
                with open(comments_file, 'w', encoding='utf-8') as output:
                    output.write('\n'.join(formatted_comments))
                self.log(f"✅ Extracted {len(comments)} comments (including replies) to {comments_file}")
            else:
                self.log("⚠️ info.json not found. Skipping comment extraction.", level="warning")

        # Determine correct .info.json path, fallback to manual selection
        info_json_path = os.path.splitext(progress_data['filename'])[0] + ".info.json"
        if ".f" in progress_data['filename']:
            info_json_path = os.path.splitext(progress_data['filename'])[0] + "info.json"

        if os.path.exists(info_json_path):
            extract_comments()
        else:
            info_json_path = filedialog.askopenfilename(
                title=f"info.json for {progress_data.get('filename','latest')}",
                filetypes=[("JSON Files", "*.json")]
            )
            if info_json_path:
                extract_comments()
            else:
                self.log("❌ info.json file not found for comments Extraction.", level="error")