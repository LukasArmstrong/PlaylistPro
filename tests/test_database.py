"""
Tests for pywertube database operations.
"""

import pytest
from pywertube import db
from pywertube.models import Creator, Keyphrase, WatchLaterVideo, QuotaLimit
from pywertube.database import (
    get_creators_dict,
    get_keyphrases_dict,
    store_watch_later,
    get_watch_later_videos,
    add_creator,
    clear_watch_later,
)


class TestCreatorOperations:
    """Tests for creator database operations."""

    def test_add_creator(self, db_session):
        """Add a new creator to the database."""
        creator = add_creator(
            name='Test Creator',
            priority_score=10,
            channel_id='UC123456'
        )

        assert creator.id is not None
        assert creator.creators == 'Test Creator'
        assert creator.priorityScore == 10
        assert creator.channelId == 'UC123456'

    def test_get_creators_dict(self, db_session):
        """Get creators as a dictionary."""
        # Add some creators
        add_creator('Creator A', priority_score=5)
        add_creator('Creator B', priority_score=10)
        add_creator('Creator C', priority_score=0)

        result = get_creators_dict()

        assert result['Creator A'] == 5
        assert result['Creator B'] == 10
        assert result['Creator C'] == 0

    def test_get_creators_dict_empty(self, db_session):
        """Return empty dict when no creators."""
        result = get_creators_dict()
        assert result == {}


class TestKeyphraseOperations:
    """Tests for keyphrase database operations."""

    def test_get_keyphrases_dict(self, db_session):
        """Get keyphrases as a dictionary."""
        # Add some keyphrases directly
        db_session.add(Keyphrase(phrase='tutorial', score=5))
        db_session.add(Keyphrase(phrase='review', score=3))
        db_session.commit()

        result = get_keyphrases_dict()

        assert result['tutorial'] == 5
        assert result['review'] == 3

    def test_get_keyphrases_dict_empty(self, db_session):
        """Return empty dict when no keyphrases."""
        result = get_keyphrases_dict()
        assert result == {}


class TestWatchLaterOperations:
    """Tests for watch later database operations."""

    def test_store_watch_later(self, db_session, sample_watch_later_list):
        """Store watch later list in database."""
        store_watch_later(sample_watch_later_list)

        # Verify data was stored
        videos = WatchLaterVideo.query.all()
        assert len(videos) == 5

    def test_get_watch_later_videos(self, db_session, sample_watch_later_list):
        """Retrieve watch later videos as tuples."""
        store_watch_later(sample_watch_later_list)

        result = get_watch_later_videos()

        assert len(result) == 5
        # Check first video
        assert result[0][0] == 0  # position
        assert result[0][2] == 'dQw4w9WgXcQ'  # videoID
        assert result[0][4] == 'Rick Astley'  # creator

    def test_clear_watch_later(self, db_session, sample_watch_later_list):
        """Clear all watch later videos."""
        store_watch_later(sample_watch_later_list)
        assert WatchLaterVideo.query.count() == 5

        clear_watch_later()
        assert WatchLaterVideo.query.count() == 0

    def test_store_watch_later_clears_existing(self, db_session, sample_watch_later_list):
        """Storing new list clears existing data."""
        # Store initial list
        store_watch_later(sample_watch_later_list)
        assert WatchLaterVideo.query.count() == 5

        # Store new smaller list
        new_list = [sample_watch_later_list[0]]
        store_watch_later(new_list)
        assert WatchLaterVideo.query.count() == 1


class TestWatchLaterVideoModel:
    """Tests for WatchLaterVideo model methods."""

    def test_to_tuple(self, db_session, sample_video_tuple):
        """Convert model to tuple format."""
        video = WatchLaterVideo.from_tuple(sample_video_tuple)
        db_session.add(video)
        db_session.commit()

        result = video.to_tuple()

        assert result == sample_video_tuple

    def test_from_tuple(self, sample_video_tuple):
        """Create model from tuple format."""
        video = WatchLaterVideo.from_tuple(sample_video_tuple)

        assert video.position == 0
        assert video.playlistID == 'PLtest123'
        assert video.videoID == 'dQw4w9WgXcQ'
        assert video.duration == 212.0
        assert video.creator == 'Rick Astley'
        assert video.title == 'Never Gonna Give You Up'
