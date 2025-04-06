#!/usr/bin/env python3
"""
MP3-MKV Merger Integration Client Example

This script demonstrates how to use the MP3-MKV Merger API
within the ContentCreatorTools integrated environment.
"""

import requests
import json
import time
import os
import sys
import argparse
from datetime import datetime

class MP3MKVClient:
    """Client for the MP3-MKV Merger Integration API"""
    
    def __init__(self, base_url, api_key):
        """
        Initialize the client with base URL and API key
        
        Args:
            base_url (str): Base URL of the API (e.g., http://localhost:5000)
            api_key (str): API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def find_matches(self, mp3_dir, mkv_dir):
        """
        Find matching MP3 and MKV files
        
        Args:
            mp3_dir (str): Directory containing MP3 files
            mkv_dir (str): Directory containing MKV files
            
        Returns:
            dict: API response with matches
        """
        url = f"{self.base_url}/api/find_matches"
        payload = {
            "mp3Dir": mp3_dir,
            "mkvDir": mkv_dir,
            "api_key": self.api_key
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(response)
    
    def start_job(self, mp3_dir, mkv_dir, out_dir, options=None):
        """
        Start a new processing job
        
        Args:
            mp3_dir (str): Directory containing MP3 files
            mkv_dir (str): Directory containing MKV files
            out_dir (str): Output directory for processed files
            options (dict, optional): Additional options for processing
            
        Returns:
            dict: API response with job details
        """
        url = f"{self.base_url}/api/start"
        
        # Default options
        payload = {
            "mp3Dir": mp3_dir,
            "mkvDir": mkv_dir,
            "outDir": out_dir,
            "api_key": self.api_key
        }
        
        # Add additional options if provided
        if options:
            payload.update(options)
        
        response = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(response)
    
    def get_job_status(self, job_id):
        """
        Get the status of a job
        
        Args:
            job_id (int): ID of the job
            
        Returns:
            dict: API response with job status
        """
        url = f"{self.base_url}/api/status/{job_id}?api_key={self.api_key}"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def stop_job(self, job_id):
        """
        Stop a running job
        
        Args:
            job_id (int): ID of the job
            
        Returns:
            dict: API response with stop status
        """
        url = f"{self.base_url}/api/stop/{job_id}"
        payload = {
            "api_key": self.api_key
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(response)
    
    def get_jobs(self, limit=20):
        """
        Get a list of jobs
        
        Args:
            limit (int, optional): Maximum number of jobs to return
            
        Returns:
            dict: API response with job list
        """
        url = f"{self.base_url}/api/jobs?api_key={self.api_key}&limit={limit}"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def get_preferences(self):
        """
        Get user preferences
        
        Returns:
            dict: API response with preferences
        """
        url = f"{self.base_url}/api/preferences?api_key={self.api_key}"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def update_preferences(self, preferences):
        """
        Update user preferences
        
        Args:
            preferences (dict): New preferences to set
            
        Returns:
            dict: API response with update status
        """
        url = f"{self.base_url}/api/preferences"
        payload = preferences.copy()
        payload["api_key"] = self.api_key
        
        response = requests.post(url, json=payload, headers=self.headers)
        return self._handle_response(response)
    
    def _handle_response(self, response):
        """Handle API response and error cases"""
        try:
            data = response.json()
            
            if response.status_code >= 400:
                error_msg = data.get('message', f"Error: HTTP {response.status_code}")
                print(f"API Error: {error_msg}")
            
            return data
        except ValueError:
            print(f"Error: Invalid JSON response - {response.text}")
            return {"success": False, "message": "Invalid response format"}
        except Exception as e:
            print(f"Error handling response: {str(e)}")
            return {"success": False, "message": str(e)}

def monitor_job(client, job_id, interval=2):
    """
    Monitor a job until completion
    
    Args:
        client (MP3MKVClient): Client instance
        job_id (int): Job ID to monitor
        interval (int): Polling interval in seconds
        
    Returns:
        bool: True if job completed successfully, False otherwise
    """
    print(f"Monitoring job {job_id}...")
    
    try:
        while True:
            response = client.get_job_status(job_id)
            
            if not response.get('success'):
                print(f"Error monitoring job: {response.get('message')}")
                return False
            
            job = response.get('job', {})
            status = job.get('status')
            progress = job.get('progress', 0)
            message = job.get('message', 'No status message')
            
            # Format timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message} ({progress}%)")
            
            # Check if job has finished
            if status in ['completed', 'failed', 'stopped']:
                if status == 'completed':
                    print(f"Job {job_id} completed successfully!")
                    return True
                else:
                    print(f"Job {job_id} {status}: {message}")
                    return False
            
            # Wait before checking again
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nMonitoring interrupted. Attempting to stop job...")
        client.stop_job(job_id)
        return False

def format_job_list(jobs):
    """Format job list for display"""
    if not jobs:
        return "No jobs found."
    
    result = []
    result.append("ID    Status     Progress  Created             Message")
    result.append("-----------------------------------------------------------")
    
    for job in jobs:
        job_id = job.get('id', 'N/A')
        status = job.get('status', 'unknown')
        progress = job.get('progress', 0)
        created = job.get('created_at', 'N/A')
        message = job.get('message', 'No message')
        
        # Truncate message if too long
        if len(message) > 40:
            message = message[:37] + "..."
        
        # Format the line
        result.append(f"{job_id:<5} {status:<10} {progress:>3}%     {created[:16]}  {message}")
    
    return "\n".join(result)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='MP3-MKV Merger Client')
    
    # Server and authentication
    parser.add_argument('--server', default='http://localhost:5000',
                        help='Server URL (default: http://localhost:5000)')
    parser.add_argument('--api-key', required=True,
                        help='API key for authentication')
    
    # Commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Find matches command
    find_parser = subparsers.add_parser('find', help='Find matching files')
    find_parser.add_argument('--mp3', required=True, help='Directory containing MP3 files')
    find_parser.add_argument('--mkv', required=True, help='Directory containing MKV files')
    
    # Start job command
    start_parser = subparsers.add_parser('start', help='Start a processing job')
    start_parser.add_argument('--mp3', required=True, help='Directory containing MP3 files')
    start_parser.add_argument('--mkv', required=True, help='Directory containing MKV files')
    start_parser.add_argument('--out', required=True, help='Output directory')
    start_parser.add_argument('--replace-audio', action='store_true', help='Replace original audio')
    start_parser.add_argument('--keep-original', action='store_true', help='Keep original audio track')
    start_parser.add_argument('--normalize', action='store_true', help='Normalize audio levels')
    start_parser.add_argument('--monitor', action='store_true', help='Monitor job progress')
    
    # Job status command
    status_parser = subparsers.add_parser('status', help='Get job status')
    status_parser.add_argument('--job-id', type=int, required=True, help='Job ID to check')
    status_parser.add_argument('--monitor', action='store_true', help='Monitor job progress')
    
    # Stop job command
    stop_parser = subparsers.add_parser('stop', help='Stop a running job')
    stop_parser.add_argument('--job-id', type=int, required=True, help='Job ID to stop')
    
    # List jobs command
    list_parser = subparsers.add_parser('list', help='List jobs')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum number of jobs to return')
    
    # Get preferences command
    prefs_parser = subparsers.add_parser('preferences', help='Get user preferences')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    if not args.command:
        print("Error: No command specified. Use --help for available commands.")
        return 1
    
    # Create client
    client = MP3MKVClient(args.server, args.api_key)
    
    if args.command == 'find':
        # Find matching files
        print(f"Finding matching files in:")
        print(f"  MP3 directory: {args.mp3}")
        print(f"  MKV directory: {args.mkv}")
        
        response = client.find_matches(args.mp3, args.mkv)
        
        if response.get('success'):
            matches = response.get('matches', [])
            print(f"\nFound {len(matches)} matching pairs:")
            
            for i, match in enumerate(matches, 1):
                print(f"  {i}. {match['mp3']} → {match['mkv']}")
                print(f"     Output: {match['output']}")
        else:
            print(f"Error: {response.get('message', 'Unknown error')}")
            return 1
    
    elif args.command == 'start':
        # Start a job
        print(f"Starting processing job:")
        print(f"  MP3 directory: {args.mp3}")
        print(f"  MKV directory: {args.mkv}")
        print(f"  Output directory: {args.out}")
        
        # Build options
        options = {}
        if args.replace_audio:
            options['replaceAudio'] = True
        if args.keep_original:
            options['keepOriginal'] = True
        if args.normalize:
            options['normalizeAudio'] = True
        
        response = client.start_job(args.mp3, args.mkv, args.out, options)
        
        if response.get('success'):
            job_id = response.get('job_id')
            print(f"Job started successfully with ID: {job_id}")
            
            if args.monitor:
                monitor_job(client, job_id)
        else:
            print(f"Error: {response.get('message', 'Unknown error')}")
            return 1
    
    elif args.command == 'status':
        # Get job status
        response = client.get_job_status(args.job_id)
        
        if response.get('success'):
            job = response.get('job', {})
            print(f"Job {args.job_id} Status:")
            print(f"  Status: {job.get('status', 'unknown')}")
            print(f"  Progress: {job.get('progress', 0)}%")
            print(f"  Message: {job.get('message', 'No message')}")
            print(f"  Created: {job.get('created_at', 'N/A')}")
            print(f"  Completed: {job.get('completed_at', 'N/A')}")
            
            if args.monitor and job.get('status') in ['pending', 'running']:
                monitor_job(client, args.job_id)
        else:
            print(f"Error: {response.get('message', 'Unknown error')}")
            return 1
    
    elif args.command == 'stop':
        # Stop a job
        response = client.stop_job(args.job_id)
        
        if response.get('success'):
            print(f"Job {args.job_id} stopped successfully")
        else:
            print(f"Error: {response.get('message', 'Unknown error')}")
            return 1
    
    elif args.command == 'list':
        # List jobs
        response = client.get_jobs(args.limit)
        
        if response.get('success'):
            jobs = response.get('jobs', [])
            print(format_job_list(jobs))
        else:
            print(f"Error: {response.get('message', 'Unknown error')}")
            return 1
    
    elif args.command == 'preferences':
        # Get preferences
        response = client.get_preferences()
        
        if response.get('success'):
            prefs = response.get('preferences', {})
            print("User Preferences:")
            
            for key, value in sorted(prefs.items()):
                print(f"  {key}: {value}")
        else:
            print(f"Error: {response.get('message', 'Unknown error')}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())