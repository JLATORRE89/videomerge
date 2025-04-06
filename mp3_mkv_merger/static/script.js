
// JavaScript for MP3-MKV Merger web UI
document.addEventListener('DOMContentLoaded', function() {
    // Directory browse buttons
    document.querySelectorAll('.browse-button').forEach(function(button) {
        button.addEventListener('click', function() {
            const inputId = this.getAttribute('data-for');
            const input = document.getElementById(inputId);
            
            // We can't browse directly from a web app
            alert('In a web browser, we cannot directly browse your filesystem. Please manually enter the full path.');
            
            // For demonstration/testing, suggest some example paths
            if (inputId === 'mp3Dir') {
                input.value = input.value || 'C:\\Users\\YourName\\Music';
            } else if (inputId === 'mkvDir') {
                input.value = input.value || 'C:\\Users\\YourName\\Videos';
            } else if (inputId === 'outDir') {
                input.value = input.value || 'C:\\Users\\YourName\\Videos\\Output';
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
            keepOriginal: form.keepOriginal.checked
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
                    let message = 'Found ' + data.matches.length + ' matching pairs:\n\n';
                    data.matches.forEach((match, index) => {
                        message += (index + 1) + '. ' + match.mp3 + ' -> ' + match.mkv + '\n';
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
