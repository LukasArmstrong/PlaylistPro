"""
PlaylistPro Web Server

A Flask application for managing and sorting YouTube playlists.
Supports SQLite (default) and MariaDB/MySQL databases.
"""

import os
from flask import Flask, request, render_template, flash
from datetime import datetime as dt

import pywertube as pt
from pywertube import config

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


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        sort()
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/sorting_editor')
def sortEditor():
    return render_template('SortEditor.html')


@app.route('/data_visualization')
def dataVis():
    return render_template('dataVis.html')


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


def sort():
    """Main sorting function - orchestrates the playlist sorting process."""
    if request.method != 'POST':
        return

    sortLog = logger.bind()
    pt.setLogger(sortLog)
    sortLog.info("Starting playlist sort operation")

    messages = []
    quota = 0
    inDB = False

    # Step 1: Load data from database
    try:
        creatorDictionary, keywordDictionary, videoFollowUpList, sequentialCreatorsDict, quota, inDB = initWatchLater(sortLog)
    except Exception as e:
        sortLog.error(f"Failed to load data from database: {e}", exc_info=True)
        flash("Error: Could not load data from database. Check logs for details.")
        return

    # Step 2: Get YouTube credentials and watch later list
    try:
        youtube = getYoutubeObj(sortLog)
        youtubeWatchLater, requestOps = pt.getWatchLater(youtube, config.playlist_id, True)
        quota += requestOps
        sortLog.info(f"Watch later obtained. Quota used: {requestOps}, Total: {quota}")
    except Exception as e:
        sortLog.error(f"Failed to get YouTube data: {e}", exc_info=True)
        _save_quota(sortLog, inDB, quota)
        flash("Error: Could not connect to YouTube API. Check credentials and try again.")
        return

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
        flash("Error: Sorting algorithm failed. Check logs for details.")
        return

    # Step 4: Update playlist on YouTube
    try:
        videoOps, youtubeWatchLater = pt.updatePlaylist(
            youtubeWatchLater,
            sortedWatchLater,
            youtube,
            config.playlist_id
        )
        quota += videoOps * 50
        sortLog.info(f"Playlist updated on YouTube. Operations: {videoOps}, Quota used: {videoOps * 50}, Total: {quota}")
        messages.append("Playlist sorted successfully!")
    except Exception as e:
        sortLog.error(f"Failed to update YouTube playlist: {e}", exc_info=True)
        _save_quota(sortLog, inDB, quota)
        flash("Error: Could not update playlist on YouTube. Check logs for details.")
        return

    # Step 5: Store statistics (non-critical - don't fail the whole operation)
    youtubeWatchLater = pt.renumberWatchLater(youtubeWatchLater)
    try:
        pt.storeWatchLaterDB(youtubeWatchLater)
        datetime_str = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        pt.WatchLaterStats(youtubeWatchLater, datetime_str)
        quota += pt.WatchLaterCreatorStats(youtubeWatchLater, datetime_str, youtube)
        sortLog.info("Statistics stored in database")
        messages.append("Statistics saved.")
    except Exception as e:
        sortLog.warning(f"Failed to store statistics (non-critical): {e}", exc_info=True)
        messages.append("Warning: Could not save statistics.")

    # Save quota usage
    _save_quota(sortLog, inDB, quota)
    messages.append(f"Quota used: {quota}")

    flash(" ".join(messages))


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
