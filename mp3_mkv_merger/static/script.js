
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
                input.value = input.value || 'C:\Users\Music\MP3';
            } else if (inputId === 'mkvDir') {
                input.value = input.value || 'C:\Users\Videos\MKV';
            } else if (inputId === 'outDir') {
                input.value = input.value || 'C:\Users\Videos\Output';
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
            socialFormat: form.socialFormat ? form.socialFormat.value : 'mp4'
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
        fetch('/stop', {
            method: 'POST'
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
                    let message = 'Found ' + data.matches.length + ' matching pairs:

';
                    data.matches.forEach((match, index) => {
                        message += (index + 1) + '. ' + match.mp3 + ' ⟹ ' + match.mkv + '
';
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
