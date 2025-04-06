"""
Utility functions for MP3-MKV Merger.

This module contains utility functions used throughout the application,
including logging setup and file handling.
"""

import os
import sys
import logging
import platform
from datetime import datetime
from pathlib import Path

def setup_logging(debug=False, log_file=None):
    """
    Set up logging configuration.
    
    Args:
        debug (bool): Whether to enable debug logging
        log_file (str, optional): Path to log file, if None, auto-generate in logs directory
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Set log level based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Auto-generate log filename if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"mp3_mkv_merger_{timestamp}.log")
    elif not os.path.isabs(log_file):
        # If relative path, place in logs directory
        log_file = os.path.join(logs_dir, log_file)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Format for log messages
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        console_handler.setLevel(logging.WARNING)
        root_logger.warning(f"Could not create log file: {str(e)}")
    
    # Create a logger for this application
    logger = logging.getLogger('mp3_mkv_merger')
    
    # Log system info
    logger.info(f"MP3-MKV Merger starting")
    logger.info(f"System: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Log level: {'DEBUG' if debug else 'INFO'}")
    
    return logger

def get_default_directory():
    """
    Get the default directory for files based on user's OS.
    
    Returns:
        str: Path to videos directory
    """
    system = platform.system()
    home = str(Path.home())
    
    if system == "Windows":
        return os.path.join(home, "Videos")
    elif system == "Darwin":  # macOS
        return os.path.join(home, "Movies")
    else:  # Linux and others
        return os.path.join(home, "Videos")

def get_version():
    """
    Get the version of the application.
    
    Returns:
        str: Version string
    """
    try:
        from . import __version__
        return __version__
    except (ImportError, AttributeError):
        return "unknown"

def check_ffmpeg_installed():
    """
    Check if ffmpeg is installed and available in the PATH.
    
    Returns:
        bool: True if ffmpeg is available, False otherwise
    """
    import subprocess
    
    try:
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def format_time(seconds):
    """
    Format seconds into a human-readable time string.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string (HH:MM:SS)
    """
    if seconds is None:
        return "00:00:00"
        
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"