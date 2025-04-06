#!/usr/bin/env python3
"""
Patch script to fix the MP3-MKV Merger project structure.
This script will:
1. Create a proper package structure
2. Move files to the correct locations
3. Fix import statements
4. Create a setup.py file if needed
"""

import os
import shutil
import re
import sys

def create_directory_structure():
    """Create the proper directory structure for the package."""
    print("Creating directory structure...")
    
    # Create mp3_mkv_merger package directory if it doesn't exist
    if not os.path.exists("mp3_mkv_merger"):
        os.makedirs("mp3_mkv_merger")
        print("  Created mp3_mkv_merger directory")
    
    # Create static directory for web UI files
    if not os.path.exists(os.path.join("mp3_mkv_merger", "static")):
        os.makedirs(os.path.join("mp3_mkv_merger", "static"))
        print("  Created mp3_mkv_merger/static directory")
    
    # Create logs directory
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("  Created logs directory")

def fix_import_statements(file_path):
    """Fix relative import statements in a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace relative imports with absolute imports
    modified_content = re.sub(
        r"from \.([\w]+) import", 
        r"from mp3_mkv_merger.\1 import", 
        content
    )
    
    # Replace non-relative imports of our modules
    modified_content = re.sub(
        r"from (core|cli|utils|web_ui) import", 
        r"from mp3_mkv_merger.\1 import", 
        modified_content
    )
    
    # Special case for main.py imports
    modified_content = re.sub(
        r"from (cli|utils|web_ui) import", 
        r"from mp3_mkv_merger.\1 import", 
        modified_content
    )
    
    # Write back the modified content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    return content != modified_content

def create_init_file():
    """Create or update the __init__.py file."""
    init_path = os.path.join("mp3_mkv_merger", "__init__.py")
    
    init_content = '''"""
MP3-MKV Merger - Combine MP3 audio files with MKV video files from OBS Studio.

This package provides functionality to merge MP3 audio files with MKV video files
using ffmpeg. It offers both a command-line interface and a web-based UI.
"""

__version__ = "1.0.0"
'''
    
    with open(init_path, "w", encoding="utf-8") as f:
        f.write(init_content)
    
    print(f"Created/updated {init_path}")

def create_setup_file():
    """Create or update the setup.py file."""
    setup_content = '''#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="mp3_mkv_merger",
    version="1.0.0",
    description="Combine MP3 audio files with MKV video files from OBS Studio",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "ffmpeg-python",
        "flask",
        "tqdm",
        "watchdog",
    ],
    entry_points={
        'console_scripts': [
            'mp3-mkv-merger=mp3_mkv_merger.main:main',
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
'''
    
    with open("setup.py", "w", encoding="utf-8") as f:
        f.write(setup_content)
    
    print("Created/updated setup.py")

def move_files():
    """Move Python files to the package directory."""
    files_to_move = [
        "main.py", "core.py", "cli.py", "utils.py", "web_ui.py"
    ]
    
    for file_name in files_to_move:
        if os.path.exists(file_name):
            # First, check if file already exists in package dir
            dest_path = os.path.join("mp3_mkv_merger", file_name)
            if os.path.exists(dest_path):
                # Backup the existing file
                backup_path = dest_path + ".bak"
                shutil.copy2(dest_path, backup_path)
                print(f"  Backed up existing {dest_path} to {backup_path}")
            
            # Move the file
            shutil.copy2(file_name, dest_path)
            print(f"  Moved {file_name} to mp3_mkv_merger/")
            
            # Fix imports in the moved file
            if fix_import_statements(dest_path):
                print(f"  Fixed imports in {dest_path}")
    
    # Look for mp3_mkv_merger.py and remove it if present
    if os.path.exists("mp3_mkv_merger.py"):
        legacy_backup = "mp3_mkv_merger.py.legacy"
        shutil.copy2("mp3_mkv_merger.py", legacy_backup)
        print(f"  Backed up mp3_mkv_merger.py to {legacy_backup}")
        # We don't delete it just in case

def move_static_files():
    """Move static files to the package static directory."""
    static_dir = os.path.join("mp3_mkv_merger", "static")
    
    # Look for HTML, CSS, JS files in the root static directory
    if os.path.exists("static"):
        for file_name in os.listdir("static"):
            src_path = os.path.join("static", file_name)
            if os.path.isfile(src_path):
                dest_path = os.path.join(static_dir, file_name)
                shutil.copy2(src_path, dest_path)
                print(f"  Moved static/{file_name} to mp3_mkv_merger/static/")

def create_runner_script():
    """Create a simple runner script in the root directory."""
    runner_content = '''#!/usr/bin/env python3
"""
Runner script for MP3-MKV Merger.
"""

from mp3_mkv_merger.main import main

if __name__ == "__main__":
    main()
'''
    
    with open("run_mp3_mkv_merger.py", "w", encoding="utf-8") as f:
        f.write(runner_content)
    
    print("Created run_mp3_mkv_merger.py")

def create_manual_file():
    """Create the manual.html file in the package directory."""
    # If manual.html exists in root, move it to the package
    if os.path.exists("manual.html"):
        dest_path = os.path.join("mp3_mkv_merger", "manual.html")
        shutil.copy2("manual.html", dest_path)
        print(f"  Copied manual.html to {dest_path}")
        
        # Also copy to static directory
        static_path = os.path.join("mp3_mkv_merger", "static", "manual.html")
        shutil.copy2("manual.html", static_path)
        print(f"  Copied manual.html to {static_path}")
    else:
        print("  Warning: manual.html not found in root directory")

def main():
    """Main function to patch the project."""
    print("Starting MP3-MKV Merger project structure patch...")
    
    # Check if we're in the right directory
    if not any(os.path.exists(f) for f in ["main.py", "core.py", "mp3_mkv_merger.py"]):
        print("Error: This script should be run from the project root directory.")
        print("Please place it in the directory containing main.py, core.py, etc.")
        return 1
    
    try:
        # Create directory structure
        create_directory_structure()
        
        # Move files to package directory
        move_files()
        
        # Move static files
        move_static_files()
        
        # Create/update __init__.py
        create_init_file()
        
        # Create/update setup.py
        create_setup_file()
        
        # Create runner script
        create_runner_script()
        
        # Create/copy manual file
        create_manual_file()
        
        print("\nPatch completed successfully!")
        print("\nYou can now run the application in one of these ways:")
        print("1. From the project root directory:")
        print("   python run_mp3_mkv_merger.py")
        print("\n2. As a module:")
        print("   python -m mp3_mkv_merger.main")
        print("\n3. Install the package and use the command-line tool:")
        print("   pip install -e .")
        print("   mp3-mkv-merger")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())