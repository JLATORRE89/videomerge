
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
