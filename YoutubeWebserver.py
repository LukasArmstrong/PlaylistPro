"""
PlaylistPro Web Server

A Flask application for managing and sorting YouTube playlists.
Supports SQLite (default) and MariaDB/MySQL databases.
"""

from flask import Flask, request, render_template, flash
import pywertube as pt
import os
from datetime import datetime as dt
from googleapiclient.discovery import build

# Set Logger
if 'TERM_PROGRAM' in os.environ.keys() and os.environ['TERM_PROGRAM'] == 'vscode':
    logger = pt.initLogger(__file__, debug=True, verbose=False)
else:
    logger = pt.initLogger(__file__, debug=os.environ.get('DEBUG_MODE', False), verbose=os.environ.get('VERBOSE_DEBUG', False))

# Load environment variables
database, mariaPort, password, serverIp, user, host_ip, host_port, projectID, portNumber, playlistID = pt.getProjectVariablesENV()

# Build client secret for OAuth
client_secret_dict = {
    'web': {
        'client_id': os.environ.get('CLIENT_ID'),
        'project_id': os.environ.get('PROJECT_ID'),
        'auth_uri': os.environ.get('AUTH_URI'),
        'token_uri': os.environ.get('TOKEN_URI'),
        'auth_provider_x509_cert_url': os.environ.get('AUTH_PROVIDER'),
        'client_secret': os.environ.get('CLIENT_SECRET'),
        'redirect_uris': os.environ.get('REDIRECT_URIS', '').split(',')
    }
}
pt.createJsonFile('youtube_user_client_secret.json', client_secret_dict)

# Sorting keywords
numberedSerializedKeywords = ['series', 'part', 'finale', 'episode', 'ep', '#', 'chapter']
serializedKeywords = []

# Initialize Flask app
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Configure database based on environment
# Detection priority:
# 1. Explicit DATABASE_URL environment variable (production/docker)
# 2. ENVIRONMENT variable set to 'production' + MariaDB env vars
# 3. Default to SQLite (development)

def get_database_url():
    """Determine the database URL based on environment."""
    # Check for explicit DATABASE_URL first (docker-compose, etc.)
    if os.environ.get('DATABASE_URL'):
        return os.environ.get('DATABASE_URL'), 'production'

    # Check if we're in production mode with MariaDB env vars
    env = os.environ.get('ENVIRONMENT', os.environ.get('FLASK_ENV', 'development'))
    is_production = env.lower() in ('production', 'prod', 'docker')

    if is_production and all([serverIp, user, password, database]):
        # Build URL from individual MariaDB environment variables
        url = f"mysql+pymysql://{user}:{password}@{serverIp}:{mariaPort}/{database}"
        return url, 'production'

    # Default to SQLite for development
    return 'sqlite:///playlistpro.db', 'development'


database_url, environment = get_database_url()

if environment == 'development':
    logger.info("Development mode: Using SQLite database")
else:
    # Log URL without password for security
    safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
    logger.info(f"Production mode: Using database at {safe_url}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    activeCredentials = pt.getCredentials(portNumber, 'youtube_user_client_secret.json')
    subLog.info("Credentials obtained!")

    youtube = build("youtube", "v3", credentials=activeCredentials)
    subLog.info("Youtube object built!")

    subs = pt.getSubscriptions(youtube, mine=True)
    pt.storeSubscripton(subs, youtube)
    pt.subscribeCreators()

    return "subscribers updated"


def sort():
    """Main sorting function - orchestrates the playlist sorting process."""
    msg = ""
    sortLog = logger.bind()
    pt.setLogger(sortLog)
    sortLog.info("sortLogger set as logger!")

    if request.method == 'POST':
        sortLog.info("Entering POST Request")
        try:
            # Load data from database using ORM
            creatorDictionary, keywordDictionary, videoFollowUpList, sequentialCreatorsDict, quota, inDB = initWatchLater(sortLog)

            try:
                youtube = getYoutubeObj(logger)
                youtubeWatchLater, requestOps = pt.getWatchLater(youtube, playlistID, True)
                quota += requestOps
                sortLog.info(f"Youtube Watchlater Obtained! Quota incurred: {requestOps}, Total: {quota}")

                try:
                    sortedWatchLater = pt.sortWatchLater(
                        youtubeWatchLater,
                        creatorDictionary,
                        keywordDictionary,
                        numberedSerializedKeywords,
                        serializedKeywords,
                        videoFollowUpList,
                        sequentialCreatorsDict
                    )
                    sortLog.info("Watchlater sorted!")

                    try:
                        videoOps, youtubeWatchLater = pt.updatePlaylist(
                            youtubeWatchLater,
                            sortedWatchLater,
                            youtube,
                            playlistID
                        )
                        quota += videoOps * 50
                        sortLog.info(f"Watchlater updated on youtube! Quota incurred: {videoOps*50}, Total: {quota}")

                        youtubeWatchLater = pt.renumberWatchLater(youtubeWatchLater)
                        sortLog.debug("Watchlater renumbered for DB storage!")
                        msg = "Sorted! \n"

                        try:
                            pt.storeWatchLaterDB(youtubeWatchLater)
                            sortLog.info("Watchlater stored in DB for stats!")

                            datetime_str = dt.now().strftime('%Y-%m-%d %H:%M:%S')
                            pt.WatchLaterStats(youtubeWatchLater, datetime_str)
                            quota += pt.WatchLaterCreatorStats(youtubeWatchLater, datetime_str, youtube)
                            msg += "Stored!\n"
                        except Exception as e:
                            msg += "Error storing stats!\n"
                            sortLog.error(f"Error: {e}")
                    except Exception as e:
                        msg += "Error updating yt watch later!\n"
                        sortLog.error(f"Error: {e}")
                except Exception as e:
                    msg += "Error sorting Watch Later!\n"
                    sortLog.error(f"Error: {e}")
            except Exception as e:
                msg += "Error getting yt credentials or watchlater list!\n"
                sortLog.error(f"Error: {e}")
        except Exception as e:
            msg += "Error getting data from DB!\n"
            sortLog.error(f"Error: {e}")

        try:
            pt.setQuotaUsed(inDB, quota, 1)
            sortLog.info(f"Used Quota set! Total accrued: {quota}")
            sortLog.info("Watch later stats stored")
            msg += f"Quota Saved! Accrued: {quota}\n"
        except Exception:
            msg += "Error setting data in DB \n"

        flash(msg)


@app.route('/renew', methods=['GET'])
def reNewToken():
    if request.method == 'GET':
        flow = pt.getFlowObject('youtube_user_client_secret.json')
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
    quota, inDB = pt.getQuotaUsed(projectID)
    log.info(f"Used Quota obtained! So far incurred: {quota}")

    return creatorDictionary, keywordDictionary, videoFollowUpList, sequentialCreatorsDict, quota, inDB


def getYoutubeObj(log):
    """Build and return a YouTube API client."""
    activeCredentials = pt.getCredentials(portNumber, 'youtube_user_client_secret.json')
    log.info("Credentials obtained!")

    youtube = build("youtube", "v3", credentials=activeCredentials)
    log.info("Youtube object built!")

    return youtube


if __name__ == "__main__":
    app.run(host=host_ip, port=host_port)
