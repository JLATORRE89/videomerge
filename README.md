# MP3-MKV Merger

A powerful Python application to merge MP3 audio files with MKV video files from OBS Studio, featuring both a modern web interface and command-line functionality. Includes social media optimization for platforms like Instagram, TikTok, and YouTube.

## Features

- Combines MP3 audio files with MKV video files
- Options to replace or add audio tracks
- Modern, responsive web UI interface
- Advanced command-line interface for batch processing
- Uses local ffmpeg installation with Python integration
- Real-time progress tracking and logging
- File monitoring for automatic processing of new files
- Intelligent file matching between MP3 and MKV files
- Audio normalization for consistent volume levels
- Customizable audio and video codec selection
- Social media optimization for different platforms

## Requirements

- Python 3.6+
- ffmpeg installed and available in system PATH
- Compatible with Windows, macOS, and Linux

### Python Dependencies
- ffmpeg-python: For Pythonic ffmpeg integration
- Flask: For the web interface
- tqdm: For progress bars in CLI mode
- watchdog: For file monitoring capabilities

## Installation

1. Clone or download this repository
2. Make sure ffmpeg is installed and in your system PATH
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python -m mp3_mkv_merger.main
   ```

## Usage

### Web Interface (Default)

1. Run the application without arguments to start the web UI:
   ```
   python -m mp3_mkv_merger.main
   ```
   This will open your default browser to the interface.

2. Enter the directories containing your MP3 files, MKV files, and where to save the output.

3. Select your preferences:
   - **Basic Options**:
     - Replace original audio: Completely replaces the audio in the MKV file with the MP3
     - Keep original audio track: When not replacing, keeps the original audio as a second track
   
   - **Advanced Options**:
     - Normalize audio: Adjusts audio levels for consistent volume
     - Audio codec: Select the audio codec to use (AAC, MP3, or copy)
     - Video codec: Select the video codec to use (copy, H.264, H.265/HEVC)
     - Social media optimization: Resize video for social media platforms

4. Additional Features:
   - Use "Find Matches" to see which MP3 and MKV files will be paired together
   - View real-time progress during processing
   - Monitor progress with a visual progress bar

5. Click "Start Processing" to begin the merge operation.

### Command Line Interface

For batch processing, use the CLI mode:

```
python -m mp3_mkv_merger.main --cli --mp3 /path/to/mp3 --mkv /path/to/mkv --out /path/to/output
```

Available options:
```
--web               Run in web UI mode (default)
--cli               Run in command-line mode
--mp3 DIR           Directory containing MP3 files
--mkv DIR           Directory containing MKV files
--out DIR           Directory for output files
--replace           Replace original audio instead of adding as new track
--no-keep           Don't keep original audio track (when not replacing)
--normalize         Normalize audio levels
--audio-codec CODEC Audio codec to use (default: aac)
--video-codec CODEC Video codec to use (default: copy)
--social            Optimize for social media
--social-width W    Width for social media output (default: 1080)
--social-height H   Height for social media output (default: 1080)
--social-format FMT Format for social media output (mp4, mov, webm) (default: mp4)
--output-format FMT Output file format (mp4, webm, mov) (default: mp4)
--watch             Watch directories for new files
--port PORT         Port for web server (default: 8000)
--debug             Enable debug logging
--log-file FILE     Log file path (default: auto-generated)
```

Examples:

Basic audio replacement:
```
python -m mp3_mkv_merger.main --cli --mp3 /audio --mkv /video --out /output --replace
```

Using advanced options:
```
python -m mp3_mkv_merger.main --cli --mp3 /audio --mkv /video --out /output --normalize --audio-codec mp3 --watch
```

Social media optimization:
```
python -m mp3_mkv_merger.main --cli --mp3 /audio --mkv /video --out /output --social --social-width 1080 --social-height 1920 --social-format mp4
```

Using WebM output format:
```
python -m mp3_mkv_merger.main --cli --mp3 /audio --mkv /video --out /output --output-format webm
```

## How It Works

- Files are matched intelligently between the MP3 and MKV directories:
  1. First by identical filenames (without extensions)
  2. Then by creation time if name matching fails
  3. Finally by alphabetical order as a fallback
- The application uses ffmpeg via the ffmpeg-python library to merge the audio and video streams
- Advanced options allow for audio normalization and codec selection
- Output files are saved as MP4, WebM, or MOV files depending on your selection
- File monitoring can watch for new files and process them automatically
- The Flask-based web interface provides real-time feedback and advanced options

## Project Structure

The MP3-MKV Merger is organized into the following modules:

- `main.py`: Main entry point that parses arguments and starts the application
- `core.py`: Contains the `MediaMerger` class that handles the core functionality
- `cli.py`: Handles command-line interface operations
- `web_ui.py`: Provides a Flask-based web interface
- `utils.py`: Utility functions for logging and other common tasks
- `static/`: Directory containing web UI files (HTML, CSS, JavaScript)

## Troubleshooting

- Make sure ffmpeg is installed and available in your system PATH
  - The application will check for ffmpeg on startup and notify you if it's not found
- Check that you have read/write permissions for all directories
- Ensure MP3 and MKV files are properly formatted
- If using OBS Studio, make sure your recordings are completed and not corrupted
- Check the log files in the `logs` directory for detailed error information
- For codec issues, try using the "copy" option to avoid re-encoding
- If file matching isn't working as expected, use the "Find Matches" feature to see which files will be paired

## Development

To contribute to the MP3-MKV Merger:

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Run the tests to ensure everything works
5. Submit a pull request

## License

This project is released under the MIT License.