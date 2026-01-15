"""
Database operations for PlaylistPro using SQLAlchemy ORM.

This module provides database helper functions that work with the
SQLAlchemy models. For most operations, you should import and use
the models directly.
"""

from .db import db
from .models import (
    Creator, Keyphrase, WatchLaterVideo, OrderVideo,
    SequentialCreator, WatchLaterStat, WatchLaterCreatorStat, QuotaLimit
)
from .logging_config import getLogger
from .utils import sanitizeTitle


def get_creators_dict():
    """Get a dictionary mapping creator names to priority scores."""
    gLogger = getLogger()
    gLogger.debug("Fetching creators dictionary...")
    creators = Creator.query.all()
    return {c.creators: c.priorityScore for c in creators}


def get_keyphrases_dict():
    """Get a dictionary mapping phrases to scores."""
    gLogger = getLogger()
    gLogger.debug("Fetching keyphrases dictionary...")
    phrases = Keyphrase.query.all()
    return {p.phrase: p.score for p in phrases}


def get_sequential_creators_dict():
    """Get a dictionary of sequential creators with duration exceptions."""
    gLogger = getLogger()
    gLogger.debug("Fetching sequential creators...")
    results = db.session.query(
        Creator.creators,
        SequentialCreator.DurationExpection
    ).join(
        SequentialCreator,
        Creator.id == SequentialCreator.creatorId
    ).all()
    return dict(results)


def get_order_videos_list():
    """Get the follow-up video relationships as lists."""
    gLogger = getLogger()
    gLogger.debug("Fetching order videos...")
    videos = OrderVideo.query.all()
    if not videos:
        return []
    ids = [v.id for v in videos]
    video_ids = [v.videoID for v in videos]
    predecent_ids = [v.predecentVideoID for v in videos]
    return [ids, video_ids, predecent_ids]


def clear_watch_later():
    """Delete all records from WatchLaterList table."""
    gLogger = getLogger()
    gLogger.debug("Clearing WatchLaterList table...")
    WatchLaterVideo.query.delete()
    db.session.commit()
    gLogger.debug("WatchLaterList cleared!")


def clear_order_videos():
    """Delete all records from OrderVideos table."""
    gLogger = getLogger()
    gLogger.debug("Clearing OrderVideos table...")
    OrderVideo.query.delete()
    db.session.commit()
    gLogger.debug("OrderVideos cleared!")


def store_watch_later(watchlater_tuples):
    """
    Store the watch later list in the database.

    Args:
        watchlater_tuples: List of tuples in format:
            (position, playlistID, videoID, duration, creator, publishedTimeUTC, title)
    """
    gLogger = getLogger()
    gLogger.debug("Entering...")

    # Clear existing data
    clear_watch_later()
    gLogger.debug("WatchLaterList cleared!")

    gLogger.debug("Filling new list...")
    for video_tuple in watchlater_tuples:
        video = WatchLaterVideo(
            position=video_tuple[0],
            playlistID=video_tuple[1],
            videoID=video_tuple[2],
            duration=video_tuple[3],
            creator=video_tuple[4],
            publishedTimeUTC=video_tuple[5],
            title=sanitizeTitle(video_tuple[6])
        )
        db.session.add(video)

    db.session.commit()
    gLogger.debug("Watch Later stored in database!")


def get_watch_later_videos():
    """Get all watch later videos as a list of tuples."""
    gLogger = getLogger()
    gLogger.debug("Fetching watch later videos...")
    videos = WatchLaterVideo.query.order_by(WatchLaterVideo.position).all()
    return [v.to_tuple() for v in videos]


def get_creator_by_name(name):
    """Get a creator by name."""
    return Creator.query.filter_by(creators=name).first()


def get_creator_id_map():
    """Get a dictionary mapping creator names to IDs."""
    gLogger = getLogger()
    gLogger.debug("Fetching creator ID map...")
    creators = Creator.query.all()
    return {c.creators: c.id for c in creators}


