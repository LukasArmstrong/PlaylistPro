"""
YouTube API operations for PlaylistPro.

This module handles all interactions with the YouTube Data API v3,
including authentication, playlist management, and video operations.
"""

import os
import pickle
import requests
import googleapiclient.discovery as gacd
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from .logging_config import getLogger
from .db import db
from .models import Creator
from .utils import checkType, durationString2Sec, dateString2EpochTime, sanitizeTitle, getCreatorDictionary

# Global strike counter
gNumStrikes = 3


def getCredentials(portNumber, clientSecretFile):
    """Get or refresh OAuth2 credentials for YouTube API."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    credentials = None
    # token.pickle stores the user's credentials from previously successful logins
    gLogger.debug("Checking if token pickle exist...")
    if os.path.exists("token.pickle"):
        gLogger.debug("Loading credentials token from file...")
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)
        gLogger.debug("credentials token loaded")
    # If there is no valid credentials available, then either refresh the token or log in.
    gLogger.debug("Checking if credential token is valid...")
    if not credentials or not credentials.valid:
        gLogger.debug("Credential token not valid. Checking if expired...")
        if credentials and credentials.expired and credentials.refresh_token:
            gLogger.debug("Credential token expired and can be refreshed...")
            gLogger.debug("Refreshing access token...")
            credentials.refresh(Request())
            gLogger.debug("Token refreshed!")
            saveCredentails(credentials)
        else:
            gLogger.debug("Credential token expired and can _not_ be refreshed...")
            gLogger.debug("Fetching new token...")
            flow = getFlowObject(clientSecretFile)
            gLogger.debug("Flow server created. Running...")
            flow.run_local_server(
                port=portNumber,
                prompt="consent",
                authorization_prompt_message=""
            )
            gLogger.debug("Obtaining credential token...")
            credentials = flow.credentials
            gLogger.debug("Credential token obtained!")
            saveCredentails(credentials)
    gLogger.debug("Returning credentials...")
    return credentials


def getFlowObject(clientSecretFile):
    """Create an OAuth2 flow object for authentication."""
    gLogger = getLogger()
    gLogger.debug("Enter...")
    gLogger.debug("Creating Flow object...")
    return InstalledAppFlow.from_client_secrets_file(
        clientSecretFile,
        scopes=["https://www.googleapis.com/auth/youtube",
                "https://www.googleapis.com/auth/youtube.force-ssl",
                "https://www.googleapis.com/auth/youtubepartner"]
    )


def saveCredentails(credentials):
    """Save OAuth2 credentials to a pickle file."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    # Save credentials for the next run
    with open("token.pickle", "wb") as f:
        gLogger.debug("Saving credentials for future use...")
        pickle.dump(credentials, f)
    gLogger.debug("Credentails Saved!")
    gLogger.debug("Leaving...")


