"""
Utility functions for PlaylistPro.

This module contains helper functions for type checking, data conversion,
configuration loading, and statistics generation.
"""

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
    mariaPort = int(os.environ.get('DATABASE_PORT', 3306))
    password = os.environ.get('DATABASE_PASSWORD')
    serverIp = os.environ.get('DATABASE_SERVER_IP')
    user = os.environ.get('DATABASE_USER')
    projectID = int(os.environ.get('IDRIS_PROJECT_ID', 1))
    portNumber = int(os.environ.get('INTERNAL_FLOW_PORT', 8080))
    playlistID = os.environ.get('YOUTUBE_PLAYLIST_ID')
    hostIP = os.environ.get('HOST_IP', '0.0.0.0')
    hostPort = int(os.environ.get('HOST_PORT', 5000))
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
    from .database import get_creator_id_map, add_creator
    from .youtube_api import findChannelID

    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(creatorList, list)

    import googleapiclient.discovery as gacd
    checkType(youtube, gacd.Resource)

    gLogger.debug("Getting Ids for creators...")
    creatorDict = get_creator_id_map()
    lastID = max(creatorDict.values()) if creatorDict else 0

    gLogger.debug("Looping over creators to make sure all have an ID...")
    quotaUsed = 0
    for creator in creatorList:
        sanitized = sanitizeTitle(creator)
        if sanitized not in creatorDict:
            channel_id = findChannelID(creator, youtube)
            add_creator(sanitized, channel_id=channel_id)
            creatorDict[sanitized] = lastID + 1
            lastID += 1

    gLogger.debug("Returning creator dictionary...")
    return creatorDict, quotaUsed * 100


def WatchLaterStats(watchLater, datetime_str):
    """Calculate and store statistics about the watch later list."""
    # Import here to avoid circular dependency
    from .database import add_watch_later_stat

    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(watchLater, list)
    checkType(datetime_str, str)

    gLogger.debug("Creating creator list and duration list...")
    durationList = [video[3] for video in watchLater]
    creatorList = [video[4] for video in watchLater]

    gLogger.debug("Creating watch later stats...")
    add_watch_later_stat(
        datetime_str=datetime_str,
        length=len(watchLater),
        total_duration=sum(durationList),
        avg_duration=stats.fmean(durationList),
        median_duration=stats.median(durationList),
        stdv_duration=stats.pstdev(durationList),
        variance_duration=stats.pvariance(durationList),
        num_unique_creators=len(set(creatorList))
    )
    gLogger.debug("Leaving...")


def WatchLaterCreatorStats(watchLater, datetime_str, youtube):
    """Calculate and store per-creator statistics."""
    # Import here to avoid circular dependency
    from .database import add_creator_stat

    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(watchLater, list)
    checkType(datetime_str, str)

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
            add_creator_stat(
                datetime_str=datetime_str,
                creator_id=creatorDict[creator],
                frequency=creatorList.count(creator),
                duration=sum(creatorDurationList),
                oldest_video=creatorPublishList[-1],
                longest_video=max(creatorDurationList),
                avg_unix_age=stats.fmean(creatorPublishList),
                freq_pct=creatorList.count(creator) / len(creatorList),
                duration_pct=sum(creatorDurationList) / sum(durationList)
            )

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
