"""
Utility functions for PlaylistPro.

This module contains helper functions for type checking, data conversion,
configuration loading, and statistics generation.
"""

from __future__ import annotations

import datetime as dt
import pickle
import re
import os
import operator
import yaml
import json
import statistics as stats
from typing import Any, Optional

from dotenv import load_dotenv

from .logging_config import getLogger

load_dotenv()

# Type aliases
VideoTuple = tuple[int, str, str, float, str, float, str]


def checkType(var: Any, expected_type: type) -> None:
    """Validate that a variable is of the expected type."""
    if not isinstance(var, expected_type):
        gLogger = getLogger()
        gLogger.error("Type check failed", expected=str(expected_type), actual=str(type(var)))
        raise TypeError(f"{var} not of type: {expected_type}!")


def checkTypeReturn(var: Any, expected_type: type) -> bool:
    """Check if a variable is of the expected type and return boolean."""
    return isinstance(var, expected_type)


def renumberWatchLater(watchLater: list[VideoTuple]) -> list[VideoTuple]:
    """Renumber the positions in a watch later list."""
    checkType(watchLater, list)
    for x in range(len(watchLater)):
        watchLater[x] = (x, watchLater[x][1], watchLater[x][2], watchLater[x][3], watchLater[x][4], watchLater[x][5], watchLater[x][6])
    return watchLater


def getProjectVariablesYAML(file: str) -> tuple[Any, ...]:
    """Load project variables from a YAML file."""
    checkType(file, str)
    with open(file, 'r') as f:
        projectVariables = yaml.safe_load(f)
    return tuple(projectVariables.values())


def getProjectVariablesENV() -> tuple[Optional[str], int, Optional[str], Optional[str], Optional[str], str, int, int, int, Optional[str]]:
    """Load project variables from environment variables."""
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


def durationString2Sec(
    durationString: str,
    hours_pattern: re.Pattern[str] = re.compile(r'(\d+)H'),
    minutes_pattern: re.Pattern[str] = re.compile(r'(\d+)M'),
    seconds_pattern: re.Pattern[str] = re.compile(r'(\d+)S')
) -> float:
    """Convert YouTube duration string (ISO 8601) to seconds."""
    checkType(durationString, str)

    hoursString = hours_pattern.search(durationString)
    minutesString = minutes_pattern.search(durationString)
    secondsString = seconds_pattern.search(durationString)

    hours = int(hoursString.group(1)) if hoursString else 0
    minutes = int(minutesString.group(1)) if minutesString else 0
    seconds = int(secondsString.group(1)) if secondsString else 0

    return dt.timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()


def dateString2EpochTime(dateString: str, time_pattern: str = "%Y-%m-%dT%H:%M:%SZ") -> float:
    """Convert a date string to Unix epoch time."""
    checkType(dateString, str)
    d = dt.datetime.strptime(dateString, time_pattern)
    epoch = dt.datetime(1970, 1, 1)
    return (d - epoch).total_seconds()


def filterDict(_dict: dict[str, int], string: str, threshold: int) -> dict[str, int]:
    """Filter a dictionary based on a comparison operator and threshold."""
    checkType(_dict, dict)
    checkType(string, str)
    checkType(threshold, int)

    ops = {
        "<": operator.ge,
        "<=": operator.gt,
        ">": operator.le,
        ">=": operator.lt
    }

    return {key: value for key, value in _dict.items() if not ops[string](value, threshold)}


def sanitizeTitle(string: str) -> str:
    """Remove special characters from a title string."""
    checkType(string, str)
    for char in '",\',?':
        string = string.replace(char, '')
    return string


def getCreatorDictionary(creatorList: list[str], youtube: Any) -> tuple[dict[str, int], int]:
    """Build a dictionary mapping creator names to IDs."""
    # Import here to avoid circular dependency
    from .database import get_creator_id_map, add_creator
    from .youtube_api import findChannelID

    checkType(creatorList, list)
    import googleapiclient.discovery as gacd
    checkType(youtube, gacd.Resource)

    creatorDict = get_creator_id_map()
    lastID = max(creatorDict.values()) if creatorDict else 0
    new_creators = 0

    for creator in creatorList:
        sanitized = sanitizeTitle(creator)
        if sanitized not in creatorDict:
            channel_id = findChannelID(creator, youtube)
            add_creator(sanitized, channel_id=channel_id)
            creatorDict[sanitized] = lastID + 1
            lastID += 1
            new_creators += 1

    if new_creators:
        gLogger = getLogger()
        gLogger.info("Added new creators", count=new_creators)

    return creatorDict, new_creators * 100


def WatchLaterStats(watchLater: list[VideoTuple], datetime_str: str) -> None:
    """Calculate and store statistics about the watch later list."""
    # Import here to avoid circular dependency
    from .database import add_watch_later_stat

    checkType(watchLater, list)
    checkType(datetime_str, str)

    durationList = [video[3] for video in watchLater]
    creatorList = [video[4] for video in watchLater]

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


def WatchLaterCreatorStats(watchLater: list[VideoTuple], datetime_str: str, youtube: Any) -> int:
    """Calculate and store per-creator statistics."""
    # Import here to avoid circular dependency
    from .database import add_creator_stat

    checkType(watchLater, list)
    checkType(datetime_str, str)
    import googleapiclient.discovery as gacd
    checkType(youtube, gacd.Resource)

    creatorList = [video[4] for video in watchLater]
    durationList = [video[3] for video in watchLater]
    creatorDict, quotaUsed = getCreatorDictionary(creatorList, youtube)

    stats_saved = 0
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
            stats_saved += 1

    gLogger = getLogger()
    gLogger.info("Saved creator stats", creators=stats_saved)
    return quotaUsed


def createJsonFile(file: str, data_dict: dict[str, Any]) -> None:
    """Write a dictionary to a JSON file."""
    with open(file, 'w') as outfile:
        json.dump(data_dict, outfile, indent=4)


def createYamlFile(file: str, data_dict: dict[str, Any]) -> None:
    """Write a dictionary to a YAML file."""
    with open(file, 'w') as yaml_file:
        yaml.dump(data_dict, yaml_file, default_flow_style=False)


def pickleSomething(thing: Any, nameString: str) -> None:
    """Pickle an object and save it to a file."""
    os.makedirs("pickles", exist_ok=True)
    with open(f"pickles/{nameString}.pickle", "wb") as f:
        pickle.dump(thing, f)
