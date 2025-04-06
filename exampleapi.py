#!/usr/bin/env python3
"""
Example script showing how to use the MP3-MKV Merger API with direct path specification.
This script demonstrates both Windows and cross-platform path handling.
"""

import requests
import json
import time
import os
import sys
import argparse

# API configuration
API_BASE_URL = "http://localhost:8000/api"
API_KEY = "your_api_key_here"  # Replace with your actual API key

def start_processing(mp3_dir, mkv_dir, out_dir):
    """
    Start processing files using the API with direct path specification.
    
    Args:
        mp3_dir (str): Directory containing MP3 files
        mkv_dir (str): Directory containing MKV files
        out_dir (str): Output directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{API_BASE_URL}/start"
    
    # Create request payload
    payload = {
        "mp3Dir": mp3_dir,
        "mkvDir": mkv_dir,
        "outDir": out_dir,
        "replaceAudio": True,
        "keepOriginal": False,
        "normalizeAudio": True,
        "audioCodec": "aac",
        "videoCodec": "copy",
        "outputFormat": "mp4",
        "api_key": API_KEY
    }
    
    try:
        # Send request
        response = requests.post(url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"Processing started successfully with:")
                print(f"  MP3 Directory: {mp3_dir}")
                print(f"  MKV Directory: {mkv_dir}")
                print(f"  Output Directory: {out_dir}")
                return True
            else:
                print(f"Error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def find_matching_files(mp3_dir, mkv_dir):
    """
    Find matching MP3 and MKV files with direct path specification.
    
    Args:
        mp3_dir (str): Directory containing MP3 files
        mkv_dir (str): Directory containing MKV files
        
    Returns:
        list: List of matching file pairs or None if failed
    """
    url = f"{API_BASE_URL}/find_matches"
    
    # Create request payload
    payload = {
        "mp3Dir": mp3_dir,
        "mkvDir": mkv_dir,
        "api_key": API_KEY
    }
    
    try:
        # Send request
        response = requests.post(url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("matches", [])
            else:
                print(f"Error finding matches: {data.get('message', 'Unknown error')}")
                return None
        else:
            print(f"Error finding matches: HTTP {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error finding matches: {str(e)}")
        return None

def check_status():
    """
    Check the current processing status.
    
    Returns:
        dict: Status data or None if failed
    """
    url = f"{API_BASE_URL}/status?api_key={API_KEY}"
    
    try:
        # Send request
        response = requests.get(url)
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error checking status: HTTP {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error checking status: {str(e)}")
        return None

def stop_processing():
    """
    Stop the current processing operation.
    
    Returns:
        bool: True if stopped successfully, False otherwise
    """
    url = f"{API_BASE_URL}/stop"
    
    try:
        # Send request
        response = requests.post(url, json={"api_key": API_KEY})
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("Processing stopped successfully")
                return True
            else:
                print(f"Error stopping processing: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"Error stopping processing: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error stopping processing: {str(e)}")
        return False

def monitor_processing():
    """
    Monitor the processing operation until completion.
    """
    print("Monitoring processing status...")
    
    while True:
        # Check status
        status = check_status()
        
        if status is None:
            print("Failed to get status")
            break
            
        # Print status
        print(f"Status: {status['message']} ({status['percent']}%)")
        
        # Check if processing is complete
        if not status["running"]:
            if status["percent"] == 100:
                print("Processing completed successfully")
            else:
                print("Processing stopped or failed")
            break
            
        # Wait before checking again
        time.sleep(2)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='MP3-MKV Merger API Client')
    parser.add_argument('--mp3', required=True, help='Directory containing MP3 files')
    parser.add_argument('--mkv', required=True, help='Directory containing MKV files')
    parser.add_argument('--out', required=True, help='Output directory')
    parser.add_argument('--api-key', help='API key (overrides the default)')
    parser.add_argument('--find-only', action='store_true', 
                        help='Only find matching files without processing')
    parser.add_argument('--server', default='http://localhost:8000',
                        help='Server URL (default: http://localhost:8000)')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Update API configuration if provided
    if args.api_key:
        API_KEY = args.api_key
    
    if args.server:
        API_BASE_URL = f"{args.server}/api"
    
    # Ensure directories exist
    for path_name, path in [('MP3', args.mp3), ('MKV', args.mkv)]:
        if not os.path.exists(path):
            print(f"Error: {path_name} directory '{path}' does not exist")
            sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.out, exist_ok=True)
    
    # Find matching files
    print(f"Finding matching files...")
    print(f"  MP3 Directory: {args.mp3}")
    print(f"  MKV Directory: {args.mkv}")
    
    matches = find_matching_files(args.mp3, args.mkv)
    
    if matches:
        print(f"Found {len(matches)} matching pairs:")
        for i, match in enumerate(matches):
            print(f"  {i+1}. {match['mp3']} -> {match['mkv']}")
            print(f"     Output: {match['output']}")
        
        # Process files if not find-only mode
        if not args.find_only:
            if start_processing(args.mp3, args.mkv, args.out):
                # Monitor processing
                monitor_processing()
        else:
            print("\nFind-only mode enabled. No files were processed.")
    else:
        print("No matching files found or error occurred")