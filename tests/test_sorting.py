"""
Tests for pywertube sorting functions.
"""

import pytest
from pywertube.sorting import (
    getPriorityVideos,
    getSerializedVideos,
)


class TestGetPriorityVideos:
    """Tests for priority video extraction."""

    def test_getPriorityVideos_by_creator(self, sample_watch_later_list):
        """Extract videos by creator priority."""
        creator_dict = {'Creator A': 10, 'Creator B': 5}

        priority, remaining = getPriorityVideos(
            sample_watch_later_list,
            creator_dict,
            {}  # empty keyword dict
        )

        # Creator A has 2 videos (positions 1 and 3)
        creator_a_videos = [v for v in priority if v[4] == 'Creator A']
        assert len(creator_a_videos) == 2

    def test_getPriorityVideos_no_matches(self, sample_watch_later_list):
        """Return empty priority list when no matches."""
        creator_dict = {'Unknown Creator': 10}

        priority, remaining = getPriorityVideos(
            sample_watch_later_list,
            creator_dict,
            {}
        )

        assert len(priority) == 0
        assert len(remaining) == len(sample_watch_later_list)

    def test_getPriorityVideos_empty_input(self):
        """Handle empty watch later list."""
        priority, remaining = getPriorityVideos([], {}, {})

        assert priority == []
        assert remaining == []


class TestGetSerializedVideos:
    """Tests for serialized video detection."""

    def test_getSerializedVideos_with_part(self):
        """Detect videos with 'part' in title."""
        videos = [
            (0, 'PL1', 'v1', 100.0, 'Creator', 123, 'Tutorial Part 1'),
            (1, 'PL1', 'v2', 100.0, 'Creator', 124, 'Tutorial Part 2'),
            (2, 'PL1', 'v3', 100.0, 'Creator', 125, 'Random Video'),
        ]
        numbered_keywords = ['part', 'episode']

        serialized, remaining = getSerializedVideos(
            videos,
            numbered_keywords,
            []
        )

        assert len(serialized) == 2
        assert len(remaining) == 1

    def test_getSerializedVideos_with_episode(self):
        """Detect videos with 'episode' in title."""
        videos = [
            (0, 'PL1', 'v1', 100.0, 'Creator', 123, 'Series Episode 1'),
            (1, 'PL1', 'v2', 100.0, 'Creator', 124, 'Series Episode 2'),
            (2, 'PL1', 'v3', 100.0, 'Creator', 125, 'One-off Video'),
        ]
        numbered_keywords = ['part', 'episode']

        serialized, remaining = getSerializedVideos(
            videos,
            numbered_keywords,
            []
        )

        assert len(serialized) == 2

    def test_getSerializedVideos_case_insensitive(self):
        """Keywords should match case-insensitively."""
        videos = [
            (0, 'PL1', 'v1', 100.0, 'Creator', 123, 'PART 1 Tutorial'),
            (1, 'PL1', 'v2', 100.0, 'Creator', 124, 'Part 2 Tutorial'),
        ]
        numbered_keywords = ['part']

        serialized, remaining = getSerializedVideos(
            videos,
            numbered_keywords,
            []
        )

        assert len(serialized) == 2

    def test_getSerializedVideos_no_matches(self, sample_watch_later_list):
        """Return empty when no serialized videos found."""
        numbered_keywords = ['part', 'episode']

        serialized, remaining = getSerializedVideos(
            sample_watch_later_list,
            numbered_keywords,
            []
        )

        assert len(serialized) == 0
        assert len(remaining) == len(sample_watch_later_list)
