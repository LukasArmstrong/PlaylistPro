import re
from natsort import natsorted

from .logging_config import getLogger
from .database import clearTableDB
from .utils import checkType, filterDict


def getPriorityVideos(watchLaterList, creatorDict, keywordDict, priorityThreshold, durationThreshold):
    """Filter and categorize videos by priority based on creator and keyword scores."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    nonPriority = watchLaterList.copy()  # creates copy to return non priority videos as well
    gLogger.debug("Watch Later List copied!")
    creatorDict = filterDict(creatorDict, ">", priorityThreshold)
    keywordDict = filterDict(keywordDict, ">", priorityThreshold)
    gLogger.debug("Creator and Keyboard dictionaries filtered!")
    gLogger.debug("Making set from Creator dictionary values...", creatorDictValues=creatorDict.values())
    setValues = set(list(creatorDict.values()))
    gLogger.debug("Adding Keyphrase dictionary values to set...", KeyphraseDictValues=keywordDict.values())
    setValues.update(list(keywordDict.values()))
    gLogger.debug("Converting set to list and reverse sorting...")
    scoreSet = sorted(list(setValues), reverse=True)
    gLogger.debug("Priority Scores list created!")
    gLogger.debug(f"Creating {len(scoreSet)} dimensional list (Size is determined by number of priority scores)...")
    priorityWatchLater = [[] for i in range(len(scoreSet))]
    gLogger.debug("Looping over watch later list to find priority videos...")
    for item in watchLaterList:
        # Check Keyword first because some creators have natural priority, but subset of videos from said creator have higher priority
        keywordFound = False
        for word in keywordDict.keys():
            if word in item[6]:
                if keywordDict[word] in scoreSet:
                    gLogger.debug(f"Found Video, {item[6]}, is priority with keyword {word}!")
                    gLogger.debug("Finding priority score index of video...")
                    scoreIndex = scoreSet.index(keywordDict[word])
                    gLogger.debug("Appending priority video to priority list...")
                    priorityWatchLater[scoreIndex].append(item)
                    gLogger.debug("Removing priority video from orginal list...")
                    nonPriority.remove(item)
                    keywordFound = True
                    gLogger.debug(f"{item[6]} added to priority list and removed from original list due to keyword {word}!")
                    break
        if keywordFound:
            gLogger.debug("Since Keyword found, skipping creator check...")
            continue
        if item[4] in creatorDict.keys():
            if item[3] < (durationThreshold):
                if creatorDict[item[4]] in scoreSet:
                    gLogger.debug(f"Found Video, {item[6]}, is priority with creator {item[4]}!")
                    gLogger.debug("Finding priority score index of video...")
                    scoreIndex = scoreSet.index(creatorDict[item[4]])
                    gLogger.debug("Appending priority video to priority list...")
                    priorityWatchLater[scoreIndex].append(item)
                    gLogger.debug("Removing priority video from orginal list...")
                    nonPriority.remove(item)
                    gLogger.debug(f"{item[6]} added to priority list and removed from original list due to creator {item[4]}!")
    gLogger.debug("Returning to priority watch later and non-priority list")
    return priorityWatchLater, nonPriority


def getSerializedVideos(watchLaterList, numSerKeywords, serKeywords):
    """Extract videos that are part of a series based on keywords."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    nonSerialized = watchLaterList.copy()
    gLogger.debug("Watch Later List copied!")
    seriesPattern = re.compile(r"(%s)\s?\d+" % "|".join(numSerKeywords) + "|(%s)" % "|".join(serKeywords), re.IGNORECASE)
    gLogger.debug("Regular Expression created to find Serialized Videos")
    gLogger.debug("Creating creator list...")
    creators = [i[4] for i in watchLaterList]
    gLogger.debug("Removing dupes from creator list...")
    creatorsSet = list(set(creators))
    gLogger.debug("Creator List Created!")
    gLogger.debug(f"Creating {len(creatorsSet)} dimensional list (Size is determined by number of creators in watch later)...")
    seriesList = [[] for i in range(len(creatorsSet))]
    gLogger.debug("Looping over watch later list to find serialized videos...")
    for item in watchLaterList:
        result = seriesPattern.search(item[6])
        if result:
            gLogger.debug(f"Result found! {result} in {item[6]}!")
            gLogger.debug("Finding creator index of video...")
            scoreIndex = creatorsSet.index(item[4])
            gLogger.debug("Appending serialized video to creator sub-list...")
            seriesList[scoreIndex].append(item)
            gLogger.debug("Removing serialized video from orginal list...")
            nonSerialized.remove(item)
    gLogger.debug("Returning to serialized watch later and non-serialized list")
    return seriesList, nonSerialized