def getWatchLater(youtube, playlistID, nextPageBoolean):
    """Fetch the watch later playlist from YouTube."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Initalizing variables...")
    nextPageToken = None
    numberRequest = 0
    watchLaterList = []
    gLogger.debug("Getting List...")
    while True:
        # Watch Later isn't available through the API, so have to use playlist as pseudo watch later list
        gLogger.debug("Creating youtube playlist request...")
        pl_request = youtube.playlistItems().list(
            part="contentDetails, snippet",
            playlistId=playlistID,
            maxResults=50,  # Youtube API won't allow more then 50 results per request
            pageToken=nextPageToken
        )
        try:
            gLogger.debug("Executing youtube playlist request...")
            pl_response = pl_request.execute()
            gLogger.debug("Playlist request executed!")
        except Exception as e:
            gLogger.error(f"Error executing youtube playlist request. Type: {type(e)} Arguements:{e}")
            raise RuntimeError(e)
        numberRequest += 1  # Tracking quota usage
        gLogger.debug("Unpacking youtube playlist response...")
        videoErrorCount = 0
        for item in pl_response["items"]:
            video = (item["snippet"]["position"], item["id"], item["contentDetails"]["videoId"])
            # Need more data to sort
            gLogger.debug("Creating youtube video request...")
            vid_request = youtube.videos().list(
                part="contentDetails, snippet",
                id=item["contentDetails"]["videoId"],
            )
            gLogger.debug("Executing youtube video request...")
            try:
                vid_response = vid_request.execute()
                gLogger.debug("Video request executed!")
            except Exception as e:
                videoErrorCount += 1
                if videoErrorCount > gNumStrikes:
                    gLogger.error(f"Error executing youtube video request. All Strikes Used. Type: {type(e)} Arguements:{e}")
                    raise RuntimeError(e)
                else:
                    gLogger.warning(f"Unexcepted issue executing youtube video request. Strike: {videoErrorCount} Type: {type(e)} Arguements:{e}")
                    pass
            numberRequest += 1  # Tracking quota usage
            gLogger.debug("Unpacking youtube video response...")
            videoSnippet = ()
            for vid in vid_response["items"]:
                gLogger.debug("Converting video duration to more useful format...")
                duration = durationString2Sec(vid["contentDetails"]["duration"])
                gLogger.debug("Converting video published date to more useful format...")
                utcPublishedTime = dateString2EpochTime(vid["snippet"]["publishedAt"])
                gLogger.debug("Video duration and publish time converted! Storing in tuple...")
                videoSnippet = (duration, vid["snippet"]["channelTitle"], utcPublishedTime, vid["snippet"]["title"])
            gLogger.debug("Combining video tuples...")
            if videoSnippet:
                video = video + videoSnippet
                gLogger.debug("Adding video tuple to watch later list...")
                watchLaterList.append(video)
        gLogger.debug("Checking if should get next page...")
        if nextPageBoolean:
            gLogger.debug("Getting next page token...")
            nextPageToken = pl_response.get('nextPageToken')

        gLogger.debug("Checking if next page token exist...")
        if not nextPageToken:
            gLogger.debug("Next page token doesn't exist, breaking out of loop...")
            break
    gLogger.debug("Returning watch later list and number of requests...")
    return watchLaterList, numberRequest


def updatePlaylist(watchLater, sortedWatchLater, youtube, playlistID):
    """Update the YouTube playlist order to match the sorted order."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking types...")
    checkType(watchLater, list)
    checkType(sortedWatchLater, list)
    checkType(playlistID, str)
    numOperations = 0
    videoErrorCount = 0
    gLogger.debug("Initialized variables...", numOperations=numOperations, videoErrorCount=0)
    gLogger.debug("Checking length of watch later")
    if len(watchLater) != len(sortedWatchLater):
        gLogger.error("Length of watch later lists don't match!", watchLater=watchLater, sortedWatchLater=sortedWatchLater)
        raise ValueError("Lists must have the same size")
    gLogger.debug("Entering loop for watch later...")
    for x in range(len(watchLater)):
        gLogger.debug("Checking if video position on YT wach later same as sorted watch later...")
        if watchLater[x] != sortedWatchLater[x]:  # naive approach to save on quota
            gLogger.debug("Creating update request..")
            update_request = youtube.playlistItems().update(
                part="snippet",
                body={
                    "id": sortedWatchLater[x][1],
                    "snippet": {
                        "playlistId": playlistID,
                        "position": x,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": sortedWatchLater[x][2],
                        }
                    }
                }
            )
            gLogger.debug("Attempting to execute update request...")
            try:
                update_response = update_request.execute()
                gLogger.debug("Execution Successful!")
                try:
                    gLogger.debug("incrementing num of operations...")
                    numOperations += 1
                    gLogger.debug("Moving video record to position in sorted list")
                    watchLater.insert(x, watchLater.pop(watchLater.index(sortedWatchLater[x])))
                except Exception as e:
                    gLogger.error(f"Unexpect error updating watch later list! Type: {type(e)} Arguements:{e}")
            except Exception as e:
                videoErrorCount += 1
                if videoErrorCount > gNumStrikes:
                    gLogger.error(f"Error executing youtube update request. All Strikes Used. Type: {type(e)} Arguements:{e}")
                    raise RuntimeError(e)
                else:
                    gLogger.warning(f"Unexcepted issue executing youtube update request. Strike: {videoErrorCount} Type: {type(e)} Arguements:{e}")
                    pass
                gLogger.error(f"Couldn't update {x[6]}. Type: {type(e)} Arguements:{e}")
    gLogger.debug(f"Number of operations preformed: {numOperations}")
    gLogger.debug("Leaving...")
    return numOperations, watchLater


