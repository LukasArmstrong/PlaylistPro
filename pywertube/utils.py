import datetime as dt
import pickle
import re
import os
import operator
import yaml
import json
import statistics as stats

from .logging_config import getLogger


def checkType(var, expected_type):
    """Validate that a variable is of the expected type."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    if not isinstance(var, expected_type):
        gLogger.error(f"{var} not of {expected_type}!", variable=var, type=expected_type)
        raise TypeError(f"{var} not of type: {expected_type}!")
    gLogger.debug("Type Checks out! Leaving...")


def checkTypeReturn(var, expected_type):
    """Check if a variable is of the expected type and return boolean."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    if not isinstance(var, expected_type):
        gLogger.warning(f"{var} not of {expected_type}!", variable=var, type=expected_type)
        return False
    gLogger.debug("Type Checks out! Returning True...")
    return True


def renumberWatchLater(watchLater):
    """Renumber the positions in a watch later list."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    checkType(watchLater, list)
    for x in range(len(watchLater)):
        watchLater[x] = (x, watchLater[x][1], watchLater[x][2], watchLater[x][3], watchLater[x][4], watchLater[x][5], watchLater[x][6])
    gLogger.debug("Returning renumbered Watch Later...")
    return watchLater


def getProjectVariablesYAML(file):
    """Load project variables from a YAML file."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    checkType(file, str)
    with open(file, 'r') as f:
        projectVariables = yaml.safe_load(f)
    print(projectVariables)
    gLogger.debug("Returning tuple packed values...")
    return tuple(projectVariables.values())


def getProjectVariablesENV():
    """Load project variables from environment variables."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    database = os.environ.get('DATABASE')
    mariaPort = int(os.environ.get('DATABASE_PORT'))
    password = os.environ.get('DATABASE_PASSWORD')
    serverIp = os.environ.get('DATABASE_SERVER_IP')
    user = os.environ.get('DATABASE_USER')
    projectID = int(os.environ.get('IDRIS_PROJECT_ID'))
    portNumber = int(os.environ.get('INTERNAL_FLOW_PORT'))
    playlistID = os.environ.get('YOUTUBE_PLAYLIST_ID')
    hostIP = os.environ.get('HOST_IP')
    hostPort = int(os.environ.get('HOST_PORT'))
    return (database, mariaPort, password, serverIp, user, hostIP, hostPort, projectID, portNumber, playlistID)


def durationString2Sec(durationString, hours_pattern=re.compile(r'(\d+)H'), minutes_pattern=re.compile(r'(\d+)M'), seconds_pattern=re.compile(r'(\d+)S')):
    """Convert YouTube duration string (ISO 8601) to seconds."""
    gLogger = getLogger()
    gLogger.debug("Entering...")

    gLogger.debug("Making sure durationString Variable is string...")
    checkType(durationString, str)

    gLogger.debug("Checking time patterns...")
    checkType(hours_pattern, re.Pattern)
    checkType(minutes_pattern, re.Pattern)
    checkType(seconds_pattern, re.Pattern)

    gLogger.debug("Searching durationString for time patterns...")
    hoursString = hours_pattern.search(durationString)
    minutesString = minutes_pattern.search(durationString)
    secondsString = seconds_pattern.search(durationString)

    gLogger.debug("Converting time string to int...")
    hours = int(hoursString.group(1)) if hoursString else 0
    minutes = int(minutesString.group(1)) if minutesString else 0
    seconds = int(secondsString.group(1)) if secondsString else 0

    gLogger.debug("Coverting ints to time object...")
    video_seconds = dt.timedelta(
        hours=hours,
        minutes=minutes,
        seconds=seconds
    ).total_seconds()

    gLogger.debug("Returning time object...")
    return video_seconds


def dateString2EpochTime(dateString, time_pattern="%Y-%m-%dT%H:%M:%SZ"):
    """Convert a date string to Unix epoch time."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(dateString, str)
    checkType(time_pattern, str)

    gLogger.debug("Converting date string to datetime object...")
    d = dt.datetime.strptime(dateString, time_pattern)

    gLogger.debug("Getting datetime object from start of epoch...")
    epoch = dt.datetime(1970, 1, 1)

    gLogger.debug("Returning seconds from start of epoch...")
    return (d - epoch).total_seconds()


