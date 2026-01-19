"""
PlaylistPro Web Server

A Flask application for managing and sorting YouTube playlists.
Supports SQLite (default) and MariaDB/MySQL databases.
"""

import os
import uuid
import threading
from functools import wraps
from flask import Flask, request, render_template, flash, jsonify, Response, redirect, url_for, session
from datetime import datetime as dt
from typing import Callable, Optional, Generator

import pywertube as pt
from pywertube import config
from pywertube.dashboard_stats import calculate_turnaround_metrics


# =============================================================================
# Authentication
# =============================================================================

def admin_required(f):
    """Decorator to protect admin routes with password authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If no password configured, admin is open (dev mode)
        if not config.admin_auth_required:
            return f(*args, **kwargs)

        # Check if user is authenticated
        if not session.get('admin_authenticated'):
            # For API endpoints, return 401
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized", "message": "Admin authentication required"}), 401
            # For pages, redirect to login
            return redirect(url_for('login', next=request.path))

        return f(*args, **kwargs)
    return decorated_function

# In-memory job storage (thread-safe)
_sort_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()

# Sorting keywords
NUMBERED_SERIALIZED_KEYWORDS = ['series', 'part', 'finale', 'episode', 'ep', '#', 'chapter']
SERIALIZED_KEYWORDS = []

# Set up logger
if os.environ.get('TERM_PROGRAM') == 'vscode':
    logger = pt.initLogger(__file__, debug=True, verbose=False)
else:
    logger = pt.initLogger(__file__, debug=config.debug_mode, verbose=config.verbose_debug)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.secret_key or os.urandom(24)

# Configure database
database_url = config.database.get_url()
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if config.database.is_sqlite:
    logger.info("Development mode: Using SQLite database")
else:
    # Log URL without password for security
    safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
    logger.info(f"Production mode: Using database at {safe_url}")

# Initialize database with Flask app
pt.init_db(app)
logger.info("Database initialized!")


@app.context_processor
def inject_config():
    """Make config available in all templates."""
    return {'config': config}


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        sort()
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    # If auth not required, redirect to admin
    if not config.admin_auth_required:
        return redirect(url_for('admin'))

    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == config.admin_password:
            session['admin_authenticated'] = True
            next_url = request.args.get('next', url_for('admin'))
            return redirect(next_url)
        else:
            error = 'Invalid password'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Log out of admin session."""
    session.pop('admin_authenticated', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """Dashboard with stats and visualizations."""
    # Get recent stats from database
    stats_query = pt.WatchLaterStat.query.order_by(pt.WatchLaterStat.Date.desc()).limit(30).all()

    # Convert to dicts for JSON serialization in template
    stats = [{
        'Date': s.Date,
        'Length': s.Length,
        'TotalDuration': s.TotalDuration,
        'AverageDuration': s.AverageDuration,
        'MedianDuration': s.MedianDuration,
        'StdvDuration': s.StdvDuration,
        'NumUniqueCreators': s.NumUniqueCreators
    } for s in stats_query]

    # Get creator stats for the most recent date (all creators for pie chart)
    latest_date = pt.WatchLaterStat.query.order_by(pt.WatchLaterStat.Date.desc()).first()
    creator_stats_query = []
    if latest_date:
        creator_stats_query = pt.WatchLaterCreatorStat.query.filter_by(
            date=latest_date.Date
        ).order_by(pt.WatchLaterCreatorStat.Frequency.desc()).all()

    # Build creators map for looking up creator names by ID
    creators = pt.Creator.query.all()
    creators_map = {c.id: c for c in creators}

    # Convert creator_stats to dicts with creator names for JSON serialization
    creator_stats = [{
        'CreatorID': cs.CreatorID,
        'CreatorName': creators_map.get(cs.CreatorID).creators if creators_map.get(cs.CreatorID) else 'Unknown',
        'Frequency': cs.Frequency,
        'Duration': cs.Duration,
        'FrequencyPercentage': cs.FrequencyPercentage,
        'DurationPercentage': cs.DurationPercentage
    } for cs in creator_stats_query]

    # Calculate turnaround metrics by comparing historical snapshots
    turnaround_stats = calculate_turnaround_metrics(creators_map)

    return render_template('dashboard.html', stats=stats, creator_stats=creator_stats,
                          creators_map=creators_map, turnaround_stats=turnaround_stats)


@app.route('/admin')
@admin_required
def admin():
    """Admin page for editing configuration tables."""
    creators = pt.Creator.query.order_by(pt.Creator.priorityScore.desc()).all()
    keyphrases = pt.Keyphrase.query.order_by(pt.Keyphrase.score.desc()).all()
    sequential = pt.SequentialCreator.query.all()

    return render_template('admin.html',
                          creators=creators,
                          keyphrases=keyphrases,
                          sequential=sequential)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    webhookLog = logger.bind()
    pt.setLogger(webhookLog)
    webhookLog.debug("webhooklog set as logger!")

    if request.method == 'POST':
        pt.pickleSomething(request.data, "request_" + dt.now().strftime("%Y%m%d%H%M%S"))
        return {"message": "Accepted"}, 202
    else:
        return request.args.get('hub.challenge')


@app.route('/subs', methods=['GET'])
def subscribe():
    subLog = logger.bind()
    pt.setLogger(subLog)
    subLog.info("subLogger set as logger!")

    youtube = pt.get_youtube_client(config.oauth_port, config.oauth.to_client_secret_dict())
    subLog.info("YouTube client obtained!")

    subs = pt.getSubscriptions(youtube, mine=True)
    pt.storeSubscripton(subs, youtube)
    pt.subscribeCreators()

    return "subscribers updated"


class SortError(Exception):
    """Custom exception for sort operation failures."""
    pass


def _perform_sort(on_progress: Optional[Callable[[str, int], None]] = None):
    """
    Core sorting logic - orchestrates the playlist sorting process.

    Args:
        on_progress: Optional callback(step_message, percent_complete) for progress updates

    Returns:
        dict: Result with 'success', 'message', 'video_count', 'moves', 'quota_used'
    """
    def progress(msg: str, pct: int):
        if on_progress:
            on_progress(msg, pct)

    sortLog = logger.bind()
    pt.setLogger(sortLog)
    sortLog.info("Starting playlist sort operation")
    progress("Starting sort operation...", 0)

    quota = 0
    inDB = False

    # Step 1: Load data from database
    progress("Loading configuration from database...", 10)
    try:
        creatorDictionary, keywordDictionary, videoFollowUpList, sequentialCreatorsDict, quota, inDB = initWatchLater(sortLog)
    except Exception as e:
        sortLog.error(f"Failed to load data from database: {e}", exc_info=True)
        return {"success": False, "message": "Failed to load data from database", "error": str(e)}

    # Step 2: Get YouTube credentials and watch later list
    progress("Connecting to YouTube API...", 20)
    try:
        youtube = getYoutubeObj(sortLog)
        progress("Fetching playlist from YouTube...", 30)
        youtubeWatchLater, requestOps = pt.getWatchLater(youtube, config.playlist_id, True)
        quota += requestOps
        sortLog.info(f"Watch later obtained. Quota used: {requestOps}, Total: {quota}")
    except Exception as e:
        sortLog.error(f"Failed to get YouTube data: {e}", exc_info=True)
        _save_quota(sortLog, inDB, quota)
        return {"success": False, "message": "Failed to connect to YouTube API", "error": str(e)}

    video_count = len(youtubeWatchLater)
    progress(f"Fetched {video_count} videos. Sorting...", 50)

    # Step 3: Sort the watch later list
    try:
        sortedWatchLater = pt.sortWatchLater(
            youtubeWatchLater,
            creatorDictionary,
            keywordDictionary,
            NUMBERED_SERIALIZED_KEYWORDS,
            SERIALIZED_KEYWORDS,
            videoFollowUpList,
            sequentialCreatorsDict
        )
        sortLog.info("Watch later list sorted successfully")
    except Exception as e:
        sortLog.error(f"Failed to sort watch later list: {e}", exc_info=True)
        _save_quota(sortLog, inDB, quota)
        return {"success": False, "message": "Sorting algorithm failed", "error": str(e)}

    # Step 4: Update playlist on YouTube
    progress("Updating playlist on YouTube...", 60)
    try:
        videoOps, youtubeWatchLater = pt.updatePlaylist(
            youtubeWatchLater,
            sortedWatchLater,
            youtube,
            config.playlist_id
        )
        quota += videoOps * 50
        sortLog.info(f"Playlist updated on YouTube. Operations: {videoOps}, Quota used: {videoOps * 50}, Total: {quota}")
        progress(f"Moved {videoOps} videos. Saving statistics...", 80)
    except Exception as e:
        sortLog.error(f"Failed to update YouTube playlist: {e}", exc_info=True)
        _save_quota(sortLog, inDB, quota)
        return {"success": False, "message": "Failed to update playlist on YouTube", "error": str(e)}

    # Step 5: Store statistics (non-critical - don't fail the whole operation)
    stats_saved = False
    youtubeWatchLater = pt.renumberWatchLater(youtubeWatchLater)
    try:
        pt.storeWatchLaterDB(youtubeWatchLater)
        datetime_str = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        pt.WatchLaterStats(youtubeWatchLater, datetime_str)
        quota += pt.WatchLaterCreatorStats(youtubeWatchLater, datetime_str, youtube)
        sortLog.info("Statistics stored in database")
        stats_saved = True
    except Exception as e:
        sortLog.warning(f"Failed to store statistics (non-critical): {e}", exc_info=True)

    # Save quota usage
    _save_quota(sortLog, inDB, quota)
    progress("Complete!", 100)

    return {
        "success": True,
        "message": "Playlist sorted successfully",
        "video_count": video_count,
        "moves": videoOps,
        "quota_used": quota,
        "stats_saved": stats_saved
    }


def sort():
    """Web form handler - calls core sort and uses flash for messaging."""
    if request.method != 'POST':
        return

    result = _perform_sort()

    if result["success"]:
        msg = f"Playlist sorted successfully! {result['moves']} moves, {result['video_count']} videos."
        if result.get("stats_saved"):
            msg += " Statistics saved."
        msg += f" Quota used: {result['quota_used']}"
        flash(msg)
    else:
        flash(f"Error: {result['message']}. Check logs for details.")


# =============================================================================
# API Endpoints - Background Job + Polling
# =============================================================================

def _run_sort_job(job_id: str):
    """Run sort in background thread, updating job status."""
    def update_progress(msg: str, pct: int):
        with _jobs_lock:
            if job_id in _sort_jobs:
                _sort_jobs[job_id]["step"] = msg
                _sort_jobs[job_id]["progress"] = pct

    with _jobs_lock:
        _sort_jobs[job_id]["status"] = "running"

    # Need app context for database operations in background thread
    with app.app_context():
        result = _perform_sort(on_progress=update_progress)

    with _jobs_lock:
        _sort_jobs[job_id]["status"] = "complete" if result["success"] else "failed"
        _sort_jobs[job_id]["result"] = result


@app.route('/api/sort', methods=['POST'])
def api_sort_start():
    """Start a background sort job. Returns job_id for polling."""
    job_id = str(uuid.uuid4())[:8]

    with _jobs_lock:
        _sort_jobs[job_id] = {
            "status": "pending",
            "step": "Queued...",
            "progress": 0,
            "result": None,
            "created": dt.now().isoformat()
        }

    thread = threading.Thread(target=_run_sort_job, args=(job_id,), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id, "status": "pending"}), 202


