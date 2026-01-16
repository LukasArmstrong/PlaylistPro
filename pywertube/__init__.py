"""
pywertube - Python Power User code for YouTube

A library for managing and sorting YouTube playlists.
Supports SQLite (default) and MariaDB/MySQL via SQLAlchemy.
"""

# Configuration
from .config import config, load_config, AppConfig, DatabaseConfig, OAuthConfig

# Database
from .db import db, init_db

# Models
from .models import (
    Creator,
    Keyphrase,
    WatchLaterVideo,
    OrderVideo,
    SequentialCreator,
    WatchLaterStat,
    WatchLaterCreatorStat,
    QuotaLimit,
)

# Logging
from .logging_config import (
    initLogger,
    setLogger,
    getLogger,
)

# Database operations
from .database import (
    get_creators_dict,
    get_keyphrases_dict,
    get_sequential_creators_dict,
    get_order_videos_list,
    clear_watch_later,
    clear_order_videos,
    store_watch_later,
    get_watch_later_videos,
    get_creator_by_name,
    get_creator_id_map,
    add_creator,
    add_watch_later_stat,
    add_creator_stat,
    get_subscribed_channel_ids,
    # Backwards compatibility
    storeWatchLaterDB,
    clearTableDB,
    getDataBaseConnection,
    closeDBConnection,
    CloseDBconnnection,
)

# Quota management
from .quota import (
    getQuotaUsed,
    setQuotaUsed,
)

# YouTube API
from .youtube_api import (
    get_youtube_client,
    getCredentials,
    getFlowObject,
    saveCredentails,
    getWatchLater,
    updatePlaylist,
    findChannelID,
    getVideoYT,
    getSubscriptions,
    insertVideoYT,
    storeSubscripton,
    insertCreatorsDB,
    pubhubsubhubPost,
    subscribeCreators,
)

# Sorting
from .sorting import (
    getPriorityVideos,
    getSerializedVideos,
    getSequentialVideos,
    getFollowUpVideos,
    sortSeriesVideos,
    sortSequentialVideo,
    sortWatchLater,
)

# Utilities
from .utils import (
    checkType,
    checkTypeReturn,
    renumberWatchLater,
    getProjectVariablesYAML,
    getProjectVariablesENV,
    durationString2Sec,
    dateString2EpochTime,
    filterDict,
    sanitizeTitle,
    getCreatorDictionary,
    WatchLaterStats,
    WatchLaterCreatorStats,
    createJsonFile,
    createYamlFile,
    pickleSomething,
)

__all__ = [
    # Configuration
    'config',
    'load_config',
    'AppConfig',
    'DatabaseConfig',
    'OAuthConfig',
    # Database core
    'db',
    'init_db',
    # Models
    'Creator',
    'Keyphrase',
    'WatchLaterVideo',
    'OrderVideo',
    'SequentialCreator',
    'WatchLaterStat',
    'WatchLaterCreatorStat',
    'QuotaLimit',
    # Logging
    'initLogger',
    'setLogger',
    'getLogger',
    # Database operations
    'get_creators_dict',
    'get_keyphrases_dict',
    'get_sequential_creators_dict',
    'get_order_videos_list',
    'clear_watch_later',
    'clear_order_videos',
    'store_watch_later',
    'get_watch_later_videos',
    'get_creator_by_name',
    'get_creator_id_map',
    'add_creator',
    'add_watch_later_stat',
    'add_creator_stat',
    'get_subscribed_channel_ids',
    'storeWatchLaterDB',
    'clearTableDB',
    'getDataBaseConnection',
    'closeDBConnection',
    'CloseDBconnnection',
    # Quota
    'getQuotaUsed',
    'setQuotaUsed',
    # YouTube API
    'get_youtube_client',
    'getCredentials',
    'getFlowObject',
    'saveCredentails',
    'getWatchLater',
    'updatePlaylist',
    'findChannelID',
    'getVideoYT',
    'getSubscriptions',
    'insertVideoYT',
    'storeSubscripton',
    'insertCreatorsDB',
    'pubhubsubhubPost',
    'subscribeCreators',
    # Sorting
    'getPriorityVideos',
    'getSerializedVideos',
    'getSequentialVideos',
    'getFollowUpVideos',
    'sortSeriesVideos',
    'sortSequentialVideo',
    'sortWatchLater',
    # Utilities
    'checkType',
    'checkTypeReturn',
    'renumberWatchLater',
    'getProjectVariablesYAML',
    'getProjectVariablesENV',
    'durationString2Sec',
    'dateString2EpochTime',
    'filterDict',
    'sanitizeTitle',
    'getCreatorDictionary',
    'WatchLaterStats',
    'WatchLaterCreatorStats',
    'createJsonFile',
    'createYamlFile',
    'pickleSomething',
]
