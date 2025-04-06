"""
Core functionality for MP3-MKV Merger.

This module contains the MediaMerger class which handles the merging of
MP3 audio files with MKV video files using ffmpeg.
"""

import os
import logging
import subprocess
from pathlib import Path
from tqdm import tqdm

# Try to import ffmpeg-python
try:
    import ffmpeg
except ImportError:
    raise ImportError("ffmpeg-python not installed. Install with: pip install ffmpeg-python")

# Create logger
logger = logging.getLogger('mp3_mkv_merger.core')

class MediaMerger:
    """Handles the merging of MP3 audio and MKV video files using ffmpeg-python."""
    
    def __init__(self, mp3_dir, mkv_dir, out_dir, 
                 replace_audio=False, keep_original=True,
                 audio_codec="aac", video_codec=None,
                 normalize_audio=False, social_media=False,
                 social_width=1080, social_height=1080,
                 social_format="mp4", output_format="mp4"):
        """
        Initialize the MediaMerger.
        
        Args:
            mp3_dir (str): Directory containing MP3 files
            mkv_dir (str): Directory containing MKV files
            out_dir (str): Directory for output files
            replace_audio (bool): Replace existing audio in MKV files
            keep_original (bool): Keep original audio track when adding MP3
            audio_codec (str): Audio codec to use (default: "aac")
            video_codec (str): Video codec to use (default: copy)
            normalize_audio (bool): Normalize audio levels
            social_media (bool): Optimize output for social media
            social_width (int): Width for social media output
            social_height (int): Height for social media output
            social_format (str): Format for social media output ("mp4", "mov")
        """
        self.mp3_dir = mp3_dir
        self.mkv_dir = mkv_dir
        self.out_dir = out_dir
        self.replace_audio = replace_audio
        self.keep_original = keep_original
        self.audio_codec = audio_codec
        self.video_codec = video_codec
        self.normalize_audio = normalize_audio
        self.social_media = social_media
        self.social_width = social_width
        self.social_height = social_height
        self.social_format = social_format
        self.output_format = output_format
        self.progress_callback = None
        self.stop_requested = False
        self.current_process = None
        
        # File monitoring
        self.file_observer = None
        self.file_event_handler = None
        self.watching = False
        
        logger.info(f"MediaMerger initialized with settings: mp3_dir={mp3_dir}, mkv_dir={mkv_dir}, "
                   f"out_dir={out_dir}, social_media={social_media}, output_format={output_format}")
    
    def set_progress_callback(self, callback):
        """Set a callback function for progress updates."""
        self.progress_callback = callback
    
    def _update_progress(self, message, percent):
        """Update progress using the callback if set."""
        if self.progress_callback:
            self.progress_callback(message, percent)
        logger.debug(f"Progress: {percent}% - {message}")
    
    def check_ffmpeg(self):
        """Check if ffmpeg is available and can be used."""
        try:
            # Use ffmpeg-python to probe version
            probe = ffmpeg.probe("__version__", cmd="ffmpeg", stderr=subprocess.PIPE)
            return True
        except Exception:
            try:
                # Fallback to direct command
                result = subprocess.run(
                    ["ffmpeg", "-version"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"ffmpeg found: {result.stdout.split()[2]}")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("Error: ffmpeg not found in PATH")
                self._update_progress("Error: ffmpeg not found in PATH", -1)
                return False
    
    def get_duration(self, file_path):
        """Get the duration of a media file in seconds."""
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            logger.error(f"Error getting duration for {file_path}: {str(e)}")
            return None
    
    def merge_files(self, mp3_file, mkv_file, output_file):
        """
        Merge an MP3 file with an MKV file using ffmpeg-python.
        
        Args:
            mp3_file (str): Path to MP3 file
            mkv_file (str): Path to MKV file
            output_file (str): Path to output file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.stop_requested:
            return False
        
        try:
            # Get video info
            video_duration = self.get_duration(mkv_file)
            if video_duration:
                self._update_progress(f"Video duration: {video_duration:.2f}s", 5)
            
            # Create ffmpeg inputs
            video_input = ffmpeg.input(mkv_file)
            audio_input = ffmpeg.input(mp3_file)
            
            # Get streams
            video_stream = video_input.video
            
            # Apply video codec if specified
            if self.video_codec:
                video_stream = video_stream.codec(self.video_codec)
            else:
                video_stream = video_stream.codec('copy')
            
            # Setup audio streams based on options
            if self.normalize_audio:
                audio_stream = audio_input.audio.filter('loudnorm')
            else:
                audio_stream = audio_input.audio
                
            audio_stream = audio_stream.codec(self.audio_codec)
            
            # Social media optimization
            if self.social_media:
                video_stream = video_stream.filter(
                    'scale', 
                    width=self.social_width, 
                    height=self.social_height
                )
                # Set output format
                output_format = self.social_format
            else:
                # Default to mp4 for better compatibility
                # Extract format from output filename if specified
                if output_file.lower().endswith('.webm'):
                    output_format = 'webm'
                else:
                    output_format = 'mp4'
            
            # Setup output based on options
            if self.replace_audio:
                # Replace original audio with the MP3
                output_options = ffmpeg.output(
                    video_stream,
                    audio_stream,
                    output_file,
                    f=output_format,
                    y=None  # Overwrite output file if it exists
                )
            else:
                if self.keep_original:
                    # Keep original audio and add MP3
                    original_audio = video_input.audio.codec('copy')
                    output_options = ffmpeg.output(
                        video_stream,
                        audio_stream,
                        original_audio,
                        output_file,
                        f=output_format,
                        y=None
                    )
                else:
                    # Just add MP3 audio
                    output_options = ffmpeg.output(
                        video_stream,
                        audio_stream,
                        output_file,
                        f=output_format,
                        y=None
                    )
            
            # Run the ffmpeg command with progress monitoring
            self._update_progress(f"Starting: {os.path.basename(output_file)}", 5)
            
            # Get the command for execution
            cmd = ffmpeg.compile(output_options, overwrite_output=True)
            
            # Run with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            self.current_process = process
            
            for line in process.stdout:
                if self.stop_requested:
                    process.terminate()
                    return False
                
                # Parse progress information
                if "Duration" in line:
                    self._update_progress(f"Processing: {os.path.basename(output_file)}", 10)
                elif "time=" in line:
                    try:
                        time_str = line.split("time=")[1].split()[0]
                        h, m, s = time_str.split(":")
                        seconds = float(h) * 3600 + float(m) * 60 + float(s)
                        
                        # Calculate progress if we know the duration
                        if video_duration:
                            progress = min(95, int((seconds / video_duration) * 90) + 10)
                        else:
                            progress = min(90, 10 + int(seconds / 2))
                            
                        self._update_progress(
                            f"Processing: {os.path.basename(output_file)} ({time_str})", 
                            progress
                        )
                    except Exception:
                        pass
            
            returncode = process.wait()
            self.current_process = None
            
            if returncode == 0:
                self._update_progress(f"Completed: {os.path.basename(output_file)}", 100)
                return True
            else:
                self._update_progress(f"Error processing: {os.path.basename(output_file)}", -1)
                return False
                
        except Exception as e:
            logger.error(f"Error merging files: {str(e)}")
            self._update_progress(f"Error: {str(e)}", -1)
            return False
    
    def process_all(self):
        """
        Process all MP3 and MKV files in the specified directories.
        
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        if not self.check_ffmpeg():
            return False
            
        # Create output directory if it doesn't exist
        os.makedirs(self.out_dir, exist_ok=True)
        
        # Get list of MP3 and MKV files
        try:
            mp3_files = [f for f in os.listdir(self.mp3_dir) 
                        if f.lower().endswith('.mp3')]
            mkv_files = [f for f in os.listdir(self.mkv_dir) 
                        if f.lower().endswith('.mkv')]
        except FileNotFoundError as e:
            logger.error(f"Directory not found: {str(e)}")
            self._update_progress(f"Error: {str(e)}", -1)
            return False
        except PermissionError as e:
            logger.error(f"Permission error accessing directory: {str(e)}")
            self._update_progress(f"Error: {str(e)}", -1)
            return False
        
        if not mp3_files:
            self._update_progress(f"No MP3 files found in {self.mp3_dir}", -1)
            return False
        if not mkv_files:
            self._update_progress(f"No MKV files found in {self.mkv_dir}", -1)
            return False
        
        # Sort files by name
        mp3_files.sort()
        mkv_files.sort()
        
        self._update_progress(f"Found {len(mp3_files)} MP3 files and {len(mkv_files)} MKV files", 0)
        
        # Process files
        success = True
        total_files = min(len(mp3_files), len(mkv_files))
        
        # Use tqdm for CLI progress tracking
        for i in tqdm(range(total_files), desc="Processing files", disable=self.progress_callback is not None):
            if self.stop_requested:
                self._update_progress("Operation cancelled", -1)
                return False
                
            mp3_file = os.path.join(self.mp3_dir, mp3_files[i])
            mkv_file = os.path.join(self.mkv_dir, mkv_files[i])
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(mkv_files[i]))[0]
            
            # Set output file extension based on settings
            if self.social_media:
                extension = self.social_format
            elif hasattr(self, 'output_format') and self.output_format == 'webm':
                extension = 'webm'
            else:
                extension = "mp4"
            output_file = os.path.join(self.out_dir, f"{base_name}_merged.{extension}")
            
            self._update_progress(f"Processing {i+1}/{total_files}: {base_name}", 
                                 int((i / total_files) * 100))
            
            # Merge files
            if not self.merge_files(mp3_file, mkv_file, output_file):
                success = False
        
        if success:
            self._update_progress(f"All files processed successfully", 100)
        else:
            self._update_progress(f"Some files failed to process", -1)
            
        return success
    
    def stop(self):
        """Stop the merging process."""
        self.stop_requested = True
        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception as e:
                logger.error(f"Error terminating process: {str(e)}")
        
        if self.watching and self.file_observer:
            try:
                self.file_observer.stop()
                self.watching = False
            except Exception as e:
                logger.error(f"Error stopping file observer: {str(e)}")
    
    def start_file_monitoring(self, callback=None):
        """
        Start monitoring directories for new files.
        
        Args:
            callback: Function to call when new files are detected
            
        Returns:
            bool: True if monitoring started successfully
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.error("watchdog module not installed. Install with: pip install watchdog")
            if callback:
                callback("Error: watchdog module not installed")
            return False
            
        if self.watching:
            return False
            
        class FileHandler(FileSystemEventHandler):
            def __init__(self, merger, callback):
                self.merger = merger
                self.callback = callback
                self.mp3_dir = merger.mp3_dir
                self.mkv_dir = merger.mkv_dir
                
            def on_created(self, event):
                if event.is_directory:
                    return
                    
                path = event.src_path
                if path.lower().endswith('.mp3') and os.path.dirname(path) == self.mp3_dir:
                    if self.callback:
                        self.callback(f"New MP3 detected: {os.path.basename(path)}")
                elif path.lower().endswith('.mkv') and os.path.dirname(path) == self.mkv_dir:
                    if self.callback:
                        self.callback(f"New MKV detected: {os.path.basename(path)}")
        
        try:
            # Set up the event handler and observer
            self.file_event_handler = FileHandler(self, callback)
            self.file_observer = Observer()
            
            # Watch both directories
            self.file_observer.schedule(
                self.file_event_handler, 
                self.mp3_dir, 
                recursive=False
            )
            self.file_observer.schedule(
                self.file_event_handler, 
                self.mkv_dir, 
                recursive=False
            )
            
            # Start the observer
            self.file_observer.start()
            self.watching = True
            
            if callback:
                callback("File monitoring started")
                
            return True
            
        except Exception as e:
            logger.error(f"Error starting file monitoring: {str(e)}")
            if callback:
                callback(f"Error starting file monitoring: {str(e)}")
            return False
    
    def find_matching_files(self):
        """
        Find matching MP3 and MKV files based on common patterns.
        
        Returns:
            list: List of tuples with (mp3_file, mkv_file, output_file)
        """
        try:
            # Get list of files
            mp3_files = [f for f in os.listdir(self.mp3_dir) 
                        if f.lower().endswith('.mp3')]
            mkv_files = [f for f in os.listdir(self.mkv_dir) 
                        if f.lower().endswith('.mkv')]
        except FileNotFoundError as e:
            logger.error(f"Directory not found: {str(e)}")
            return []
        except PermissionError as e:
            logger.error(f"Permission error accessing directory: {str(e)}")
            return []
                    
        # Try to find matches
        matches = []
        
        # First try to match by name without extension
        mp3_names = {os.path.splitext(f)[0]: f for f in mp3_files}
        mkv_names = {os.path.splitext(f)[0]: f for f in mkv_files}
        
        # Find common names
        common_names = set(mp3_names.keys()).intersection(set(mkv_names.keys()))
        
        for name in common_names:
            mp3_file = os.path.join(self.mp3_dir, mp3_names[name])
            mkv_file = os.path.join(self.mkv_dir, mkv_names[name])
            extension = self.social_format if self.social_media else "mp4"
            output_file = os.path.join(self.out_dir, f"{name}_merged.{extension}")
            matches.append((mp3_file, mkv_file, output_file))
        
        # If no matches by name, try matching by creation time
        if not matches and mp3_files and mkv_files:
            try:
                # Sort by creation time
                mp3_sorted = sorted(mp3_files, 
                                  key=lambda f: os.path.getctime(os.path.join(self.mp3_dir, f)))
                mkv_sorted = sorted(mkv_files, 
                                  key=lambda f: os.path.getctime(os.path.join(self.mkv_dir, f)))
                
                # Match files by order
                for i in range(min(len(mp3_sorted), len(mkv_sorted))):
                    mp3_file = os.path.join(self.mp3_dir, mp3_sorted[i])
                    mkv_file = os.path.join(self.mkv_dir, mkv_sorted[i])
                    base_name = os.path.splitext(os.path.basename(mkv_sorted[i]))[0]
                    extension = self.social_format if self.social_media else "mp4"
                    output_file = os.path.join(self.out_dir, f"{base_name}_merged.{extension}")
                    matches.append((mp3_file, mkv_file, output_file))
            except Exception as e:
                logger.error(f"Error matching files by creation time: {str(e)}")
                
        return matches