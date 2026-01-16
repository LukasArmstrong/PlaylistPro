"""
SQLAlchemy models for PlaylistPro.

This module defines the database schema as Python classes.
"""

from .db import db


class Creator(db.Model):
    """YouTube channel/creator with priority settings."""

    __tablename__ = 'Creators'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creators = db.Column(db.String(255), nullable=False)
    priorityScore = db.Column(db.Integer, default=0)
    channelId = db.Column(db.String(100))
    subscribed = db.Column(db.Boolean, default=False)
    unconditional = db.Column(db.Boolean, default=False)
    sequentialVideos = db.Column(db.Boolean, default=False)

    # Relationships
    sequential_setting = db.relationship('SequentialCreator', backref='creator', uselist=False, cascade='all, delete-orphan')
    stats = db.relationship('WatchLaterCreatorStat', backref='creator', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Creator {self.creators}>'


class Keyphrase(db.Model):
    """Keywords/phrases with priority scores for video matching."""

    __tablename__ = 'Keyphrases'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phrase = db.Column(db.String(255), nullable=False, unique=True)
    score = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Keyphrase {self.phrase}>'


class WatchLaterVideo(db.Model):
    """Video in the watch later playlist."""

    __tablename__ = 'WatchLaterList'

    # Use videoID as primary key - matches existing MariaDB schema
    # and avoids RETURNING clause issues
    position = db.Column(db.Integer, nullable=False)
    playlistID = db.Column(db.String(100))
    videoID = db.Column(db.String(50), primary_key=True, nullable=False)
    duration = db.Column(db.Float)
    creator = db.Column(db.String(255))
    publishedTimeUTC = db.Column(db.BigInteger)
    title = db.Column(db.String(500))

    def to_tuple(self):
        """Convert to tuple format for compatibility with existing sorting code."""
        return (
            self.position,
            self.playlistID,
            self.videoID,
            self.duration,
            self.creator,
            self.publishedTimeUTC,
            self.title
        )

    @classmethod
    def from_tuple(cls, video_tuple):
        """Create instance from tuple format."""
        return cls(
            position=video_tuple[0],
            playlistID=video_tuple[1],
            videoID=video_tuple[2],
            duration=video_tuple[3],
            creator=video_tuple[4],
            publishedTimeUTC=video_tuple[5],
            title=video_tuple[6]
        )

    def __repr__(self):
        return f'<WatchLaterVideo {self.title[:30]}...>'


class OrderVideo(db.Model):
    """Video follow-up/sequel relationships."""

    __tablename__ = 'OrderVideos'

    # Use videoID as primary key - matches existing MariaDB schema
    videoID = db.Column(db.String(50), primary_key=True, nullable=False)
    predecentVideoID = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<OrderVideo {self.videoID}>'


class SequentialCreator(db.Model):
    """Creators whose videos should be watched in order."""

    __tablename__ = 'SequentialCreators'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creatorId = db.Column(db.Integer, db.ForeignKey('Creators.id'), nullable=False)
    DurationExpection = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<SequentialCreator {self.creatorId}>'


class WatchLaterStat(db.Model):
    """Aggregate statistics for watch later playlist snapshots."""

    __tablename__ = 'WatchLaterStats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Date = db.Column(db.String(50), nullable=False)
    Length = db.Column(db.Integer)
    TotalDuration = db.Column(db.Float)
    AverageDuration = db.Column(db.Float)
    MedianDuration = db.Column(db.Float)
    StdvDuration = db.Column(db.Float)
    VarianceDuration = db.Column(db.Float)
    NumUniqueCreators = db.Column(db.Integer)

    def __repr__(self):
        return f'<WatchLaterStat {self.Date}>'


class WatchLaterCreatorStat(db.Model):
    """Per-creator statistics from watch later playlist."""

    __tablename__ = 'WatchLaterCreatorStats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.String(50), nullable=False)
    CreatorID = db.Column(db.Integer, db.ForeignKey('Creators.id'), nullable=False)
    Frequency = db.Column(db.Integer)
    Duration = db.Column(db.Float)
    OldestVideo = db.Column(db.BigInteger)
    LongestVideo = db.Column(db.Float)
    AverageUnixAge = db.Column(db.Float)
    FrequencyPercentage = db.Column(db.Float)
    DurationPercentage = db.Column(db.Float)

    def __repr__(self):
        return f'<WatchLaterCreatorStat {self.date} - Creator {self.CreatorID}>'


class QuotaLimit(db.Model):
    """YouTube API quota tracking per project per day."""

    __tablename__ = 'QuotaLimit'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.String(20), nullable=False)
    Amount = db.Column(db.Integer, default=0)
    projectID = db.Column(db.Integer, nullable=False)

    # Unique constraint on date + projectID
    __table_args__ = (
        db.UniqueConstraint('date', 'projectID', name='unique_date_project'),
    )

    def __repr__(self):
        return f'<QuotaLimit {self.date} - Project {self.projectID}>'
