"""
YouTube API operations for PlaylistPro.

This module handles all interactions with the YouTube Data API v3,
including authentication, playlist management, and video operations.
"""

from __future__ import annotations

import os
import pickle
import requests
from typing import Any, Optional

import googleapiclient.discovery as gacd
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .logging_config import getLogger
from .db import db
from .models import Creator
from .utils import checkType, durationString2Sec, dateString2EpochTime, sanitizeTitle, getCreatorDictionary

# Type aliases
VideoTuple = tuple[int, str, str, float, str, float, str]  # (position, playlistID, videoID, duration, creator, publishedTime, title)
ClientConfig = dict[str, Any]  # OAuth client configuration dictionary

# Maximum retries for API errors before failing
MAX_RETRIES = 3

# Cached YouTube client
_youtube_client = None


# OAuth scopes required for YouTube API
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtubepartner"
]


def get_youtube_client(port_number: int, client_config: ClientConfig, force_refresh: bool = False) -> gacd.Resource:
    """
    Get a YouTube API client, with optional caching.

    Args:
        port_number: Port for OAuth flow
        client_config: OAuth config dict (from OAuthConfig.to_client_secret_dict())
        force_refresh: If True, create a new client even if cached

    Returns:
        YouTube API client resource
    """
    global _youtube_client
    gLogger = getLogger()

    if _youtube_client is not None and not force_refresh:
        return _youtube_client

    credentials = getCredentials(port_number, client_config)
    _youtube_client = gacd.build("youtube", "v3", credentials=credentials)
    gLogger.info("YouTube API client initialized")

    return _youtube_client


def getCredentials(portNumber: int, clientConfig: ClientConfig) -> Credentials:
    """Get or refresh OAuth2 credentials for YouTube API."""
    gLogger = getLogger()
    credentials: Optional[Credentials] = None

    # Load existing credentials if available
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)

    # Refresh or fetch new credentials if needed
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            gLogger.info("Refreshing expired OAuth token")
            credentials.refresh(Request())
            saveCredentails(credentials)
        else:
            gLogger.info("Initiating new OAuth flow")
            flow = getFlowObject(clientConfig)
            flow.run_local_server(
                port=portNumber,
                prompt="consent",
                authorization_prompt_message=""
            )
            credentials = flow.credentials
            saveCredentails(credentials)

    return credentials


def getFlowObject(clientConfig: ClientConfig) -> InstalledAppFlow:
    """Create an OAuth2 flow object for authentication.

    Args:
        clientConfig: OAuth config dict (kept in memory, not written to disk)
    """
    return InstalledAppFlow.from_client_config(
        clientConfig,
        scopes=YOUTUBE_SCOPES
    )


def saveCredentails(credentials: Credentials) -> None:
    """Save OAuth2 credentials to a pickle file."""
    with open("token.pickle", "wb") as f:
        pickle.dump(credentials, f)


def getWatchLater(youtube, playlistID, nextPageBoolean):
    """Fetch the watch later playlist from YouTube."""
    gLogger = getLogger()
    nextPageToken = None
    numberRequest = 0
    watchLaterList = []
    errorCount = 0

    while True:
        pl_request = youtube.playlistItems().list(
            part="contentDetails, snippet",
            playlistId=playlistID,
            maxResults=50,
            pageToken=nextPageToken
        )
        try:
            pl_response = pl_request.execute()
        except Exception as e:
            gLogger.error("Failed to fetch playlist", playlist_id=playlistID, error=str(e))
            raise RuntimeError(e)

        numberRequest += 1

        for item in pl_response["items"]:
            video = (item["snippet"]["position"], item["id"], item["contentDetails"]["videoId"])

            vid_request = youtube.videos().list(
                part="contentDetails, snippet",
                id=item["contentDetails"]["videoId"],
            )
            try:
                vid_response = vid_request.execute()
            except Exception as e:
                errorCount += 1
                if errorCount > MAX_RETRIES:
                    gLogger.error("Max retries exceeded fetching video details",
                                  video_id=item["contentDetails"]["videoId"], error=str(e))
                    raise RuntimeError(e)
                gLogger.warning("Retrying video fetch",
                                video_id=item["contentDetails"]["videoId"],
                                attempt=errorCount, error=str(e))
                continue

            numberRequest += 1

            for vid in vid_response["items"]:
                duration = durationString2Sec(vid["contentDetails"]["duration"])
                utcPublishedTime = dateString2EpochTime(vid["snippet"]["publishedAt"])
                videoSnippet = (duration, vid["snippet"]["channelTitle"], utcPublishedTime, vid["snippet"]["title"])
                video = video + videoSnippet
                watchLaterList.append(video)

        if nextPageBoolean:
            nextPageToken = pl_response.get('nextPageToken')

        if not nextPageToken:
            break

    gLogger.info("Fetched watch later playlist",
                 video_count=len(watchLaterList), api_requests=numberRequest)
    return watchLaterList, numberRequest