def add_creator(name, priority_score=0, channel_id=None, subscribed=False,
                unconditional=False, sequential=False):
    """Add a new creator to the database."""
    gLogger = getLogger()
    gLogger.debug(f"Adding creator: {name}")

    creator = Creator(
        creators=name,
        priorityScore=priority_score,
        channelId=channel_id,
        subscribed=subscribed,
        unconditional=unconditional,
        sequentialVideos=sequential
    )
    db.session.add(creator)
    db.session.commit()
    gLogger.debug(f"Creator {name} added with ID {creator.id}")
    return creator


def add_watch_later_stat(datetime_str, length, total_duration, avg_duration,
                         median_duration, stdv_duration, variance_duration,
                         num_unique_creators):
    """Add a watch later statistics record."""
    gLogger = getLogger()
    gLogger.debug("Adding watch later stats...")

    stat = WatchLaterStat(
        Date=datetime_str,
        Length=length,
        TotalDuration=total_duration,
        AverageDuration=avg_duration,
        MedianDuration=median_duration,
        StdvDuration=stdv_duration,
        VarianceDuration=variance_duration,
        NumUniqueCreators=num_unique_creators
    )
    db.session.add(stat)
    db.session.commit()
    gLogger.debug("Watch later stats added!")


def add_creator_stat(datetime_str, creator_id, frequency, duration, oldest_video,
                     longest_video, avg_unix_age, freq_pct, duration_pct):
    """Add a per-creator statistics record."""
    gLogger = getLogger()
    gLogger.debug(f"Adding creator stat for creator {creator_id}...")

    stat = WatchLaterCreatorStat(
        date=datetime_str,
        CreatorID=creator_id,
        Frequency=frequency,
        Duration=duration,
        OldestVideo=oldest_video,
        LongestVideo=longest_video,
        AverageUnixAge=avg_unix_age,
        FrequencyPercentage=freq_pct,
        DurationPercentage=duration_pct
    )
    db.session.add(stat)
    db.session.commit()
    gLogger.debug("Creator stat added!")


def get_subscribed_channel_ids():
    """Get channel IDs for all subscribed creators."""
    gLogger = getLogger()
    gLogger.debug("Fetching subscribed channel IDs...")
    creators = Creator.query.filter_by(subscribed=True).all()
    return [c.channelId for c in creators if c.channelId]


# ============================================================
# Backwards compatibility aliases
# These maintain the old API while using SQLAlchemy underneath
# ============================================================

def storeWatchLaterDB(watchlater):
    """Backwards compatible alias for store_watch_later."""
    store_watch_later(watchlater)


def clearTableDB(table_name):
    """Backwards compatible function to clear a table by name."""
    gLogger = getLogger()
    gLogger.debug(f"Clearing table: {table_name}")

    table_map = {
        'WatchLaterList': WatchLaterVideo,
        'OrderVideos': OrderVideo,
        'Creators': Creator,
        'Keyphrases': Keyphrase,
        'WatchLaterStats': WatchLaterStat,
        'WatchLaterCreatorStats': WatchLaterCreatorStat,
        'QuotaLimit': QuotaLimit,
        'SequentialCreators': SequentialCreator,
    }

    model = table_map.get(table_name)
    if model:
        model.query.delete()
        db.session.commit()
        gLogger.debug(f"Table {table_name} cleared!")
    else:
        gLogger.warning(f"Unknown table: {table_name}")


# Legacy function stubs - these are no longer needed with Flask-SQLAlchemy
def getDataBaseConnection(usr, pswd, host, port, db_name):
    """No-op: Database connection handled by Flask-SQLAlchemy."""
    gLogger = getLogger()
    gLogger.debug("getDataBaseConnection called - handled by Flask-SQLAlchemy")


def closeDBConnection():
    """No-op: Connection management handled by Flask-SQLAlchemy."""
    gLogger = getLogger()
    gLogger.debug("closeDBConnection called - handled by Flask-SQLAlchemy")


CloseDBconnnection = closeDBConnection  # Backwards compatibility alias
