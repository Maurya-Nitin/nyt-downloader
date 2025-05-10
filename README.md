# NYT Downloader

A modern, user-friendly GUI application for downloading videos and audio from YouTube and other supported platforms using `yt-dlp`. This application provides a feature-rich interface to manage download queues, customize settings, and handle advanced options like SponsorBlock, subtitles, and metadata embedding.

## Features

- **Intuitive GUI**: Built with Tkinter, featuring a clean and responsive interface for managing downloads.
- **Queue Management**: Add, import, export, and clear download queues with support for playlists and spreadsheets (CSV/Excel).
- **Customizable Settings**: Fine-tune download options such as format, quality, file naming, subtitles, metadata, and SponsorBlock settings.
- **Concurrent Downloads**: Supports up to 4 simultaneous downloads for faster processing.
- **SponsorBlock Integration**: Mark or remove sponsor segments, intros, outros, and more.
- **System Tray Support**: Minimize the app to the system tray and run downloads in the background.
- **Logging**: Detailed, color-coded logs with export functionality for debugging and tracking.
- **Cross-Platform**: Compatible with Windows, Linux, and macOS (requires FFmpeg).

## Installation

### Prerequisites
- **Python 3.8+**: Ensure Python is installed on your system. [Download Python](https://www.python.org/downloads/).
- **FFmpeg**: Required for post-processing (e.g., merging audio/video, embedding subtitles). The app will prompt to install FFmpeg if not found.
- **Dependencies**: Install the required Python packages listed in `pyproject.toml`.

### Steps
1. **Clone the Repository**:
   ```
   git clone https://github.com/yourusername/nyt-downloader.git
   cd nyt-downloader
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   Install the required Python packages using `poetry` or `pip` based on the `pyproject.toml` file:
   ```
   # Using Poetry (recommended)
   poetry install

   # Alternatively, using pip
   pip install -r requirements.txt
   ```
   To generate `requirements.txt` from `pyproject.toml` if needed:
   ```
   poetry export -f requirements.txt --output requirements.txt --without-hashes
   ```

4. **Run the Application**:
   ```
   python app.py
   ```

5. **FFmpeg Check**: On first run, the app checks for FFmpeg. If not found, it prompts to install it automatically (requires internet).

## Usage

1. **Launch the App**:
   Run `python app.py` to start the application. The main window opens in a maximized state.

2. **Add Downloads**:
   - Enter a YouTube URL or search query in the **Input** section and click **Add to Queue** (or press Enter).
   - For playlists, provide the playlist URL.
   - Load a spreadsheet (CSV/Excel) with URLs/queries via the **Load Spreadsheet** section.

3. **Select Download Directory**:
   Click **Select Folder** to choose where files are saved.

4. **Customize Settings**:
   - Use the **Handy Settings** section for quick options like format, extension, and SponsorBlock.
   - Click **Full Settings** (or press F2) for advanced options, including file naming, subtitles, and metadata.

5. **Start Downloads**:
   Click **Start Downloads** to process queued items. Up to 4 concurrent downloads are supported.

6. **Manage Queue**:
   - View the queue in the **Download Queue** section.
   - Use buttons to refresh, export, import, or clear the queue.
   - Select items to modify settings or remove them.

7. **Minimize to Tray**:
   Click **Run in Background** to minimize to the system tray while downloads continue.

8. **View Logs**:
   Check the **Download Logs** section for color-coded logs. Export logs to a file if needed.

## Project Structure

- `app.py`: Entry point for the application.
- `core/`:
  - `downloader.py`: Handles downloading tasks using `yt-dlp`.
  - `logger.py`: Implements a logging system with colored output.
  - `queue.py`: Manages the download queue, including adding, clearing, and importing/exporting.
  - `settings.py`: Manages download settings and presets.
- `ui/`:
  - `main_window.py`: Defines the main GUI window and components.
  - `widgets.py`: Implements the settings window with a tabbed interface.
- `utils/`:
  - `helpers.py`: Utility functions, including FFmpeg installation checks.
- `assets/`: Contains icons and images for the GUI (e.g., `logo.ico`, `export.png`).

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bugfix:
   ```
   git checkout -b feature-name
   ```
3. Make changes and commit:
   ```
   git commit -m "Add feature-name"
   ```
4. Push to your fork and create a pull request:
   ```
   git push origin feature-name
   ```

Ensure your code follows the project's coding style and includes documentation.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading and processing media.
- Uses [Tkinter](https://docs.python.org/3/library/tkinter.html) for the GUI.
- Thanks to the open-source community for tools and libraries that made this project possible.