def getSequentialVideos(watchLaterList, sequentialCreatorsDict, durationThreshold):
    """Extract videos from creators whose content should be watched in order."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    nonSequential = watchLaterList.copy()
    gLogger.debug("Watch Later List copied!")
    gLogger.debug(f"Creating {len(sequentialCreatorsDict.keys())} dimensional list (Size is determined by number of creators in sequential)...")
    seqList = [[] for i in range(len(sequentialCreatorsDict.keys()))]
    gLogger.debug("Looping over watch later list to find serialized videos...")
    for video in watchLaterList:
        if video[4] in sequentialCreatorsDict.keys():
            if (video[3] < durationThreshold) or bool(sequentialCreatorsDict[video[4]]):
                gLogger.debug(f"Result found! {video[6]} by {video[4]}!")
                gLogger.debug("Finding creator index of video...")
                seqIndex = list(sequentialCreatorsDict.keys()).index(video[4])
                gLogger.debug("Appending sequential video to creator sub-list...")
                seqList[seqIndex].append(video)
                gLogger.debug("Removing serialized video from orginal list...")
                nonSequential.remove(video)
    gLogger.debug("Returning to serialized watch later and non-serialized list")
    return seqList, nonSequential


def getFollowUpVideos(watchLaterList, FollowUpIDList):
    """Extract videos that are follow-ups to other videos."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking types...")
    checkType(watchLaterList, list)
    checkType(FollowUpIDList, list)

    gLogger.debug("Pulling out videos records from watcherlater if in Follow up list...")
    videos = [item for item in watchLaterList if item[2] in FollowUpIDList[1]]

    gLogger.debug("Checking if follow up videos in watch later still")
    if not videos:
        clearTableDB('OrderVideos')
        return []

    gLogger.debug("Pulling out parent videos from follow up list...")
    parentIds = [v for i, v in enumerate(FollowUpIDList[0]) if FollowUpIDList[2][i] is None]
    nullCount = FollowUpIDList[2].count(None)
    FollowUpWatchLater = [[] for i in range(nullCount)]
    gLogger.debug("Entering loop to order follow up...")
    for index, id in enumerate(FollowUpIDList[2]):
        if id is None:
            gLogger.debug("Getting ID of Parent video...")
            idIndex = parentIds.index(FollowUpIDList[0][index])
        else:
            gLogger.debug("Getting ID of Child video...")
            idIndex = parentIds.index(id)
        gLogger.debug("Ordering follow up video...")
        FollowUpWatchLater[idIndex].append(videos[index])
    gLogger.debug("Returning follow up watch later...")
    return FollowUpWatchLater


def sortSeriesVideos(watchLaterList):
    """Sort videos within each series using natural sort."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Looping over series list...")
    for index in range(len(watchLaterList)):
        if not watchLaterList[index]:
            continue
        gLogger.debug("Natural sorting series sub list...")
        watchLaterList[index] = natsorted(watchLaterList[index], key=lambda x: x[6].rsplit("-", 1)[1] if '-' in x[6] else x[6])
    gLogger.debug("Returning sorted series list...")
    return watchLaterList


def sortSequentialVideo(watchLaterList):
    """Sort sequential videos by publish time."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Looping over sequential list...")
    for index in range(len(watchLaterList)):
        gLogger.debug("Sorting sequential sub list...")
        watchLaterList[index] = sorted(watchLaterList[index], key=lambda x: x[5])
    gLogger.debug("Returning sorted sequential list...")
    return watchLaterList