def filterDict(_dict, string, threshold):
    """Filter a dictionary based on a comparison operator and threshold."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(_dict, dict)
    checkType(string, str)
    checkType(threshold, int)

    gLogger.debug("Definig operator dictionary...")
    ops = {
        "<": operator.ge,
        "<=": operator.gt,
        ">": operator.le,
        ">=": operator.lt
    }

    gLogger.debug("Creating copy of dictionary...")
    tempDict = _dict.copy()

    gLogger.debug("Looping over dictionary items...")
    for key, value in _dict.items():
        if ops[string](value, threshold):
            gLogger.debug(f"Deleting pair: ({key},{value}")
            del tempDict[key]

    gLogger.debug("Returning filtered dictionary...")
    return tempDict


def sanitizeTitle(string):
    """Remove special characters from a title string."""
    gLogger = getLogger()
    gLogger.debug("Entering...")

    gLogger.debug("Checking Type...")
    checkType(string, str)

    gLogger.debug("Getting characters to remove...")
    char2Remove = '",\',?'

    gLogger.debug("Looping over characters...")
    for char in char2Remove:
        string = string.replace(char, '')

    gLogger.debug("Returning sanitized string...")
    return string


def getCreatorDictionary(creatorList, youtube):
    """Build a dictionary mapping creator names to IDs."""
    # Import here to avoid circular dependency
    from .database import getDataDB
    from .youtube_api import insertCreatorsDB

    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(creatorList, list)

    import googleapiclient.discovery as gacd
    checkType(youtube, gacd.Resource)

    gLogger.debug("Getting Ids for creators...")
    data = getDataDB('Creators', ['id', 'creators'])
    dataDict = dict(data)
    gLogger.debug("Swapping values and keys in creator dict...")
    creatorDict = dict((v, k) for k, v in dataDict.items())
    lastID = max(creatorDict.values()) if creatorDict else 0
    gLogger.debug("Looping over creators to make sure all have an ID...")
    quotaUsed = 0
    for creator in creatorList:
        if sanitizeTitle(creator) not in creatorDict:
            insertCreatorsDB(sanitizeTitle(creator), youtube=youtube)
            creatorDict[creator] = lastID + 1
            lastID += 1
    gLogger.debug("Returning creator dictionary...")
    return creatorDict, quotaUsed * 100


def WatchLaterStats(watchLater, datetime):
    """Calculate and store statistics about the watch later list."""
    # Import here to avoid circular dependency
    from .database import setDataDB

    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(watchLater, list)
    checkType(datetime, str)
    gLogger.debug("Creating creator list and duration list...")
    durationList = [video[3] for video in watchLater]
    creatorList = [video[4] for video in watchLater]
    gLogger.debug("Creatings watch later stats...")
    cols = ['Date', 'Length', 'TotalDuration', 'AverageDuration', 'MedianDuration', 'StdvDuration', 'VarianceDuration', 'NumUniqueCreators']
    vals = [datetime, len(watchLater), sum(durationList), stats.fmean(durationList), stats.median(durationList), stats.pstdev(durationList), stats.pvariance(durationList), len(set(creatorList))]
    setDataDB('WatchLaterStats', cols, vals)
    gLogger.debug("Leaving...")


def WatchLaterCreatorStats(watchLater, datetime, youtube):
    """Calculate and store per-creator statistics."""
    # Import here to avoid circular dependency
    from .database import setDataDB

    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(watchLater, list)
    checkType(datetime, str)

    import googleapiclient.discovery as gacd
    checkType(youtube, gacd.Resource)

    gLogger.debug("Creating creator list and duration list...")
    creatorList = [video[4] for video in watchLater]
    durationList = [video[3] for video in watchLater]
    gLogger.debug("Creating Creator -> ID mapping...")
    creatorDict, quotaUsed = getCreatorDictionary(creatorList, youtube)
    gLogger.debug("Looping over creators to save stats")
    for creator in creatorDict.keys():
        creatorDurationList = [video[3] for video in watchLater if video[4] == creator]
        creatorPublishList = [video[5] for video in watchLater if video[4] == creator]
        if creatorDurationList and creatorPublishList:
            cols = ['date', 'CreatorID', 'Frequency', 'Duration', 'OldestVideo', 'LongestVideo', 'AverageUnixAge', 'FrequencyPercentage', 'DurationPercentage']
            vals = [datetime, creatorDict[creator], creatorList.count(creator), sum(creatorDurationList), creatorPublishList[-1], max(creatorDurationList), stats.fmean(creatorPublishList), creatorList.count(creator) / len(creatorList), sum(creatorDurationList) / sum(durationList)]
            setDataDB('WatchLaterCreatorStats', cols, vals)
    gLogger.debug("Returning quota...")
    return quotaUsed


def createJsonFile(file, data_dict):
    """Write a dictionary to a JSON file."""
    with open(file, 'w') as outfile:
        json.dump(data_dict, outfile, indent=4)


def createYamlFile(file, data_dict):
    """Write a dictionary to a YAML file."""
    with open(file, 'w') as yaml_file:
        yaml.dump(data_dict, yaml_file, default_flow_style=False)


def pickleSomething(thing, nameString):
    """Pickle an object and save it to a file."""
    os.makedirs("pickles", exist_ok=True)
    with open(f"pickles/{nameString}.pickle", "wb") as f:
        print("Saving " + nameString + " for future use...")
        pickle.dump(thing, f)
