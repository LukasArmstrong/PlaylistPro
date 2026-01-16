"""
Sorting algorithms for PlaylistPro watch later playlist.

This module contains the logic for prioritizing and ordering videos
based on creator preferences, series detection, and other criteria.
"""

import re
from natsort import natsorted

from .logging_config import getLogger
from .database import clearTableDB
from .utils import checkType, filterDict


def getPriorityVideos(watchLaterList, creatorDict, keywordDict, priorityThreshold, durationThreshold):
    """
    Filter and categorize videos by priority based on creator and keyword scores.

    Returns:
        tuple: (priorityWatchLater, nonPriority) - priority videos grouped by score level,
               and remaining non-priority videos
    """
    gLogger = getLogger()
    nonPriority = watchLaterList.copy()

    # Filter dictionaries to only include items above threshold
    creatorDict = filterDict(creatorDict, ">", priorityThreshold)
    keywordDict = filterDict(keywordDict, ">", priorityThreshold)

    # Build priority score levels
    setValues = set(list(creatorDict.values()))
    setValues.update(list(keywordDict.values()))
    scoreSet = sorted(list(setValues), reverse=True)

    priorityWatchLater = [[] for _ in range(len(scoreSet))]

    for item in watchLaterList:
        # Check keywords first (higher priority than creator)
        keywordFound = False
        for word in keywordDict.keys():
            if word in item[6] and keywordDict[word] in scoreSet:
                scoreIndex = scoreSet.index(keywordDict[word])
                priorityWatchLater[scoreIndex].append(item)
                nonPriority.remove(item)
                keywordFound = True
                break

        if keywordFound:
            continue

        # Check creator priority
        if item[4] in creatorDict.keys():
            if item[3] < durationThreshold and creatorDict[item[4]] in scoreSet:
                scoreIndex = scoreSet.index(creatorDict[item[4]])
                priorityWatchLater[scoreIndex].append(item)
                nonPriority.remove(item)

    total_priority = sum(len(group) for group in priorityWatchLater)
    gLogger.info("Extracted priority videos",
                 priority_count=total_priority,
                 remaining=len(nonPriority),
                 score_levels=len(scoreSet))

    return priorityWatchLater, nonPriority


def getSerializedVideos(watchLaterList, numSerKeywords, serKeywords):
    """
    Extract videos that are part of a series based on keywords.

    Returns:
        tuple: (seriesList, nonSerialized) - series videos grouped by creator,
               and remaining non-series videos
    """
    gLogger = getLogger()
    nonSerialized = watchLaterList.copy()

    # Build regex pattern for series detection
    seriesPattern = re.compile(
        r"(%s)\s?\d+" % "|".join(numSerKeywords) + "|(%s)" % "|".join(serKeywords),
        re.IGNORECASE
    )

    # Group by creator
    creators = list(set(item[4] for item in watchLaterList))
    seriesList = [[] for _ in range(len(creators))]

    for item in watchLaterList:
        if seriesPattern.search(item[6]):
            creatorIndex = creators.index(item[4])
            seriesList[creatorIndex].append(item)
            nonSerialized.remove(item)

    total_series = sum(len(group) for group in seriesList)
    gLogger.info("Extracted series videos",
                 series_count=total_series,
                 remaining=len(nonSerialized))

    return seriesList, nonSerialized


def getSequentialVideos(watchLaterList, sequentialCreatorsDict, durationThreshold):
    """
    Extract videos from creators whose content should be watched in order.

    Returns:
        tuple: (seqList, nonSequential) - sequential videos grouped by creator,
               and remaining videos
    """
    gLogger = getLogger()
    nonSequential = watchLaterList.copy()
    seqList = [[] for _ in range(len(sequentialCreatorsDict.keys()))]

    creatorKeys = list(sequentialCreatorsDict.keys())

    for video in watchLaterList:
        if video[4] in creatorKeys:
            if (video[3] < durationThreshold) or bool(sequentialCreatorsDict[video[4]]):
                seqIndex = creatorKeys.index(video[4])
                seqList[seqIndex].append(video)
                nonSequential.remove(video)

    total_sequential = sum(len(group) for group in seqList)
    gLogger.info("Extracted sequential videos",
                 sequential_count=total_sequential,
                 remaining=len(nonSequential))

    return seqList, nonSequential


def getFollowUpVideos(watchLaterList, FollowUpIDList):
    """
    Extract videos that are follow-ups to other videos.

    Returns:
        list: Follow-up videos grouped by parent video
    """
    gLogger = getLogger()
    checkType(watchLaterList, list)
    checkType(FollowUpIDList, list)

    # Find videos in watch later that are in follow-up list
    videos = [item for item in watchLaterList if item[2] in FollowUpIDList[1]]

    if not videos:
        clearTableDB('OrderVideos')
        return []

    # Identify parent videos (those with no predecessor)
    parentIds = [v for i, v in enumerate(FollowUpIDList[0]) if FollowUpIDList[2][i] is None]
    nullCount = FollowUpIDList[2].count(None)
    FollowUpWatchLater = [[] for _ in range(nullCount)]

    for index, id in enumerate(FollowUpIDList[2]):
        if id is None:
            idIndex = parentIds.index(FollowUpIDList[0][index])
        else:
            idIndex = parentIds.index(id)
        FollowUpWatchLater[idIndex].append(videos[index])

    gLogger.info("Extracted follow-up videos", groups=len(FollowUpWatchLater))
    return FollowUpWatchLater


