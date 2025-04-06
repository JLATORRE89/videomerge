#!/usr/bin/env python3
"""
Main entry point for MP3-MKV Merger.
"""

import sys
import os

from mp3_mkv_merger.cli import parse_args
from mp3_mkv_merger.core import MediaMerger
from mp3_mkv_merger.utils import setup_logging
from mp3_mkv_merger.web_ui import start_web_server


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(debug=args.debug, log_file=args.log_file)
    logger.info("MP3-MKV Merger starting")
    
    if args.cli:
        # Run in CLI mode
        from mp3_mkv_merger.cli import run_cli
        run_cli(args)
    else:
        # Run in web UI mode
        from mp3_mkv_merger.web_ui import run_web_ui
        run_web_ui(args)


if __name__ == "__main__":
    main()
