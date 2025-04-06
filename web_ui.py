"""
Web UI for MP3-MKV Merger.

This module provides a Flask-based web interface for the MP3-MKV Merger application.
"""

import os
import sys
import json
import logging
import threading
import webbrowser
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory, Response, render_template
except ImportError:
    raise ImportError("Flask not installed. Install with: pip install flask")

from .core import MediaMerger
from .utils import get_default_directory, check_ffmpeg_installed

# Get logger
logger = logging.getLogger('mp3_mkv_merger.web_ui')

# Global variables for web mode
merger_status = {"running": False, "message": "Ready", "percent": 0}
active_merger = None
merger_thread = None

# Create Flask app
app = Flask(__name__, static_folder='static')

def create_web_ui():
    """Create the necessary files for the web interface."""
    # Get the directory path
    module_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(module_dir, "static")
    
    # Create the static directory if it doesn't exist
    os.makedirs(static_dir, exist_ok=True)
    
    # Copy the manual.html file if it exists in the module directory
    manual_src = os.path.join(module_dir, "manual.html")
    manual_dst = os.path.join(static_dir, "manual.html")
    
    # If manual.html exists in the module directory, copy it to static
    if os.path.exists(manual_src):
        try:
            import shutil
            shutil.copy2(manual_src, manual_dst)
            logger.info(f"Copied manual.html to {manual_dst}")
        except Exception as e:
            logger.error(f"Error copying manual.html: {str(e)}")
    
    # Create CSS file
    css_content = """
/* CSS styles for MP3-MKV Merger web UI */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #2c3e50;
    margin-bottom: 20px;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}

.container {
    background: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"], input[type="number"] {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-sizing: border-box;
}

input[type="checkbox"] {
    margin-right: 5px;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 15px;
    cursor: pointer;
    border-radius: 4px;
    font-size: 16px;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #2980b9;
}

button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
}

.status {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 4px;
    margin-top: 20px;
    display: none;
}

.progress {
    height: 20px;
    background-color: #ecf0f1;
    border-radius: 4px;
    margin-top: 10px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background-color: #2ecc71;
    width: 0%;
    transition: width 0.5s;
}

.buttons {
    margin-top: 20px;
}

.buttons button {
    margin-right: 10px;
}

.advanced-toggle {
    cursor: pointer;
    color: #3498db;
    text-decoration: underline;
    margin-bottom: 15px;
    display: inline-block;
}

.advanced-options {
    display: none;
    padding-top: 10px;
    border-top: 1px solid #eee;
}

.option-row {
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 10px;
}

.option-group {
    flex: 1;
    min-width: 250px;
    margin-right: 20px;
}

.radio-group {
    margin-top: 5px;
}

@media (max-width: 768px) {
    .option-group {
        flex: 100%;
        margin-right: 0;
        margin-bottom: 10px;
    }
}
"""
    with open(os.path.join(static_dir, "styles.css"), "w", encoding="utf-8") as f:
        f.write(css_content)
    
    # Create JavaScript file
    js_content = """
// JavaScript for MP3-MKV Merger web UI
document.addEventListener('DOMContentLoaded', function() {
    // Toggle advanced options
    document.getElementById('advancedToggle').addEventListener('click', function() {
        const advancedOptions = document.getElementById('advancedOptions');
        const isHidden = advancedOptions.style.display === 'none' || advancedOptions.style.display === '';
        
        advancedOptions.style.display = isHidden ? 'block' : 'none';
        this.textContent = isHidden ? 'Hide Advanced Options' : 'Show Advanced Options';
    });
    
    // Handle output format changes
    const outputFormatSelect = document.getElementById('outputFormat');
    if (outputFormatSelect) {
        outputFormatSelect.addEventListener('change', function() {
            const selectedFormat = this.value;
            const videoCodecSelect = document.getElementById('videoCodec');
            const audioCodecSelect = document.getElementById('audioCodec');
            
            // Reset options first
            videoCodecSelect.querySelectorAll('option').forEach(opt => opt.disabled = false);
            audioCodecSelect.querySelectorAll('option').forEach(opt => opt.disabled = false);
            
            // Format-specific settings
            if (selectedFormat === 'webm') {
                // WebM typically uses VP8/VP9 for video and Opus/Vorbis for audio
                // Since we don't have these options explicitly, we'll just show a notice
                alert('Note: WebM format typically uses VP8/VP9 for video and Opus/Vorbis for audio codecs. ' +
                      'Your selected codecs will be mapped to appropriate WebM codecs.');
            }
        });
    }
    
    // Directory browse buttons
    document.querySelectorAll('.browse-button').forEach(function(button) {
        button.addEventListener('click', function() {
            const inputId = this.getAttribute('data-for');
            // This is just visual - in a web app we can't access file system directly
            alert('Browse functionality is simulated. Please enter the path manually.');
        });
    });
    
    // Start button handler
    document.getElementById('startButton').addEventListener('click', function() {
        const form = document.getElementById('mergerForm');
        
        // Basic validation
        if (!form.mp3Dir.value || !form.mkvDir.value || !form.outDir.value) {
            alert('Please fill in all directory paths');
            return;
        }
        
        // Show status area
        document.getElementById('status').style.display = 'block';
        document.getElementById('statusText').textContent = 'Starting...';
        document.getElementById('progressFill').style.width = '0%';
        
        // Disable start button, enable stop button
        this.disabled = true;
        document.getElementById('stopButton').disabled = false;
        
        // Collect form data
        const formData = {
            mp3Dir: form.mp3Dir.value,
            mkvDir: form.mkvDir.value,
            outDir: form.outDir.value,
            replaceAudio: form.replaceAudio.checked,
            keepOriginal: form.keepOriginal.checked,
            normalizeAudio: form.normalizeAudio.checked,
            audioCodec: form.audioCodec.value,
            videoCodec: form.videoCodec.value,
            outputFormat: form.outputFormat.value,
            socialMedia: form.socialMedia.checked,
            socialWidth: form.socialWidth.value,
            socialHeight: form.socialHeight.value,
            socialFormat: form.socialFormat.value
        };
        
        // Send the request
        fetch('/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Start status polling
                pollStatus();
            } else {
                document.getElementById('statusText').textContent = 'Error: ' + data.message;
                document.getElementById('startButton').disabled = false;
                document.getElementById('stopButton').disabled = true;
            }
        })
        .catch(error => {
            document.getElementById('statusText').textContent = 'Error: ' + error.message;
            document.getElementById('startButton').disabled = false;
            document.getElementById('stopButton').disabled = true;
        });
    });
    
    // Stop button handler
    document.getElementById('stopButton').addEventListener('click', function() {
        fetch('/stop', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('statusText').textContent = 'Operation stopped';
            }
        })
        .catch(error => {
            console.error('Error stopping operation:', error);
        });
        
        this.disabled = true;
    });
    
    // Find matches button handler
    document.getElementById('findMatchesButton').addEventListener('click', function() {
        const form = document.getElementById('mergerForm');
        
        // Basic validation
        if (!form.mp3Dir.value || !form.mkvDir.value) {
            alert('Please fill in MP3 and MKV directory paths');
            return;
        }
        
        // Disable button temporarily
        this.disabled = true;
        
        // Collect form data
        const formData = {
            mp3Dir: form.mp3Dir.value,
            mkvDir: form.mkvDir.value
        };
        
        // Send the request
        fetch('/find_matches', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            this.disabled = false;
            
            if (data.success) {
                if (data.matches.length > 0) {
                    let message = 'Found ' + data.matches.length + ' matching pairs:\n\n';
                    data.matches.forEach((match, index) => {
                        message += (index + 1) + '. ' + match.mp3 + ' ⟹ ' + match.mkv + '\n';
                    });
                    alert(message);
                } else {
                    alert('No matching files found');
                }
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            this.disabled = false;
            alert('Error: ' + error.message);
        });
    });
    
    // Status polling function
    function pollStatus() {
        fetch('/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('statusText').textContent = data.message;
            
            if (data.percent >= 0) {
                document.getElementById('progressFill').style.width = data.percent + '%';
            }
            
            if (data.running) {
                // Continue polling
                setTimeout(pollStatus, 1000);
            } else {
                // Reset UI
                document.getElementById('startButton').disabled = false;
                document.getElementById('stopButton').disabled = true;
                
                if (data.percent === 100) {
                    document.getElementById('statusText').textContent = 'Processing completed successfully';
                }
            }
        })
        .catch(error => {
            console.error('Error polling status:', error);
            document.getElementById('statusText').textContent = 'Error checking status';
            document.getElementById('startButton').disabled = false;
            document.getElementById('stopButton').disabled = true;
        });
    }
});
"""
    with open(os.path.join(static_dir, "script.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    
    # Create HTML template
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MP3-MKV Merger</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>MP3-MKV Merger</h1>
    <div style="text-align: right; margin-top: -40px;">
        <a href="/manual" target="_blank" style="color: #3498db; text-decoration: none;">
            User Manual
        </a>
    </div>
    
    <div class="container">
        <form id="mergerForm">
            <div class="form-group">
                <label for="mp3Dir">MP3 Directory:</label>
                <div style="display: flex;">
                    <input type="text" id="mp3Dir" name="mp3Dir" placeholder="Path to MP3 files">
                    <button type="button" class="browse-button" data-for="mp3Dir">Browse</button>
                </div>
            </div>
            
            <div class="form-group">
                <label for="mkvDir">MKV Directory:</label>
                <div style="display: flex;">
                    <input type="text" id="mkvDir" name="mkvDir" placeholder="Path to MKV files">
                    <button type="button" class="browse-button" data-for="mkvDir">Browse</button>
                </div>
            </div>
            
            <div class="form-group">
                <label for="outDir">Output Directory:</label>
                <div style="display: flex;">
                    <input type="text" id="outDir" name="outDir" placeholder="Path for output files">
                    <button type="button" class="browse-button" data-for="outDir">Browse</button>
                </div>
            </div>
            
            <div class="form-group">
                <input type="checkbox" id="replaceAudio" name="replaceAudio">
                <label for="replaceAudio" style="display: inline;">Replace original audio</label>
            </div>
            
            <div class="form-group">
                <input type="checkbox" id="keepOriginal" name="keepOriginal" checked>
                <label for="keepOriginal" style="display: inline;">Keep original audio track (when not replacing)</label>
            </div>
            
            <span id="advancedToggle" class="advanced-toggle">Show Advanced Options</span>
            
            <div id="advancedOptions" class="advanced-options">
                <div class="option-row">
                    <div class="option-group">
                        <label>Audio Options:</label>
                        <div class="form-group">
                            <input type="checkbox" id="normalizeAudio" name="normalizeAudio">
                            <label for="normalizeAudio" style="display: inline;">Normalize audio levels</label>
                        </div>
                        
                        <div class="form-group">
                            <label for="audioCodec">Audio Codec:</label>
                            <select id="audioCodec" name="audioCodec">
                                <option value="aac">AAC (recommended)</option>
                                <option value="mp3">MP3</option>
                                <option value="copy">Copy (no re-encoding)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="option-group">
                        <label>Video Options:</label>
                        <div class="form-group">
                            <label for="videoCodec">Video Codec:</label>
                            <select id="videoCodec" name="videoCodec">
                                <option value="copy">Copy (no re-encoding, recommended)</option>
                                <option value="h264">H.264</option>
                                <option value="hevc">H.265/HEVC</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="option-row">
                    <div class="option-group">
                        <div class="form-group">
                            <input type="checkbox" id="socialMedia" name="socialMedia">
                            <label for="socialMedia" style="display: inline;">Optimize for social media</label>
                        </div>
                        
                        <div class="form-group">
                            <label for="socialWidth">Width:</label>
                            <input type="number" id="socialWidth" name="socialWidth" value="1080">
                        </div>
                        
                        <div class="form-group">
                            <label for="socialHeight">Height:</label>
                            <input type="number" id="socialHeight" name="socialHeight" value="1080">
                        </div>
                        
                        <div class="form-group">
                            <label for="socialFormat">Format:</label>
                            <select id="socialFormat" name="socialFormat">
                                <option value="mp4">MP4</option>
                                <option value="mov">MOV</option>
                                <option value="webm">WebM</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="buttons">
                <button type="button" id="startButton">Start Processing</button>
                <button type="button" id="stopButton" disabled>Stop</button>
                <button type="button" id="findMatchesButton">Find Matches</button>
            </div>
        </form>
    </div>
    
    <div id="status" class="status">
        <div id="statusText">Ready</div>
        <div class="progress">
            <div id="progressFill" class="progress-fill"></div>
        </div>
    </div>
    
    <script src="script.js"></script>
</body>
</html>
"""
    with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info("Web UI files created successfully")

# Flask routes
@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/manual')
def manual():
    """Serve the user manual."""
    return send_from_directory(app.static_folder, 'manual.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory(app.static_folder, path)

@app.route('/status')
def status():
    """Get the current status."""
    return jsonify(merger_status)

@app.route('/start', methods=['POST'])
def start():
    """Start the merging process."""
    global merger_status, active_merger, merger_thread
    
    # Check if already running
    if merger_status["running"]:
        return jsonify({"success": False, "message": "Already running"})
    
    try:
        # Get request data
        data = request.json
        
        # Check if ffmpeg is installed
        if not check_ffmpeg_installed():
            return jsonify({
                "success": False, 
                "message": "ffmpeg not found. Please install ffmpeg."
            })
        
        # Validate directories
        if not os.path.exists(data["mp3Dir"]):
            return jsonify({
                "success": False, 
                "message": f"MP3 directory '{data['mp3Dir']}' does not exist"
            })
        
        if not os.path.exists(data["mkvDir"]):
            return jsonify({
                "success": False, 
                "message": f"MKV directory '{data['mkvDir']}' does not exist"
            })
        
        # Create output directory if it doesn't exist
        os.makedirs(data["outDir"], exist_ok=True)
        
        # Create merger
        active_merger = MediaMerger(
            mp3_dir=data["mp3Dir"],
            mkv_dir=data["mkvDir"],
            out_dir=data["outDir"],
            replace_audio=data.get("replaceAudio", False),
            keep_original=data.get("keepOriginal", True),
            normalize_audio=data.get("normalizeAudio", False),
            audio_codec=data.get("audioCodec", "aac"),
            video_codec=data.get("videoCodec", "copy") if data.get("videoCodec") != "copy" else None,
            social_media=data.get("socialMedia", False),
            social_width=int(data.get("socialWidth", 1080)),
            social_height=int(data.get("socialHeight", 1080)),
            social_format=data.get("socialFormat", "mp4"),
            output_format=data.get("outputFormat", "mp4")
        )
        
        # Set progress callback
        def progress_callback(message, percent):
            global merger_status
            merger_status["message"] = message
            merger_status["percent"] = percent
        
        active_merger.set_progress_callback(progress_callback)
        
        # Start merger in a separate thread
        merger_status["running"] = True
        merger_status["message"] = "Starting..."
        merger_status["percent"] = 0
        
        def run_merger():
            global merger_status, active_merger
            try:
                active_merger.process_all()
            except Exception as e:
                logger.exception(f"Error in merger thread: {str(e)}")
                merger_status["message"] = f"Error: {str(e)}"
                merger_status["percent"] = -1
            finally:
                merger_status["running"] = False
        
        merger_thread = threading.Thread(target=run_merger)
        merger_thread.daemon = True
        merger_thread.start()
        
        # Return success
        return jsonify({"success": True})
        
    except Exception as e:
        logger.exception(f"Error starting merger: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/stop', methods=['POST'])
def stop():
    """Stop the merging process."""
    global active_merger, merger_status
    
    # Stop the merger if running
    if merger_status["running"] and active_merger:
        try:
            active_merger.stop()
            merger_status["message"] = "Operation stopped by user"
            return jsonify({"success": True})
        except Exception as e:
            logger.exception(f"Error stopping merger: {str(e)}")
            return jsonify({"success": False, "message": str(e)})
    else:
        return jsonify({"success": False, "message": "Not running"})

@app.route('/find_matches', methods=['POST'])
def find_matches():
    """Find matching MP3 and MKV files."""
    try:
        # Get request data
        data = request.json
        
        # Validate directories
        if not os.path.exists(data["mp3Dir"]):
            return jsonify({
                "success": False, 
                "message": f"MP3 directory '{data['mp3Dir']}' does not exist"
            })
        
        if not os.path.exists(data["mkvDir"]):
            return jsonify({
                "success": False, 
                "message": f"MKV directory '{data['mkvDir']}' does not exist"
            })
        
        # Create temporary merger for finding matches
        temp_merger = MediaMerger(
            mp3_dir=data["mp3Dir"],
            mkv_dir=data["mkvDir"],
            out_dir=data.get("outDir", os.path.join(get_default_directory(), "output"))
        )
        
        # Find matches
        matches = temp_merger.find_matching_files()
        
        # Format matches for response
        match_list = [
            {
                "mp3": os.path.basename(match[0]),
                "mkv": os.path.basename(match[1])
            }
            for match in matches
        ]
        
        return jsonify({
            "success": True,
            "matches": match_list
        })
        
    except Exception as e:
        logger.exception(f"Error finding matches: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

def run_web_ui(args):
    """
    Run the application in web UI mode.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments
        
    Returns:
        None
    """
    # Create web UI files
    create_web_ui()
    
    # Check if ffmpeg is installed
    if not check_ffmpeg_installed():
        logger.warning("ffmpeg not found. Some functionality may not work.")
    
    # Set up host and port
    host = '127.0.0.1'  # localhost
    port = args.port or 8000
    
    # Log startup
    logger.info(f"Starting web server on http://{host}:{port}")
    print(f"Starting web server on http://{host}:{port}")
    print("Press Ctrl+C to stop")
    
    # Open browser
    threading.Thread(target=lambda: webbrowser.open(f"http://{host}:{port}")).start()
    
    # Run server
    try:
        app.run(host=host, port=port, debug=args.debug, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        logger.exception(f"Error running web server: {str(e)}")
        print(f"Error running web server: {str(e)}")

def start_web_server(port=8000):
    """
    Start the web UI server (legacy function for compatibility).
    
    Args:
        port (int): Port number for the web server
        
    Returns:
        None
    """
    # This function is kept for backward compatibility
    from argparse import Namespace
    args = Namespace(port=port, debug=False)
    run_web_ui(args)