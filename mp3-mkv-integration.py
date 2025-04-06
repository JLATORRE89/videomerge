#!/usr/bin/env python3
"""
ContentCreatorTools - MP3-MKV Merger Integration Example

This script demonstrates how to integrate the MP3-MKV Merger
as a module within the ContentCreatorTools application architecture.
It follows the structure outlined in the integration guide.
"""

import os
import sys
import logging
import json
import uuid
import time
import sqlite3
import hashlib
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, Blueprint, g
from flask_session import Session
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# Import MP3-MKV Merger core functionality
# In a real implementation, you would import from your actual package
# For this example, we'll simulate the imports
try:
    from mp3_mkv_merger.core import MediaMerger
    from mp3_mkv_merger.utils import check_ffmpeg_installed, get_default_directory
except ImportError:
    # Mock implementation for demonstration purposes
    class MediaMerger:
        def __init__(self, mp3_dir, mkv_dir, out_dir, **kwargs):
            self.mp3_dir = mp3_dir
            self.mkv_dir = mkv_dir
            self.out_dir = out_dir
            self.kwargs = kwargs
            self.progress_callback = None
            self.stop_requested = False
        
        def set_progress_callback(self, callback):
            self.progress_callback = callback
        
        def process_all(self):
            if self.progress_callback:
                self.progress_callback("Starting processing...", 0)
                time.sleep(1)
                self.progress_callback("Processing files...", 50)
                time.sleep(2)
                self.progress_callback("Completed", 100)
            return True
        
        def stop(self):
            self.stop_requested = True
        
        def find_matching_files(self):
            return [
                ("C:\\sample\\audio1.mp3", "C:\\sample\\video1.mkv", "C:\\sample\\output\\video1_merged.mp4"),
                ("C:\\sample\\audio2.mp3", "C:\\sample\\video2.mkv", "C:\\sample\\output\\video2_merged.mp4")
            ]
    
    def check_ffmpeg_installed():
        return True
    
    def get_default_directory():
        return os.path.expanduser("~/Videos")

# =============================================================================
# Database Setup
# =============================================================================