def sortSeriesVideos(watchLaterList):
    """Sort videos within each series using natural sort on title."""
    for index in range(len(watchLaterList)):
        if watchLaterList[index]:
            watchLaterList[index] = natsorted(
                watchLaterList[index],
                key=lambda x: x[6].rsplit("-", 1)[1] if '-' in x[6] else x[6]
            )
    return watchLaterList


def sortSequentialVideo(watchLaterList):
    """Sort sequential videos by publish time (oldest first)."""
    for index in range(len(watchLaterList)):
        watchLaterList[index] = sorted(watchLaterList[index], key=lambda x: x[5])
    return watchLaterList


def sortWatchLater(watchLaterList, creatorDict, keywordDict, numSerKeywords, serKeywords, videoIDFollowUpList, sequentialCreators):
    """
    Main sorting function that orchestrates all sorting strategies.

    WatchLaterList structure:
    (0-position on yt, 1-playlist id for yt, 2-video id for yt, 3-duration in seconds,
     4-creator, 5-published time in unix time, 6-video title)

    Sorting order:
    1. Priority videos (by creator/keyword score)
    2. Sequential creator videos (by publish time)
    3. Series videos (naturally sorted)
    4. Remaining videos (by duration, then publish time)
    5. Follow-up videos repositioned after their predecessors
    """
    gLogger = getLogger()

    # Configuration
    videoCountThreshold = 50
    durationThreshold = 61 * 60  # 61 minutes in seconds
    periodicity = 2

    # Determine priority threshold based on list length
    priorityThreshold = 0 if len(watchLaterList) > videoCountThreshold else 1

    gLogger.info("Starting sort",
                 video_count=len(watchLaterList),
                 priority_threshold=priorityThreshold)

    # Step 1 - Extract sublists
    priorityWatchLater, workingWatchLater = getPriorityVideos(
        watchLaterList, creatorDict, keywordDict, priorityThreshold, durationThreshold
    )

    followUpWatchLater = []
    if videoIDFollowUpList:
        followUpWatchLater = getFollowUpVideos(workingWatchLater, videoIDFollowUpList)

    sequentialWatchLater, workingWatchLater = getSequentialVideos(
        workingWatchLater, sequentialCreators, durationThreshold
    )

    # Series extraction disabled for now
    seriesWatchLater = []

    # Step 2 - Sort each segment
    sortedpriorityWatchLater = []
    for priorityGroup in priorityWatchLater:
        sortedpriorityWatchLater += sorted(priorityGroup, key=lambda x: x[5])

    sortedSequentialWatchLater = sortSequentialVideo(sequentialWatchLater)
    sortedSeriesWatchLater = sortSeriesVideos(seriesWatchLater)

    # Sort remaining by duration, then publish time
    workingWatchLater.sort(key=lambda x: (x[3], x[5]))

    # Step 3 - Merge sequential and series back into main list
    for index, item in enumerate(workingWatchLater):
        # Merge sequential videos at appropriate positions
        for row in range(len(sortedSequentialWatchLater)):
            if (sortedSequentialWatchLater[row] and
                sortedSequentialWatchLater[row][0][3] <= item[3] and
                sortedSequentialWatchLater[row][0][4] != item[4]):
                for v_idx, vid in enumerate(sortedSequentialWatchLater[row]):
                    workingWatchLater.insert(index + v_idx * periodicity, vid)
                sortedSequentialWatchLater[row] = []

        # Merge series videos
        for row in range(len(sortedSeriesWatchLater)):
            if (sortedSeriesWatchLater[row] and
                sortedSeriesWatchLater[row][0][3] <= item[3] and
                sortedSeriesWatchLater[row][0][4] != item[4]):
                workingWatchLater.insert(index, sortedSeriesWatchLater[row][0])
                sortedSeriesWatchLater[row].pop(0)

    # Step 4 - Reposition follow-up videos after their predecessors
    for row in followUpWatchLater:
        positionMovement = 2 if len(row) > 3 else 1
        for i in range(len(row) - 1):
            predecentVideoPosition = workingWatchLater.index(row[i])
            workingWatchLater.remove(row[i + 1])
            workingWatchLater.insert(predecentVideoPosition + positionMovement, row[i + 1])

    # Step 5 - Combine priority and working lists
    result = sortedpriorityWatchLater + workingWatchLater

    gLogger.info("Sort complete",
                 priority_videos=len(sortedpriorityWatchLater),
                 other_videos=len(workingWatchLater),
                 total=len(result))

    return result