def findChannelID(creator, youtube):
    """Search for a YouTube channel ID by creator name."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Types...")
    checkType(creator, str)
    checkType(youtube, gacd.Resource)
    gLogger.debug("Creating channel request...")
    ch_request = youtube.search().list(
        part="snippet",
        type="channel",
        q=creator
    )
    try:
        gLogger.debug("Executing youtube channel request...")
        ch_response = ch_request.execute()
        gLogger.debug("Channel request executed!")
    except Exception as e:
        gLogger.error(f"Error executing youtube channel request. Type: {type(e)} Arguements:{e}")
        raise RuntimeError(e)
    try:
        id = ch_response["items"][0]["id"]["channelId"]
    except Exception:
        id = ""
        gLogger.info(f"Couldn't find channel ID for {creator}")
    gLogger.debug("Returning channel id")
    return id


def getVideoYT(youtube, videoID):
    """Get video details from YouTube API."""
    gLogger = getLogger()
    gLogger.debug("Enter...")
    videoErrorCount = 0
    videoDetails = []
    gLogger.debug("Initialized variables...", videoErrorCount=videoErrorCount)
    gLogger.debug("Creating YT api video request...")
    vid_request = youtube.videos().list(
        part="contentDetails, snippet",
        id=videoID,
    )
    gLogger.debug("Attempting youtube video request...")
    try:
        vid_response = vid_request.execute()
        gLogger.debug("Youtube Video Request executed successfully!")
    except Exception as e:
        videoErrorCount += 1
        if videoErrorCount > gNumStrikes:
            gLogger.error(f"Error executing youtube video request. All Strikes Used. Type: {type(e)} Arguements:{e}")
            raise RuntimeError(e)
        else:
            gLogger.warning(f"Unexcepted issue executing youtube video request. Strike: {videoErrorCount} Type: {type(e)} Arguements:{e}")
            pass
    gLogger.debug("Unpacking video response... Creating Dictionary...")
    vid = vid_response["items"]
    videoDetails = {
        "duration": vid["contentDetails"]["duration"],
        "creator": vid["snippet"]["channelTitle"],
        "published": vid["snippet"]["publishedAt"],
        "title": vid["snippet"]["title"],
        "description": vid["snippet"]["description"],
        "tags": vid["snippet"]["tag"],
        "categoryIDs": vid["snippet"]["categoryId properties"]
    }
    gLogger.debug("Video Dictonary Created!")
    gLogger.debug("Leaving...")
    return videoDetails


def getSubscriptions(youtube, mine=True, channel_id=None):
    """Get the user's YouTube subscriptions."""
    gLogger = getLogger()
    nextPageToken = None
    subs = []
    while True:
        sub_request = youtube.subscriptions().list(
            part="snippet",
            mine=mine,
            channelId=channel_id,
            maxResults=50,
            pageToken=nextPageToken
        )
        try:
            gLogger.debug("Executing youtube subscription request...")
            sub_response = sub_request.execute()
            gLogger.debug("Subscription request executed!")
        except Exception as e:
            gLogger.error(f"Error executing youtube playlist request. Type: {type(e)} Arguements:{e}")
            raise RuntimeError(e)
        subs += sub_response["items"]
        gLogger.debug("Getting next page token...")
        nextPageToken = sub_response.get('nextPageToken')

        gLogger.debug("Checking if next page token exist...")
        if not nextPageToken:
            gLogger.debug("Next page token doesn't exist, breaking out of loop...")
            break
    return subs


def insertVideoYT(youtube, playlistID, videoID, position=0):
    """Insert a video into a YouTube playlist."""
    gLogger = getLogger()
    vid_request = youtube.playlistItems.insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlistID,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": videoID
                },
                "position": position
            }
        }
    )
    try:
        gLogger.debug("Executing youtube video insert request...")
        vid_response = vid_request.execute()
        gLogger.debug("Request Succeed! Video inserted!")
    except Exception as e:
        gLogger.error(f"Error executing youtube video insert request. Type: {type(e)} Arguements:{e}")
        raise RuntimeError(e)


def storeSubscripton(subs, youtube):
    """Store subscription data in the database."""
    gLogger = getLogger()
    creatorDict = getCreatorDictionary([], youtube)[0]
    lastID = max(creatorDict.values()) if creatorDict else 0

    for sub in subs:
        creator_name = sanitizeTitle(sub["snippet"]["title"])
        if creator_name not in creatorDict.keys():
            channel_id = sub["snippet"]["resourceId"]["channelId"]
            insertCreatorsDB(creator_name, channel_id=channel_id, subscribedBool=True)
            creatorDict[creator_name] = lastID + 1
            lastID += 1


def insertCreatorsDB(creator, priorirtyScore=0, channel_id=None, subscribedBool=False,
                     unconditionalBool=False, sequentialBoolInt=False, youtube=None):
    """Insert a new creator into the database."""
    gLogger = getLogger()

    if not channel_id and youtube:
        channel_id = findChannelID(creator, youtube)

    try:
        new_creator = Creator(
            creators=creator,
            priorityScore=priorirtyScore,
            channelId=channel_id,
            subscribed=subscribedBool,
            unconditional=unconditionalBool,
            sequentialVideos=sequentialBoolInt
        )
        db.session.add(new_creator)
        db.session.commit()
        gLogger.debug(f"Creator {creator} inserted successfully")
    except Exception as e:
        db.session.rollback()
        gLogger.error(f"Error inserting creator: {e}")


def pubhubsubhubPost(mode, topic, callback):
    """Subscribe to PubSubHubbub notifications for YouTube channels."""
    url = 'https://pubsubhubbub.appspot.com/subscribe?hub.callback=' + callback + '&hub.mode=' + mode + '&hub.verify=async&hub.lease=2629800&hub.topic=' + topic
    response = requests.post(url)
    print(response.text)


def subscribeCreators():
    """Subscribe to PubSubHubbub notifications for all subscribed creators."""
    gLogger = getLogger()
    gLogger.debug("Fetching subscribed creators...")

    # Query subscribed creators using ORM
    subscribed_creators = Creator.query.filter_by(subscribed=True).all()

    for creator in subscribed_creators:
        if creator.channelId:
            topic = f'https://www.youtube.com/feeds/videos.xml?channel_id={creator.channelId}'
            pubhubsubhubPost('subscribe', topic, 'http://youtube.lukasarmstrong.io/webhook')