@app.route('/api/sort/status/<job_id>', methods=['GET'])
def api_sort_status(job_id: str):
    """Check status of a sort job."""
    with _jobs_lock:
        job = _sort_jobs.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    response = {
        "job_id": job_id,
        "status": job["status"],
        "step": job["step"],
        "progress": job["progress"]
    }

    if job["status"] in ("complete", "failed"):
        response["result"] = job["result"]

    return jsonify(response)


@app.route('/api/sort', methods=['GET'])
def api_sort_sync():
    """Synchronous sort - blocks until complete. For simple use cases."""
    result = _perform_sort()
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code


# =============================================================================
# SSE Endpoint - Real-time Progress for Web UI
# =============================================================================

def _generate_sort_events() -> Generator[str, None, None]:
    """Generator that yields SSE events during sort operation."""
    import queue
    import json

    progress_queue: queue.Queue = queue.Queue()

    def on_progress(msg: str, pct: int):
        progress_queue.put({"event": "progress", "step": msg, "progress": pct})

    def run_sort():
        with app.app_context():
            result = _perform_sort(on_progress=on_progress)
            progress_queue.put({"event": "complete", "result": result})

    thread = threading.Thread(target=run_sort, daemon=True)
    thread.start()

    # Yield events as they come in
    while True:
        try:
            data = progress_queue.get(timeout=120)  # 2 min timeout
            yield f"data: {json.dumps(data)}\n\n"

            if data.get("event") == "complete":
                break
        except queue.Empty:
            # Send keepalive
            yield f"data: {json.dumps({'event': 'keepalive'})}\n\n"