def updatePlaylist(watchLater, sortedWatchLater, youtube, playlistID):
    """Update the YouTube playlist order to match the sorted order."""
    gLogger = getLogger()
    checkType(watchLater, list)
    checkType(sortedWatchLater, list)
    checkType(playlistID, str)

    if len(watchLater) != len(sortedWatchLater):
        gLogger.error("Playlist length mismatch",
                      original=len(watchLater), sorted=len(sortedWatchLater))
        raise ValueError("Lists must have the same size")

    numOperations = 0
    errorCount = 0

    for x in range(len(watchLater)):
        if watchLater[x] != sortedWatchLater[x]:
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
            try:
                update_request.execute()
                numOperations += 1
                watchLater.insert(x, watchLater.pop(watchLater.index(sortedWatchLater[x])))
            except Exception as e:
                errorCount += 1
                if errorCount > MAX_RETRIES:
                    gLogger.error("Max retries exceeded updating playlist",
                                  video_id=sortedWatchLater[x][2], error=str(e))
                    raise RuntimeError(e)
                gLogger.warning("Failed to move video",
                                video_id=sortedWatchLater[x][2],
                                position=x, error=str(e))

    gLogger.info("Playlist updated", moves=numOperations, errors=errorCount)
    return numOperations, watchLater


def findChannelID(creator, youtube):
    """Search for a YouTube channel ID by creator name."""
    gLogger = getLogger()
    checkType(creator, str)
    checkType(youtube, gacd.Resource)

    ch_request = youtube.search().list(
        part="snippet",
        type="channel",
        q=creator
    )
    try:
        ch_response = ch_request.execute()
    except Exception as e:
        gLogger.error("Failed to search for channel", creator=creator, error=str(e))
        raise RuntimeError(e)

    try:
        return ch_response["items"][0]["id"]["channelId"]
    except (IndexError, KeyError):
        gLogger.warning("Channel not found", creator=creator)
        return ""


def getVideoYT(youtube, videoID):
    """Get video details from YouTube API."""
    gLogger = getLogger()

    vid_request = youtube.videos().list(
        part="contentDetails, snippet",
        id=videoID,
    )
    try:
        vid_response = vid_request.execute()
    except Exception as e:
        gLogger.error("Failed to fetch video", video_id=videoID, error=str(e))
        raise RuntimeError(e)

    vid = vid_response["items"]
    return {
        "duration": vid["contentDetails"]["duration"],
        "creator": vid["snippet"]["channelTitle"],
        "published": vid["snippet"]["publishedAt"],
        "title": vid["snippet"]["title"],
        "description": vid["snippet"]["description"],
        "tags": vid["snippet"]["tag"],
        "categoryIDs": vid["snippet"]["categoryId properties"]
    }


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
            sub_response = sub_request.execute()
        except Exception as e:
            gLogger.error("Failed to fetch subscriptions", error=str(e))
            raise RuntimeError(e)

        subs += sub_response["items"]
        nextPageToken = sub_response.get('nextPageToken')

        if not nextPageToken:
            break

    gLogger.info("Fetched subscriptions", count=len(subs))
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
        vid_request.execute()
        gLogger.info("Video inserted into playlist",
                     video_id=videoID, playlist_id=playlistID, position=position)
    except Exception as e:
        gLogger.error("Failed to insert video",
                      video_id=videoID, playlist_id=playlistID, error=str(e))
        raise RuntimeError(e)


def storeSubscripton(subs, youtube):
    """Store subscription data in the database."""
    gLogger = getLogger()
    creatorDict = getCreatorDictionary([], youtube)[0]
    lastID = max(creatorDict.values()) if creatorDict else 0
    added = 0

    for sub in subs:
        creator_name = sanitizeTitle(sub["snippet"]["title"])
        if creator_name not in creatorDict.keys():
            channel_id = sub["snippet"]["resourceId"]["channelId"]
            insertCreatorsDB(creator_name, channel_id=channel_id, subscribedBool=True)
            creatorDict[creator_name] = lastID + 1
            lastID += 1
            added += 1

    if added:
        gLogger.info("Stored new subscriptions", count=added)


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
        gLogger.debug("Creator added", name=creator, channel_id=channel_id)
    except Exception as e:
        db.session.rollback()
        gLogger.error("Failed to insert creator", name=creator, error=str(e))


def pubhubsubhubPost(mode, topic, callback):
    """Subscribe to PubSubHubbub notifications for YouTube channels."""
    gLogger = getLogger()
    url = f'https://pubsubhubbub.appspot.com/subscribe?hub.callback={callback}&hub.mode={mode}&hub.verify=async&hub.lease=2629800&hub.topic={topic}'
    response = requests.post(url)
    if response.status_code != 200:
        gLogger.warning("PubSubHubbub request failed",
                        mode=mode, status=response.status_code)


def subscribeCreators():
    """Subscribe to PubSubHubbub notifications for all subscribed creators."""
    gLogger = getLogger()
    subscribed_creators = Creator.query.filter_by(subscribed=True).all()

    count = 0
    for creator in subscribed_creators:
        if creator.channelId:
            topic = f'https://www.youtube.com/feeds/videos.xml?channel_id={creator.channelId}'
            pubhubsubhubPost('subscribe', topic, 'http://youtube.lukasarmstrong.io/webhook')
            count += 1

    gLogger.info("Subscribed to creator notifications", count=count)
