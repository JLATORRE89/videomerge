"""
Command-line interface for MP3-MKV Merger.

This module handles command-line argument parsing and CLI operation
of the MP3-MKV Merger application.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

from mp3_mkv_merger.core import MediaMerger
from mp3_mkv_merger.utils import get_default_directory, get_version, check_ffmpeg_installed, format_time

# Get logger
logger = logging.getLogger('mp3_mkv_merger.cli')

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='MP3-MKV Merger - Combine MP3 audio with MKV video files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Version information
    parser.add_argument('--version', action='version', 
                        version=f'MP3-MKV Merger {get_version()}')
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--web', action='store_true', 
                           help='Run in web UI mode (default)')
    mode_group.add_argument('--cli', action='store_true', 
                           help='Run in command-line mode')
    
    # Input/output paths
    default_dir = get_default_directory()
    parser.add_argument('--mp3', dest='mp3_dir', default=None,
                       help='Directory containing MP3 files')
    parser.add_argument('--mkv', dest='mkv_dir', default=None,
                       help='Directory containing MKV files')
    parser.add_argument('--out', dest='out_dir', default=None,
                       help='Directory for output files')
    
    # Audio options
    parser.add_argument('--replace', action='store_true', 
                       help='Replace original audio instead of adding as new track')
    parser.add_argument('--no-keep', dest='keep_original', action='store_false', 
                       help='Don\'t keep original audio track (when not replacing)')
    parser.add_argument('--normalize', action='store_true',
                       help='Normalize audio levels')
    parser.add_argument('--audio-codec', choices=['aac', 'mp3', 'copy'], default='aac',
                       help='Audio codec to use')
    
    # Video options
    parser.add_argument('--video-codec', choices=['copy', 'h264', 'hevc'], default=None,
                       help='Video codec to use (default: copy)')
    parser.add_argument('--output-format', choices=['mp4', 'webm', 'mov'], default='mp4',
                       help='Output file format (default: mp4)')
    
    # Social media options
    parser.add_argument('--social', action='store_true',
                       help='Optimize for social media')
    parser.add_argument('--social-width', type=int, default=1080,
                       help='Width for social media output')
    parser.add_argument('--social-height', type=int, default=1080,
                       help='Height for social media output')
    parser.add_argument('--social-format', choices=['mp4', 'mov'], default='mp4',
                       help='Format for social media output')
    
    # Monitoring options
    parser.add_argument('--watch', action='store_true',
                       help='Watch directories for new files')
    
    # Web UI options
    parser.add_argument('--port', type=int, default=8000,
                       help='Port for web server')
    
    # Logging options
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--log-file', default=None,
                       help='Log file path (default: auto-generated)')
    
    # Parse arguments
    args = parser.parse_args()
    
    return args

def run_cli(args):
    """
    Run in command-line mode.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check for ffmpeg
    if not check_ffmpeg_installed():
        logger.error("Error: ffmpeg not found in PATH. Please install ffmpeg.")
        print("Error: ffmpeg not found in PATH. Please install ffmpeg.")
        return False
    
    # Validate arguments
    if not args.mp3_dir or not args.mkv_dir or not args.out_dir:
        logger.error("Error: MP3 directory, MKV directory, and output directory must be specified.")
        print("Error: MP3 directory, MKV directory, and output directory must be specified.")
        print("Use --mp3, --mkv, and --out options to specify the paths.")
        return False
    
    # Check if directories exist
    if not os.path.exists(args.mp3_dir):
        logger.error(f"Error: MP3 directory '{args.mp3_dir}' does not exist.")
        print(f"Error: MP3 directory '{args.mp3_dir}' does not exist.")
        return False
    
    if not os.path.exists(args.mkv_dir):
        logger.error(f"Error: MKV directory '{args.mkv_dir}' does not exist.")
        print(f"Error: MKV directory '{args.mkv_dir}' does not exist.")
        return False
    
    # Create merger
    merger = MediaMerger(
        mp3_dir=args.mp3_dir,
        mkv_dir=args.mkv_dir,
        out_dir=args.out_dir,
        replace_audio=args.replace,
        keep_original=args.keep_original,
        normalize_audio=args.normalize,
        audio_codec=args.audio_codec,
        video_codec=args.video_codec,
        social_media=args.social,
        social_width=args.social_width,
        social_height=args.social_height,
        social_format=args.social_format,
        output_format=args.output_format
    )
    
    # Progress callback
    def progress_callback(message, percent):
        if percent >= 0:
            print(f"{message} ({percent}%)")
        else:
            print(message)
    
    merger.set_progress_callback(progress_callback)
    
    # Start file monitoring if requested
    if args.watch:
        logger.info("Starting file monitoring...")
        print("Starting file monitoring...")
        merger.start_file_monitoring(lambda msg: print(f"[WATCH] {msg}"))
    
    # Process files
    logger.info(f"Processing files from '{args.mp3_dir}' and '{args.mkv_dir}'...")
    print(f"Processing files from '{args.mp3_dir}' and '{args.mkv_dir}'...")
    print(f"Output directory: '{args.out_dir}'")
    
    if args.social:
        logger.info(f"Social media optimization enabled: {args.social_width}x{args.social_height}, {args.social_format}")
        print(f"Social media optimization enabled: {args.social_width}x{args.social_height}, {args.social_format}")
    
    logger.info(f"Output format: {args.output_format}")
    print(f"Output format: {args.output_format}")
    
    try:
        success = merger.process_all()
        if success:
            logger.info("Processing completed successfully.")
            print(f"Processing completed successfully.")
            return True
        else:
            logger.warning("Processing failed or was cancelled.")
            print("Processing failed or was cancelled.")
            return False
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
        print("\nOperation cancelled by user.")
        merger.stop()
        return False
    except Exception as e:
        logger.exception(f"Error processing files: {str(e)}")
        print(f"Error processing files: {str(e)}")
        return False