@app.route('/api/sort/stream', methods=['GET'])
def api_sort_stream():
    """SSE endpoint for real-time sort progress. For web UI."""
    return Response(
        _generate_sort_events(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )


# =============================================================================
# Admin API Endpoints
# =============================================================================

@app.route('/api/admin/creators', methods=['POST'])
@admin_required
def api_add_creator():
    """Add a new creator."""
    data = request.get_json()
    try:
        creator = pt.Creator(
            creators=data['name'],
            priorityScore=data.get('score', 0)
        )
        pt.db.session.add(creator)
        pt.db.session.commit()
        return jsonify({"success": True, "id": creator.id})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/creators/<int:id>', methods=['PUT'])
@admin_required
def api_update_creator(id):
    """Update a creator's settings."""
    data = request.get_json()
    creator = pt.Creator.query.get_or_404(id)
    try:
        if 'score' in data:
            creator.priorityScore = data['score']
        if 'subscribed' in data:
            creator.subscribed = data['subscribed']
        if 'unconditional' in data:
            creator.unconditional = data['unconditional']
        pt.db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/creators/<int:id>', methods=['DELETE'])
@admin_required
def api_delete_creator(id):
    """Delete a creator."""
    creator = pt.Creator.query.get_or_404(id)
    try:
        pt.db.session.delete(creator)
        pt.db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/keyphrases', methods=['POST'])
@admin_required
def api_add_keyphrase():
    """Add a new keyphrase."""
    data = request.get_json()
    try:
        phrase = pt.Keyphrase(
            phrase=data['phrase'],
            score=data.get('score', 1)
        )
        pt.db.session.add(phrase)
        pt.db.session.commit()
        return jsonify({"success": True, "id": phrase.id})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/keyphrases/<int:id>', methods=['PUT'])
@admin_required
def api_update_keyphrase(id):
    """Update a keyphrase's score."""
    data = request.get_json()
    phrase = pt.Keyphrase.query.get_or_404(id)
    try:
        if 'score' in data:
            phrase.score = data['score']
        pt.db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/keyphrases/<int:id>', methods=['DELETE'])
@admin_required
def api_delete_keyphrase(id):
    """Delete a keyphrase."""
    phrase = pt.Keyphrase.query.get_or_404(id)
    try:
        pt.db.session.delete(phrase)
        pt.db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/sequential', methods=['POST'])
@admin_required
def api_add_sequential():
    """Add a sequential creator."""
    data = request.get_json()
    try:
        seq = pt.SequentialCreator(
            creatorId=data['creator_id'],
            DurationExpection=data.get('duration_exception', False)
        )
        pt.db.session.add(seq)
        pt.db.session.commit()
        return jsonify({"success": True, "id": seq.id})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/sequential/<int:id>', methods=['DELETE'])
@admin_required
def api_delete_sequential(id):
    """Remove a sequential creator."""
    seq = pt.SequentialCreator.query.get_or_404(id)
    try:
        pt.db.session.delete(seq)
        pt.db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/admin/sequential/<int:id>', methods=['PUT'])
@admin_required
def api_update_sequential(id):
    """Update a sequential creator's settings."""
    data = request.get_json()
    seq = pt.SequentialCreator.query.get_or_404(id)
    try:
        if 'duration_exception' in data:
            seq.DurationExpection = data['duration_exception']
        if 'threshold_mins' in data:
            seq.SpecialDurationThresholdMins = data['threshold_mins']
        pt.db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        pt.db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


def _save_quota(log, inDB, quota):
    """Helper to save quota usage, with error handling."""
    try:
        pt.setQuotaUsed(inDB, quota, config.project_id)
        log.info(f"Quota saved: {quota}")
    except Exception as e:
        log.warning(f"Failed to save quota (non-critical): {e}")


@app.route('/renew', methods=['GET'])
def reNewToken():
    if request.method == 'GET':
        flow = pt.getFlowObject(config.oauth.to_client_secret_dict())
        flow.run_local_server()
        flow.authorized_session()
        credentials = flow.credentials
        pt.saveCredentails(credentials)
    return 'renewed!'


def initWatchLater(log):
    """
    Initialize watch later data from database.

    Returns:
        tuple: (creatorDict, keywordDict, videoFollowUpList, sequentialCreatorsDict, quota, inDB)
    """
    log.info("Loading data from database...")

    # Get creators and their priority scores
    creatorDictionary = pt.get_creators_dict()
    log.info("Creators and their Priority Score obtained!")

    # Get keyphrases and their scores
    keywordDictionary = pt.get_keyphrases_dict()
    log.info("Keyphrase and their Priority Score obtained!")

    # Get follow-up video relationships
    videoFollowUpList = pt.get_order_videos_list()
    log.info("Follow up video data obtained!")

    # Get sequential creators
    sequentialCreatorsDict = pt.get_sequential_creators_dict()
    log.info("Sequential creators obtained!")

    # Get quota usage
    quota, inDB = pt.getQuotaUsed(config.project_id)
    log.info(f"Used Quota obtained! So far incurred: {quota}")

    return creatorDictionary, keywordDictionary, videoFollowUpList, sequentialCreatorsDict, quota, inDB


def getYoutubeObj(log):
    """Build and return a YouTube API client."""
    youtube = pt.get_youtube_client(config.oauth_port, config.oauth.to_client_secret_dict())
    log.info("YouTube client obtained!")
    return youtube


if __name__ == "__main__":
    app.run(host=config.host, port=config.port)