def sortWatchLater(watchLaterList, creatorDict, keywordDict, numSerKeywords, serKeywords, videoIDFollowUpList, sequentialCreators):
    """
    Main sorting function that orchestrates all sorting strategies.

    WatchLaterList structure:
    (0-position on yt, 1-playlist id for yt, 2-video id for yt, 3-duration in seconds,
     4-creator, 5-published time in unix time, 6-video title)
    """
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Initalizing variables...")
    videoCountThreshold = 50
    durationThreshold = 61 * 60  # 61 minutes in seconds
    sortedpriorityWatchLater = []
    periodicity = 2

    gLogger.debug("Determining priority threshold")
    if len(watchLaterList) > videoCountThreshold:
        priorityThreshold = 0
        gLogger.debug("Watch later is long! No threshold set")
    else:
        priorityThreshold = 1
        gLogger.debug("Watch later is short! Threshold set")

    # Step 1 - Get sublists
    gLogger.debug("Getting sub list (Priority, Follow-up, Series, and Sequential)...")
    gLogger.debug("Getting Priority list...")
    priorityWatchLater, workingWatchLater = getPriorityVideos(watchLaterList, creatorDict, keywordDict, priorityThreshold, durationThreshold)
    gLogger.debug("Priority list obtained! Getting Follow-up list...")
    if videoIDFollowUpList:
        followUpWatchLater = getFollowUpVideos(workingWatchLater, videoIDFollowUpList)
    else:
        followUpWatchLater = []
    gLogger.debug("Follow-up list obtained! Getting Sequential list...")
    sequentialWatchLater, workingWatchLater = getSequentialVideos(workingWatchLater, sequentialCreators, durationThreshold)
    gLogger.debug("Sequential list obtained! Getting Serialized list...")
    # seriesWatchLater, workingWatchLater = getSerializedVideos(workingWatchLater, numSerKeywords, serKeywords)
    seriesWatchLater = []
    gLogger.debug("Serialized list obtained! Moving to sorting...")

    # Step 2 - Sort segments
    gLogger.debug("Sorting Priority list...")
    for i in range(len(priorityWatchLater)):
        sortedpriorityWatchLater += sorted(priorityWatchLater[i], key=lambda x: x[5])
    gLogger.debug("Priority list sorted! Sorting  list...")
    sortedSequentialWatchLater = sortSequentialVideo(sequentialWatchLater)
    gLogger.debug("Sequential list sorted! Sorting Series list...")
    sortedSeriesWatchLater = sortSeriesVideos(seriesWatchLater)
    gLogger.debug("Sequential list sorted! Sorting rest of watch later list...")
    workingWatchLater.sort(key=lambda x: (x[3], x[5]))
    gLogger.debug("Rest of Watch Later list sorted!")

    # Step 3 - Merge sequential and series segments back together
    insertPositionList = []

    gLogger.debug("Entering loop to merging Series and Sequential lists together...")
    for index, item in enumerate(workingWatchLater):
        # Merge in sequential videos
        gLogger.debug("Looping over Sequential list...")
        for row in range(len(sortedSequentialWatchLater)):
            gLogger.debug("Checking if parent video duration is less than current item duration and they they are not same...")
            if sortedSequentialWatchLater[row] and sortedSequentialWatchLater[row][0][3] <= item[3] and sortedSequentialWatchLater[row][0][4] != item[4]:
                gLogger.debug("Parent Video is less! Reordering videos...")
                for v_idx, vid in enumerate(sortedSequentialWatchLater[row]):
                    gLogger.debug("Inserting video in list at given periodicity")
                    workingWatchLater.insert(index + v_idx * periodicity, vid)
                gLogger.debug("emptying row")
                sortedSequentialWatchLater[row] = []

        gLogger.debug("Looping over Series list...")
        for row in range(len(sortedSeriesWatchLater)):
            gLogger.debug("Checking if series video duration is less than current item duration and they they are not same...")
            if sortedSeriesWatchLater[row] and sortedSeriesWatchLater[row][0][3] <= item[3] and sortedSeriesWatchLater[row][0][4] != item[4]:
                gLogger.debug("It is! Reordering video...")
                workingWatchLater.insert(index, sortedSeriesWatchLater[row][0])
                gLogger.debug("Removing parent from Sequential list...")
                sortedSeriesWatchLater[row].pop(0)

    # Step 4 - Reorder follow up videos
    gLogger.debug("Entering loop to reorder follow-up videos in watch later list...")
    for row in followUpWatchLater:
        gLogger.debug("Determining position movement...")
        if len(row) > 3:
            positionMovement = 2
        else:
            positionMovement = 1
        gLogger.debug("Looping over each follow-up collection...")
        for i in range(len(row) - 1):
            gLogger.debug(f"Getting index of {i} video in collection...")
            predecentVideoPosition = workingWatchLater.index(row[i])
            gLogger.debug(f"Removing {i+1} video in collection from watch later list...")
            workingWatchLater.remove(row[i + 1])
            gLogger.debug(f"Inserting {i+1} video in collection...")
            workingWatchLater.insert(predecentVideoPosition + positionMovement, row[i + 1])

    # Step 5 - Combine priority and non-priority watch later
    gLogger.debug("returning combination of sorted Priority and working watch later")
    return sortedpriorityWatchLater + workingWatchLater
