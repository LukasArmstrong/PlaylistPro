"""
pywertube - Python Power User code for YouTube

A library for managing and sorting YouTube playlists.
"""

# Logging
from .logging_config import (
    initLogger,
    setLogger,
    getLogger,
)

# Database operations
from .database import (
    getDataBaseConnection,
    getDataDB,
    setDataDB,
    updateDataDB,
    clearTableDB,
    storeWatchLaterDB,
    closeDBConnection,
    CloseDBconnnection,  # backwards compatibility alias
)

# Quota management
from .quota import (
    getQuotaUsed,
    setQuotaUsed,
)

# YouTube API
from .youtube_api import (
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
    # Logging
    'initLogger',
    'setLogger',
    'getLogger',
    # Database
    'getDataBaseConnection',
    'getDataDB',
    'setDataDB',
    'updateDataDB',
    'clearTableDB',
    'storeWatchLaterDB',
    'closeDBConnection',
    'CloseDBconnnection',
    # Quota
    'getQuotaUsed',
    'setQuotaUsed',
    # YouTube API
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