def get_db():
    """Get a database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect('contentcreatortools.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database schema"""
    db = get_db()
    
    # Create users table
    db.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        api_key TEXT UNIQUE,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create user preferences table
    db.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        default_mp3_dir TEXT,
        default_mkv_dir TEXT,
        default_output_dir TEXT,
        replace_audio INTEGER DEFAULT 0,
        keep_original INTEGER DEFAULT 1,
        normalize_audio INTEGER DEFAULT 0,
        audio_codec TEXT DEFAULT 'aac',
        video_codec TEXT DEFAULT 'copy',
        output_format TEXT DEFAULT 'mp4',
        social_media INTEGER DEFAULT 0,
        social_width INTEGER DEFAULT 1080,
        social_height INTEGER DEFAULT 1080,
        social_format TEXT DEFAULT 'mp4',
        max_concurrent_jobs INTEGER DEFAULT 2,
        theme TEXT DEFAULT 'light',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Create user activity table
    db.execute('''
    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        activity_type TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Create jobs table
    db.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        mp3_dir TEXT NOT NULL,
        mkv_dir TEXT NOT NULL,
        out_dir TEXT NOT NULL,
        status TEXT NOT NULL,
        progress INTEGER DEFAULT 0,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    db.commit()

# User functions
def get_user_by_api_key(api_key):
    """Get a user by API key"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE api_key = ?', (api_key,)).fetchone()
    return user

def get_user_by_username(username):
    """Get a user by username"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    return user

def get_user_by_id(user_id):
    """Get a user by ID"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return user

def create_user(username, password, email, is_admin=0):
    """Create a new user"""
    db = get_db()
    try:
        api_key = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        db.execute(
            'INSERT INTO users (username, password, email, api_key, is_admin) VALUES (?, ?, ?, ?, ?)',
            (username, password_hash, email, api_key, is_admin)
        )
        db.commit()
        
        # Create default preferences
        user_id = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()[0]
        db.execute(
            'INSERT INTO user_preferences (user_id) VALUES (?)',
            (user_id,)
        )
        db.commit()
        
        return True
    except sqlite3.IntegrityError:
        return False

# Preferences functions
def get_user_preferences(user_id):
    """Get user preferences"""
    db = get_db()
    prefs = db.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,)).fetchone()
    
    if prefs is None:
        # Create default preferences if they don't exist
        db.execute('INSERT INTO user_preferences (user_id) VALUES (?)', (user_id,))
        db.commit()
        prefs = db.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,)).fetchone()
    
    return dict(prefs)

def update_user_preferences(user_id, preferences):
    """Update user preferences"""
    db = get_db()
    
    # Build the SQL update statement based on provided preferences
    sql_parts = []
    values = []
    
    for key, value in preferences.items():
        if key in ['user_id', 'id']:
            continue
        sql_parts.append(f"{key} = ?")
        values.append(value)
    
    values.append(user_id)
    
    if sql_parts:
        sql = f"UPDATE user_preferences SET {', '.join(sql_parts)} WHERE user_id = ?"
        db.execute(sql, tuple(values))
        db.commit()
        return True
    
    return False

# Activity functions
def log_activity(user_id, activity_type, details=None):
    """Log user activity"""
    db = get_db()
    db.execute(
        'INSERT INTO user_activity (user_id, activity_type, details) VALUES (?, ?, ?)',
        (user_id, activity_type, json.dumps(details) if details else None)
    )
    db.commit()

def get_user_activity(user_id, limit=50):
    """Get user activity history"""
    db = get_db()
    activities = db.execute(
        'SELECT * FROM user_activity WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    
    result = []
    for activity in activities:
        act_dict = dict(activity)
        # Parse the details if they exist
        if act_dict['details']:
            act_dict['details'] = json.loads(act_dict['details'])
        result.append(act_dict)
    
    return result

# Job functions
def create_job(user_id, mp3_dir, mkv_dir, out_dir):
    """Create a new job"""
    db = get_db()
    db.execute(
        'INSERT INTO jobs (user_id, mp3_dir, mkv_dir, out_dir, status) VALUES (?, ?, ?, ?, ?)',
        (user_id, mp3_dir, mkv_dir, out_dir, 'pending')
    )
    db.commit()
    return db.execute('SELECT last_insert_rowid()').fetchone()[0]

def update_job_status(job_id, status, progress=None, message=None):
    """Update job status"""
    db = get_db()
    updates = ['status = ?']
    values = [status]
    
    if progress is not None:
        updates.append('progress = ?')
        values.append(progress)
    
    if message is not None:
        updates.append('message = ?')
        values.append(message)
    
    if status in ['completed', 'failed']:
        updates.append('completed_at = CURRENT_TIMESTAMP')
    
    values.append(job_id)
    
    db.execute(
        f'UPDATE jobs SET {", ".join(updates)} WHERE id = ?',
        tuple(values)
    )
    db.commit()

def get_job(job_id):
    """Get a job by ID"""
    db = get_db()
    job = db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    return dict(job) if job else None

def get_user_jobs(user_id, limit=20):
    """Get jobs for a user"""
    db = get_db()
    jobs = db.execute(
        'SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    return [dict(job) for job in jobs]

def get_active_job_count(user_id):
    """Get count of active jobs for a user"""
    db = get_db()
    count = db.execute(
        'SELECT COUNT(*) FROM jobs WHERE user_id = ? AND status IN ("pending", "running")',
        (user_id,)
    ).fetchone()[0]
    return count

# =============================================================================
# Utility Modules
# =============================================================================

class RateLimiter:
    """Simple rate limiter for API requests"""
    def __init__(self, limit=60, window=60):
        self.limit = limit  # Max requests
        self.window = window  # Time window in seconds
        self.request_history = {}  # {ip: [(timestamp, endpoint), ...]}
    
    def is_rate_limited(self, ip, endpoint):
        now = time.time()
        
        if ip not in self.request_history:
            self.request_history[ip] = []
        
        # Remove old requests
        self.request_history[ip] = [
            req for req in self.request_history[ip]
            if now - req[0] < self.window
        ]
        
        # Check if limit is reached
        if len(self.request_history[ip]) >= self.limit:
            return True
        
        # Add current request
        self.request_history[ip].append((now, endpoint))
        return False

class JobLimiter:
    """Job concurrency limiter"""
    def __init__(self, db_func):
        self.get_active_job_count = db_func
    
    def can_create_job(self, user_id):
        """Check if user can create more jobs"""
        db = get_db()
        max_jobs = db.execute(
            'SELECT max_concurrent_jobs FROM user_preferences WHERE user_id = ?',
            (user_id,)
        ).fetchone()[0]
        
        active_jobs = self.get_active_job_count(user_id)
        return active_jobs < max_jobs

# =============================================================================
# Job Processing System
# =============================================================================

# Dictionary to store running jobs
# Format: {job_id: {"merger": MediaMerger, "thread": Thread}}
active_jobs = {}

def process_job(job_id, user_id):
    """Process a job in a separate thread"""
    global active_jobs
    
    try:
        # Get job details
        job = get_job(job_id)
        if not job:
            return
        
        # Update job status
        update_job_status(job_id, 'running', 0, 'Starting job...')
        
        # Get user preferences for default settings
        prefs = get_user_preferences(user_id)
        
        # Create merger with job and preference settings
        merger = MediaMerger(
            mp3_dir=job['mp3_dir'],
            mkv_dir=job['mkv_dir'],
            out_dir=job['out_dir'],
            replace_audio=prefs['replace_audio'] == 1,
            keep_original=prefs['keep_original'] == 1,
            normalize_audio=prefs['normalize_audio'] == 1,
            audio_codec=prefs['audio_codec'],
            video_codec=prefs['video_codec'] if prefs['video_codec'] != 'copy' else None,
            social_media=prefs['social_media'] == 1,
            social_width=prefs['social_width'],
            social_height=prefs['social_height'],
            social_format=prefs['social_format'],
            output_format=prefs['output_format']
        )
        
        # Setup progress callback
        def progress_callback(message, percent):
            update_job_status(job_id, 'running', percent, message)
        
        merger.set_progress_callback(progress_callback)
        
        # Store merger in active jobs
        active_jobs[job_id] = {
            "merger": merger,
            "thread": threading.current_thread()
        }
        
        # Process files
        success = merger.process_all()
        
        # Update final status
        if success:
            update_job_status(job_id, 'completed', 100, 'Job completed successfully')
            log_activity(user_id, 'job_completed', {
                'job_id': job_id,
                'mp3_dir': job['mp3_dir'],
                'mkv_dir': job['mkv_dir'],
                'out_dir': job['out_dir']
            })
        else:
            update_job_status(job_id, 'failed', -1, 'Job failed')
            log_activity(user_id, 'job_failed', {
                'job_id': job_id,
                'mp3_dir': job['mp3_dir'],
                'mkv_dir': job['mkv_dir'],
                'out_dir': job['out_dir']
            })
    except Exception as e:
        # Handle exceptions
        update_job_status(job_id, 'failed', -1, f'Error: {str(e)}')
        log_activity(user_id, 'job_error', {
            'job_id': job_id,
            'error': str(e)
        })
    finally:
        # Remove from active jobs
        if job_id in active_jobs:
            del active_jobs[job_id]

def start_job(user_id, mp3_dir, mkv_dir, out_dir):
    """Start a new job"""
    # Check if user can create more jobs
    job_limiter = JobLimiter(get_active_job_count)
    if not job_limiter.can_create_job(user_id):
        return None, "You've reached your concurrent job limit"
    
    # Create job in database
    job_id = create_job(user_id, mp3_dir, mkv_dir, out_dir)
    
    # Log activity
    log_activity(user_id, 'job_created', {
        'job_id': job_id,
        'mp3_dir': mp3_dir,
        'mkv_dir': mkv_dir,
        'out_dir': out_dir
    })
    
    # Start processing thread
    thread = threading.Thread(target=process_job, args=(job_id, user_id))
    thread.daemon = True
    thread.start()
    
    return job_id, None

def stop_job(job_id):
    """Stop a running job"""
    global active_jobs
    
    if job_id in active_jobs:
        active_jobs[job_id]["merger"].stop()
        update_job_status(job_id, 'stopped', -1, 'Job stopped by user')
        return True
    
    return False

# =============================================================================
# Flask Application & Blueprints
# =============================================================================

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
Session(app)

# Initialize rate limiter
rate_limiter = RateLimiter(limit=60, window=60)  # 60 requests per minute

# Register teardown function
app.teardown_appcontext(close_db)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = get_user_by_id(session['user_id'])
        if not user or user['is_admin'] != 1:
            return jsonify({
        "success": True,
        "job": {
            "id": job["id"],
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"],
            "mp3_dir": job["mp3_dir"],
            "mkv_dir": job["mkv_dir"],
            "out_dir": job["out_dir"],
            "created_at": job["created_at"],
            "completed_at": job["completed_at"]
        }
    })

@api_bp.route('/jobs', methods=['GET'])
@api_auth_required
@rate_limit
def api_jobs():
    """API endpoint to get user's jobs."""
    user_id = g.user['id']
    limit = request.args.get('limit', 20, type=int)
    
    jobs = get_user_jobs(user_id, limit)
    
    return jsonify({
        "success": True,
        "jobs": jobs,
        "total": len(jobs)
    })

@api_bp.route('/stop/<int:job_id>', methods=['POST'])
@api_auth_required
@rate_limit
def api_stop(job_id):
    """API endpoint to stop a job."""
    user_id = g.user['id']
    job = get_job(job_id)
    
    if not job:
        return jsonify({
            "success": False,
            "message": f"Job {job_id} not found"
        }), 404
    
    # Check if user owns the job
    if job['user_id'] != user_id:
        # Allow admins to stop any job
        if g.user['is_admin'] != 1:
            return jsonify({
                "success": False,
                "message": "Unauthorized to stop this job"
            }), 403
    
    # Stop the job
    success = stop_job(job_id)
    
    if success:
        log_activity(user_id, 'api_stop_job', {'job_id': job_id})
        return jsonify({
            "success": True,
            "message": "Job stopped successfully"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Job is not running or cannot be stopped"
        }), 400

@api_bp.route('/find_matches', methods=['POST'])
@api_auth_required
@rate_limit
def api_find_matches():
    """API endpoint to find matching files."""
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    
    user_id = g.user['id']
    data = request.json
    
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
        
        # Log API activity
        log_activity(user_id, 'api_find_matches', {
            'mp3_dir': data["mp3Dir"],
            'mkv_dir': data["mkvDir"],
            'matches_found': len(match_list)
        })
        
        return jsonify({
            "success": True,
            "matches": match_list,
            "total_matches": len(match_list),
            "mp3_dir": data["mp3Dir"],
            "mkv_dir": data["mkvDir"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/preferences', methods=['GET'])
@api_auth_required
@rate_limit
def api_get_preferences():
    """API endpoint to get user preferences."""
    user_id = g.user['id']
    prefs = get_user_preferences(user_id)
    
    return jsonify({
        "success": True,
        "preferences": prefs
    })

@api_bp.route('/preferences', methods=['POST'])
@api_auth_required
@rate_limit
def api_update_preferences():
    """API endpoint to update user preferences."""
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    
    user_id = g.user['id']
    data = request.json
    
    # Remove API key from data to prevent updating it
    if 'api_key' in data:
        del data['api_key']
    
    # Convert keys from camelCase to snake_case
    prefs = {}
    for key, value in data.items():
        # Skip non-preference fields
        if key in ['api_key', 'username', 'email', 'password']:
            continue
            
        # Convert camelCase to snake_case
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        
        # Convert boolean values to integers for SQLite
        if isinstance(value, bool):
            value = 1 if value else 0
            
        prefs[snake_key] = value
    
    # Update preferences
    success = update_user_preferences(user_id, prefs)
    
    if success:
        log_activity(user_id, 'api_update_preferences')
        return jsonify({
            "success": True,
            "message": "Preferences updated successfully"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Failed to update preferences"
        }), 400

# =============================================================================
# Register Blueprints
# =============================================================================

def register_blueprints(app):
    """Register all blueprints with the app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(preferences_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

# =============================================================================
# Main Application
# =============================================================================

def create_app():
    """Create and configure the application"""
    # Initialize database
    with app.app_context():
        init_db()
        
        # Create admin user if it doesn't exist
        admin = get_user_by_username('admin')
        if not admin:
            create_user('admin', 'adminpassword', 'admin@example.com', is_admin=1)
    
    # Register blueprints
    register_blueprints(app)
    
    return app

# Run the application
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting MP3-MKV Merger Integration on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)"error": "Unauthorized"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# API authentication decorator
def api_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = None
        
        # Get API key from request
        if request.method == 'GET':
            api_key = request.args.get('api_key')
        else:
            if request.is_json:
                api_key = request.json.get('api_key')
            else:
                api_key = request.form.get('api_key')
        
        if not api_key:
            return jsonify({"success": False, "message": "API key is required"}), 401
        
        # Get user from API key
        user = get_user_by_api_key(api_key)
        if not user:
            return jsonify({"success": False, "message": "Invalid API key"}), 401
        
        # Add user to request
        g.user = user
        return f(*args, **kwargs)
    
    return decorated_function

# Rate limiting decorator
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        endpoint = request.endpoint
        
        if rate_limiter.is_rate_limited(ip, endpoint):
            return jsonify({"success": False, "message": "Rate limit exceeded"}), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

# =============================================================================
# Route Blueprints
# =============================================================================

# Auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            log_activity(user['id'], 'login')
            return redirect(url_for('dashboard.index'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if create_user(username, password, email):
            return redirect(url_for('auth.login'))
        
        return render_template('register.html', error='Username or email already exists')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        log_activity(session['user_id'], 'logout')
        session.clear()
    return redirect(url_for('auth.login'))

# Dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    jobs = get_user_jobs(user_id, limit=10)
    
    return render_template('dashboard.html', 
                         jobs=jobs, 
                         username=session['username'])

@dashboard_bp.route('/jobs')
@login_required
def jobs():
    user_id = session['user_id']
    jobs = get_user_jobs(user_id)
    
    return render_template('jobs.html', 
                         jobs=jobs, 
                         username=session['username'])

@dashboard_bp.route('/job/<int:job_id>')
@login_required
def job_details(job_id):
    user_id = session['user_id']
    job = get_job(job_id)
    
    if not job or job['user_id'] != user_id:
        return redirect(url_for('dashboard.jobs'))
    
    return render_template('job_details.html', 
                         job=job, 
                         username=session['username'])

# Preferences blueprint
preferences_bp = Blueprint('preferences', __name__, url_prefix='/preferences')

@preferences_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Update preferences
        prefs = {
            'default_mp3_dir': request.form.get('default_mp3_dir'),
            'default_mkv_dir': request.form.get('default_mkv_dir'),
            'default_output_dir': request.form.get('default_output_dir'),
            'replace_audio': 1 if request.form.get('replace_audio') else 0,
            'keep_original': 1 if request.form.get('keep_original') else 0,
            'normalize_audio': 1 if request.form.get('normalize_audio') else 0,
            'audio_codec': request.form.get('audio_codec'),
            'video_codec': request.form.get('video_codec'),
            'output_format': request.form.get('output_format'),
            'social_media': 1 if request.form.get('social_media') else 0,
            'social_width': int(request.form.get('social_width', 1080)),
            'social_height': int(request.form.get('social_height', 1080)),
            'social_format': request.form.get('social_format'),
            'theme': request.form.get('theme'),
            'max_concurrent_jobs': int(request.form.get('max_concurrent_jobs', 2))
        }
        
        update_user_preferences(user_id, prefs)
        log_activity(user_id, 'update_preferences')
        
        return redirect(url_for('preferences.index'))
    
    # Get preferences
    prefs = get_user_preferences(user_id)
    user = get_user_by_id(user_id)
    
    return render_template('preferences.html', 
                         prefs=prefs, 
                         user=user, 
                         username=session['username'])

@preferences_bp.route('/api-key', methods=['POST'])
@login_required
def reset_api_key():
    user_id = session['user_id']
    db = get_db()
    
    new_api_key = str(uuid.uuid4())
    db.execute('UPDATE users SET api_key = ? WHERE id = ?', (new_api_key, user_id))
    db.commit()
    
    log_activity(user_id, 'reset_api_key')
    
    return redirect(url_for('preferences.index'))

# Activity blueprint
activity_bp = Blueprint('activity', __name__, url_prefix='/activity')

@activity_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    activities = get_user_activity(user_id)
    
    return render_template('activity.html', 
                         activities=activities, 
                         username=session['username'])

# Admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    db = get_db()
    
    stats = {
        'total_users': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_jobs': db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
        'active_jobs': db.execute('SELECT COUNT(*) FROM jobs WHERE status IN ("pending", "running")').fetchone()[0],
        'recent_activities': db.execute(
            '''SELECT a.*, u.username FROM user_activity a
               JOIN users u ON a.user_id = u.id
               ORDER BY a.created_at DESC LIMIT 10'''
        ).fetchall()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@admin_required
def users():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/jobs')
@admin_required
def jobs():
    db = get_db()
    jobs = db.execute(
        '''SELECT j.*, u.username FROM jobs j
           JOIN users u ON j.user_id = u.id
           ORDER BY j.created_at DESC LIMIT 100'''
    ).fetchall()
    
    return render_template('admin/jobs.html', jobs=jobs)

@admin_bp.route('/stop-job/<int:job_id>', methods=['POST'])
@admin_required
def stop_job_admin(job_id):
    if stop_job(job_id):
        job = get_job(job_id)
        log_activity(session['user_id'], 'admin_stop_job', {'job_id': job_id, 'user_id': job['user_id']})
    
    return redirect(url_for('admin.jobs'))

# =============================================================================
# API Routes
# =============================================================================

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/start', methods=['POST'])
@api_auth_required
@rate_limit
def api_start():
    """API endpoint to start processing."""
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    
    user_id = g.user['id']
    data = request.json
    
    # Validate required parameters
    required_params = ['mp3Dir', 'mkvDir', 'outDir']
    for param in required_params:
        if param not in data:
            return jsonify({
                "success": False, 
                "message": f"Missing required parameter: {param}"
            }), 400
    
    # Check if ffmpeg is installed
    if not check_ffmpeg_installed():
        return jsonify({
            "success": False, 
            "message": "ffmpeg not found. Please install ffmpeg."
        }), 500
    
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
    
    # Create output directory if it doesn't exist
    os.makedirs(data["outDir"], exist_ok=True)
    
    # Start job
    job_id, error = start_job(user_id, data["mp3Dir"], data["mkvDir"], data["outDir"])
    
    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 429
    
    # Log API activity
    log_activity(user_id, 'api_start_job', {
        'job_id': job_id,
        'mp3_dir': data["mp3Dir"],
        'mkv_dir': data["mkvDir"],
        'out_dir': data["outDir"]
    })
    
    return jsonify({
        "success": True,
        "message": "Job started successfully",
        "job_id": job_id
    })

@api_bp.route('/status/<int:job_id>', methods=['GET'])
@api_auth_required
@rate_limit
def api_status(job_id):
    """API endpoint to get job status."""
    user_id = g.user['id']
    job = get_job(job_id)
    
    if not job:
        return jsonify({
            "success": False,
            "message": f"Job {job_id} not found"
        }), 404
    
    # Check if user owns the job
    if job['user_id'] != user_id:
        # Allow admins to view any job
        if g.user['is_admin'] != 1:
            return jsonify({
                "success": False,
                "message": "Unauthorized to access this job"
            }), 403
    
    return jsonify({