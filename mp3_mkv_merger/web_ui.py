"""
Web UI for MP3-MKV Merger.

This module provides a Flask-based web interface for the MP3-MKV Merger application.
It supports multiple users with user-specific configurations and status tracking.
"""

import os
import sys
import json
import logging
import threading
import webbrowser
import uuid
from pathlib import Path
from typing import Dict, Any

try:
    from flask import Flask, request, jsonify, send_from_directory, Response, render_template, redirect, url_for, session
except ImportError:
    raise ImportError("Flask not installed. Install with: pip install flask")

from .core import MediaMerger
from .utils import get_default_directory, check_ffmpeg_installed

# Get logger
logger = logging.getLogger('mp3_mkv_merger.web_ui')

# Dictionary to store user-specific merger data
# Format: {username: {"status": {...}, "merger": MediaMerger, "thread": Thread}}
user_data = {}

# Secret key for sessions
SECRET_KEY = os.environ.get('SECRET_KEY') or uuid.uuid4().hex

# Create Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = SECRET_KEY

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
    
    # Create CSS file with additional user profile styles
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

/* User profile styles */
.user-profile {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.user-info {
    display: flex;
    align-items: center;
}

.username {
    font-weight: bold;
    margin-left: 10px;
    color: #2c3e50;
}

.nav-links {
    display: flex;
    gap: 20px;
}

.nav-links a {
    color: #3498db;
    text-decoration: none;
}

.nav-links a:hover {
    text-decoration: underline;
}

.api-key {
    font-family: monospace;
    padding: 5px 10px;
    background-color: #f1f1f1;
    border-radius: 3px;
    margin-left: 10px;
}

.copy-btn {
    background-color: #e0e0e0;
    color: #333;
    border: none;
    padding: 3px 8px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 12px;
    margin-left: 5px;
}

.api-docs {
    margin-top: 20px;
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.api-endpoint {
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid #eee;
}

.endpoint-url {
    font-family: monospace;
    background-color: #f1f1f1;
    padding: 5px;
    border-radius: 3px;
}

code {
    font-family: monospace;
    background-color: #f1f1f1;
    padding: 2px 4px;
    border-radius: 3px;
}

@media (max-width: 768px) {
    .option-group {
        flex: 100%;
        margin-right: 0;
        margin-bottom: 10px;
    }
    
    .user-profile {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .nav-links {
        margin-top: 10px;
    }
}
"""
    with open(os.path.join(static_dir, "styles.css"), "w", encoding="utf-8") as f:
        f.write(css_content)
    
    # Create JavaScript file with user-specific functionality
    js_content = """
// JavaScript for MP3-MKV Merger web UI
document.addEventListener('DOMContentLoaded', function() {
    // Copy API key to clipboard
    const copyApiButton = document.getElementById('copyApiKey');
    if (copyApiButton) {
        copyApiButton.addEventListener('click', function() {
            const apiKey = document.getElementById('apiKeyText').textContent;
            navigator.clipboard.writeText(apiKey).then(function() {
                copyApiButton.textContent = 'Copied!';
                setTimeout(function() {
                    copyApiButton.textContent = 'Copy';
                }, 2000);
            });
        });
    }

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
            if (videoCodecSelect) {
                videoCodecSelect.querySelectorAll('option').forEach(opt => opt.disabled = false);
            }
            if (audioCodecSelect) {
                audioCodecSelect.querySelectorAll('option').forEach(opt => opt.disabled = false);
            }
            
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
            alert('Browse functionality is simulated in the web interface. Please enter the path manually.');
            
            // For testing, you can set some example paths
            const input = document.getElementById(inputId);
            if (inputId === 'mp3Dir') {
                input.value = input.value || 'C:\\Users\\Music\\MP3';
            } else if (inputId === 'mkvDir') {
                input.value = input.value || 'C:\\Users\\Videos\\MKV';
            } else if (inputId === 'outDir') {
                input.value = input.value || 'C:\\Users\\Videos\\Output';
            }
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
        document.getElementById('findMatchesButton').disabled = true;
        
        // Get username from hidden input
        const username = document.getElementById('username').value;
        
        // Collect form data
        const formData = {
            mp3Dir: form.mp3Dir.value,
            mkvDir: form.mkvDir.value,
            outDir: form.outDir.value,
            replaceAudio: form.replaceAudio.checked,
            keepOriginal: form.keepOriginal.checked,
            normalizeAudio: form.normalizeAudio ? form.normalizeAudio.checked : false,
            audioCodec: form.audioCodec ? form.audioCodec.value : 'aac',
            videoCodec: form.videoCodec ? form.videoCodec.value : 'copy',
            outputFormat: form.outputFormat ? form.outputFormat.value : 'mp4',
            socialMedia: form.socialMedia ? form.socialMedia.checked : false,
            socialWidth: form.socialWidth ? form.socialWidth.value : 1080,
            socialHeight: form.socialHeight ? form.socialHeight.value : 1080,
            socialFormat: form.socialFormat ? form.socialFormat.value : 'mp4',
            username: username
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
                // Start status polling with username
                pollStatus(username);
            } else {
                document.getElementById('statusText').textContent = 'Error: ' + data.message;
                document.getElementById('startButton').disabled = false;
                document.getElementById('stopButton').disabled = true;
                document.getElementById('findMatchesButton').disabled = false;
            }
        })
        .catch(error => {
            document.getElementById('statusText').textContent = 'Error: ' + error.message;
            document.getElementById('startButton').disabled = false;
            document.getElementById('stopButton').disabled = true;
            document.getElementById('findMatchesButton').disabled = false;
        });
    });
    
    // Stop button handler
    document.getElementById('stopButton').addEventListener('click', function() {
        const username = document.getElementById('username').value;
        
        fetch('/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('statusText').textContent = 'Operation stopped';
                document.getElementById('startButton').disabled = false;
                document.getElementById('findMatchesButton').disabled = false;
            }
            this.disabled = true;
        })
        .catch(error => {
            console.error('Error stopping operation:', error);
        });
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
        
        // Get username from hidden input
        const username = document.getElementById('username').value;
        
        // Collect form data
        const formData = {
            mp3Dir: form.mp3Dir.value,
            mkvDir: form.mkvDir.value,
            username: username
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
                    let message = 'Found ' + data.matches.length + ' matching pairs:\\n\\n';
                    data.matches.forEach((match, index) => {
                        message += (index + 1) + '. ' + match.mp3 + ' ⟹ ' + match.mkv + '\\n';
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
    function pollStatus(username) {
        fetch(`/status?user=${encodeURIComponent(username)}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('statusText').textContent = data.message;
            
            if (data.percent >= 0) {
                document.getElementById('progressFill').style.width = data.percent + '%';
            }
            
            if (data.running) {
                // Continue polling
                setTimeout(() => pollStatus(username), 1000);
            } else {
                // Reset UI
                document.getElementById('startButton').disabled = false;
                document.getElementById('stopButton').disabled = true;
                document.getElementById('findMatchesButton').disabled = false;
                
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
            document.getElementById('findMatchesButton').disabled = false;
        });
    }
});
"""
    with open(os.path.join(static_dir, "script.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    
    # Create HTML template with user profile section
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MP3-MKV Merger</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <h1>MP3-MKV Merger</h1>
    
    <div class="user-profile">
        <div class="user-info">
            <span>User:</span>
            <span class="username">{{ username }}</span>
            <input type="hidden" id="username" value="{{ username }}">
        </div>
        <div class="nav-links">
            <a href="/api-docs?user={{ username }}">API Documentation</a>
            <a href="/manual" target="_blank">User Manual</a>
        </div>
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
                        
                        <div class="form-group">
                            <label for="outputFormat">Output Format:</label>
                            <select id="outputFormat" name="outputFormat">
                                <option value="mp4">MP4 (recommended)</option>
                                <option value="webm">WebM</option>
                                <option value="mov">MOV</option>
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
    
    <script src="/script.js"></script>
</body>
</html>
"""
    with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Create API docs template
    api_docs_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MP3-MKV Merger API Documentation</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <h1>MP3-MKV Merger API Documentation</h1>
    
    <div class="user-profile">
        <div class="user-info">
            <span>User:</span>
            <span class="username">{{ username }}</span>
            <span class="api-key" id="apiKeyText">{{ api_key }}</span>
            <button id="copyApiKey" class="copy-btn">Copy</button>
        </div>
        <div class="nav-links">
            <a href="/?user={{ username }}">Back to Dashboard</a>
            <a href="/manual" target="_blank">User Manual</a>
        </div>
    </div>
    
    <div class="api-docs">
        <h2>API Endpoints</h2>
        <p>All API requests require an <code>api_key</code> parameter that matches your user's API key.</p>
        
        <div class="api-endpoint">
            <h3>Start Processing</h3>
            <div class="endpoint-url">POST /api/start</div>
            <p>Start processing MP3 and MKV files.</p>
            <h4>Request Format:</h4>
            <pre><code>{
  "mp3Dir": "/path/to/mp3",
  "mkvDir": "/path/to/mkv",
  "outDir": "/path/to/output",
  "replaceAudio": false,
  "keepOriginal": true,
  "normalizeAudio": false,
  "audioCodec": "aac",
  "videoCodec": "copy",
  "outputFormat": "mp4",
  "socialMedia": false,
  "socialWidth": 1080,
  "socialHeight": 1080,
  "socialFormat": "mp4",
  "api_key": "your-api-key"
}</code></pre>
        </div>
        
        <div class="api-endpoint">
            <h3>Get Status</h3>
            <div class="endpoint-url">GET /api/status?api_key=your-api-key</div>
            <p>Get the current status of the processing operation.</p>
            <h4>Response Format:</h4>
            <pre><code>{
  "running": true|false,
  "message": "Processing file 2 of 10...",
  "percent": 45
}</code></pre>
        </div>
        
        <div class="api-endpoint">
            <h3>Stop Processing</h3>
            <div class="endpoint-url">POST /api/stop</div>
            <p>Stop the current processing operation.</p>
            <h4>Request Format:</h4>
            <pre><code>{
  "api_key": "your-api-key"
}</code></pre>
        </div>
        
        <div class="api-endpoint">
            <h3>Find Matching Files</h3>
            <div class="endpoint-url">POST /api/find_matches</div>
            <p>Find matching MP3 and MKV files in the specified directories.</p>
            <h4>Request Format:</h4>
            <pre><code>{
  "mp3Dir": "/path/to/mp3",
  "mkvDir": "/path/to/mkv",
  "api_key": "your-api-key"
}</code></pre>
            <h4>Response Format:</h4>
            <pre><code>{
  "success": true,
  "matches": [
    { "mp3": "audio1.mp3", "mkv": "video1.mkv" },
    { "mp3": "audio2.mp3", "mkv": "video2.mkv" }
  ]
}</code></pre>
        </div>
    </div>
    
    <script src="/script.js"></script>
</body>
</html>
"""
    with open(os.path.join(static_dir, "api_docs.html"), "w", encoding="utf-8") as f:
        f.write(api_docs_template)
    
    logger.info("Web UI files created successfully")

# Flask routes
@app.route('/')
def index():
    """Serve the main page with user context."""
    username = get_username_from_request()
    
    # Render the index template with the username
    return render_template('index.html', username=username)

@app.route('/manual')
def manual():
    """Serve the user manual."""
    return send_from_directory(app.static_folder, 'manual.html')

@app.route('/api-docs')
def api_docs():
    """Serve the API documentation."""
    username = get_username_from_request()
    user = get_user_data(username)
    
    # Render the API docs template with the username and API key
    return render_template('api_docs.html', 
                           username=username, 
                           api_key=user.get('api_key', 'N/A'))

@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory(app.static_folder, path)

@app.route('/status')
def status():
    """Get the current status for a user."""
    username = get_username_from_request()
    user = get_user_data(username)
    
    return jsonify(user['status'])

@app.route('/start', methods=['POST'])
def start():
    """Start the merging process for a user."""
    global user_data
    
    # Get username from request
    if request.is_json:
        username = request.json.get('username', 'default')
    else:
        username = request.form.get('username', 'default')
    
    # Get user data
    user = get_user_data(username)
    
    # Check if already running
    if user['status']['running']:
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
        user['merger'] = MediaMerger(
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
            user['status']['message'] = message
            user['status']['percent'] = percent
        
        user['merger'].set_progress_callback(progress_callback)
        
        # Start merger in a separate thread
        user['status']['running'] = True
        user['status']['message'] = "Starting..."
        user['status']['percent'] = 0
        
        def run_merger():
            try:
                user['merger'].process_all()
            except Exception as e:
                logger.exception(f"Error in merger thread for '{username}': {str(e)}")
                user['status']['message'] = f"Error: {str(e)}"
                user['status']['percent'] = -1
            finally:
                user['status']['running'] = False
        
        user['thread'] = threading.Thread(target=run_merger)
        user['thread'].daemon = True
        user['thread'].start()
        
        # Return success
        return jsonify({"success": True})
        
    except Exception as e:
        logger.exception(f"Error starting merger for '{username}': {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/stop', methods=['POST'])
def stop():
    """Stop the merging process for a user."""
    # Get username from request
    if request.is_json:
        username = request.json.get('username', 'default')
    else:
        username = request.form.get('username', 'default')
    
    # Get user data
    user = get_user_data(username)
    
    # Stop the merger if running
    if user['status']['running'] and user['merger']:
        try:
            user['merger'].stop()
            user['status']['message'] = "Operation stopped by user"
            return jsonify({"success": True})
        except Exception as e:
            logger.exception(f"Error stopping merger for '{username}': {str(e)}")
            return jsonify({"success": False, "message": str(e)})
    else:
        return jsonify({"success": False, "message": "Not running"})

@app.route('/find_matches', methods=['POST'])
def find_matches():
    """Find matching MP3 and MKV files for a user."""
    try:
        # Get request data
        data = request.json
        
        # Get username
        username = data.get('username', 'default')
        
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

# API Routes
@app.route('/api/start', methods=['POST'])
def api_start():
    """API endpoint to start processing."""
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    
    # Check API key
    is_valid, username = check_api_key(request.json)
    if not is_valid:
        return jsonify({"success": False, "message": "Invalid API key"}), 401
    
    # Add username to request data and forward to regular start endpoint
    data = request.json.copy()
    data['username'] = username
    
    # Validate required path parameters
    required_params = ['mp3Dir', 'mkvDir', 'outDir']
    for param in required_params:
        if param not in data:
            return jsonify({
                "success": False, 
                "message": f"Missing required parameter: {param}"
            }), 400
    
    # Direct path validation for API
    if not os.path.exists(data["mp3Dir"]):
        return jsonify({
            "success": False, 
            "message": f"MP3 directory '{data['mp3Dir']}' does not exist"
        }), 404
    
    if not os.path.exists(data["mkvDir"]):
        return jsonify({
            "success": False, 
            "message": f"MKV directory '{data['mkvDir']}' does not exist"
        }), 404
    
    # Create output directory if it doesn't exist
    os.makedirs(data["outDir"], exist_ok=True)
    
    # Start the merging process directly for API calls
    try:
        # Get user data
        user = get_user_data(username)
        
        # Check if already running
        if user['status']['running']:
            return jsonify({"success": False, "message": "Already running"}), 409
        
        # Check if ffmpeg is installed
        if not check_ffmpeg_installed():
            return jsonify({
                "success": False, 
                "message": "ffmpeg not found. Please install ffmpeg."
            }), 500
        
        # Create merger
        user['merger'] = MediaMerger(
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
            user['status']['message'] = message
            user['status']['percent'] = percent
        
        user['merger'].set_progress_callback(progress_callback)
        
        # Start merger in a separate thread
        user['status']['running'] = True
        user['status']['message'] = "Starting..."
        user['status']['percent'] = 0
        
        def run_merger():
            try:
                user['merger'].process_all()
            except Exception as e:
                logger.exception(f"Error in merger thread for '{username}': {str(e)}")
                user['status']['message'] = f"Error: {str(e)}"
                user['status']['percent'] = -1
            finally:
                user['status']['running'] = False
        
        user['thread'] = threading.Thread(target=run_merger)
        user['thread'].daemon = True
        user['thread'].start()
        
        # Return success with details about the job
        return jsonify({
            "success": True, 
            "message": "Processing started",
            "job": {
                "mp3Dir": data["mp3Dir"],
                "mkvDir": data["mkvDir"],
                "outDir": data["outDir"],
                "username": username
            }
        })
        
    except Exception as e:
        logger.exception(f"Error starting merger for '{username}': {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """API endpoint to get status."""
    # Check API key
    is_valid, username = check_api_key(request.args)
    if not is_valid:
        return jsonify({"success": False, "message": "Invalid API key"}), 401
    
    # Get user data
    user = get_user_data(username)
    
    return jsonify(user['status'])

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """API endpoint to stop processing."""
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    
    # Check API key
    is_valid, username = check_api_key(request.json)
    if not is_valid:
        return jsonify({"success": False, "message": "Invalid API key"}), 401
    
    # Add username to request data and forward to regular stop endpoint
    data = request.json.copy()
    data['username'] = username
    request.json = data
    
    return stop()

@app.route('/api/find_matches', methods=['POST'])
def api_find_matches():
    """API endpoint to find matches."""
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    
    # Check API key
    is_valid, username = check_api_key(request.json)
    if not is_valid:
        return jsonify({"success": False, "message": "Invalid API key"}), 401
    
    # Get request data
    data = request.json.copy()
    data['username'] = username
    
    # Validate required parameters
    required_params = ['mp3Dir', 'mkvDir']
    for param in required_params:
        if param not in data:
            return jsonify({
                "success": False, 
                "message": f"Missing required parameter: {param}"
            }), 400
    
    # Validate directories
    if not os.path.exists(data["mp3Dir"]):
        return jsonify({
            "success": False, 
            "message": f"MP3 directory '{data['mp3Dir']}' does not exist"
        }), 404
    
    if not os.path.exists(data["mkvDir"]):
        return jsonify({
            "success": False, 
            "message": f"MKV directory '{data['mkvDir']}' does not exist"
        }), 404
    
    # Create temporary merger for finding matches
    try:
        temp_merger = MediaMerger(
            mp3_dir=data["mp3Dir"],
            mkv_dir=data["mkvDir"],
            out_dir=data.get("outDir", os.path.join(get_default_directory(), "output"))
        )
        
        # Find matches
        matches = temp_merger.find_matching_files()
        
        # Format matches for response
        match_list = []
        for match in matches:
            mp3_file = os.path.basename(match[0])
            mkv_file = os.path.basename(match[1])
            output_file = os.path.basename(match[2])
            
            match_list.append({
                "mp3": mp3_file,
                "mp3_full_path": match[0],
                "mkv": mkv_file,
                "mkv_full_path": match[1],
                "output": output_file,
                "output_full_path": match[2]
            })
        
        return jsonify({
            "success": True,
            "matches": match_list,
            "total_matches": len(match_list),
            "mp3_dir": data["mp3Dir"],
            "mkv_dir": data["mkvDir"]
        })
        
    except Exception as e:
        logger.exception(f"Error finding matches: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

def get_user_data(username: str) -> Dict[str, Any]:
    """
    Get or create user data for the specified username.
    
    Args:
        username (str): Username to get data for
        
    Returns:
        dict: User data dictionary
    """
    global user_data
    
    if username not in user_data:
        # Create new user data with default status
        user_data[username] = {
            "status": {"running": False, "message": "Ready", "percent": 0},
            "merger": None,
            "thread": None,
            "api_key": uuid.uuid4().hex  # Generate unique API key
        }
        
        logger.info(f"Created new user data for '{username}'")
    
    return user_data[username]

def get_username_from_request() -> str:
    """
    Extract username from request parameters, session, or default.
    
    Returns:
        str: Username
    """
    # Check for username in query parameters first
    username = request.args.get('user')
    
    # Check in form/JSON data if not in query parameters
    if not username and request.method == 'POST':
        if request.is_json:
            username = request.json.get('username')
        else:
            username = request.form.get('username')
    
    # Check session if not in request data
    if not username and 'username' in session:
        username = session['username']
    
    # Use default if not found
    if not username:
        username = 'default'
    
    # Store in session for future requests
    session['username'] = username
    
    return username

def check_api_key(request_data) -> tuple:
    """
    Check if the API key is valid for the given request.
    
    Args:
        request_data (dict): Request data containing API key
        
    Returns:
        tuple: (is_valid, username)
    """
    api_key = None
    
    # Get API key from request data
    if isinstance(request_data, dict):
        api_key = request_data.get('api_key')
    
    # If no API key provided, return invalid
    if not api_key:
        return False, None
    
    # Check if API key belongs to any user
    for username, data in user_data.items():
        if data.get('api_key') == api_key:
            return True, username
    
    return False, None