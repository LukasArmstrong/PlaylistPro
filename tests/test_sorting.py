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
            {},  # empty keyword dict
            priorityThreshold=0,
            durationThreshold=9999  # high threshold to include all durations
        )

        # Priority is a list of lists (one per priority level)
        # Flatten to count Creator A videos
        all_priority = [v for sublist in priority for v in sublist]
        creator_a_videos = [v for v in all_priority if v[4] == 'Creator A']
        assert len(creator_a_videos) == 2

    def test_getPriorityVideos_no_matches(self, sample_watch_later_list):
        """Return empty priority list when no matches."""
        creator_dict = {'Unknown Creator': 10}

        priority, remaining = getPriorityVideos(
            sample_watch_later_list,
            creator_dict,
            {},
            priorityThreshold=0,
            durationThreshold=9999
        )

        # Flatten priority lists
        all_priority = [v for sublist in priority for v in sublist]
        assert len(all_priority) == 0
        assert len(remaining) == len(sample_watch_later_list)

    def test_getPriorityVideos_empty_input(self):
        """Handle empty watch later list."""
        priority, remaining = getPriorityVideos(
            [],
            {},
            {},
            priorityThreshold=0,
            durationThreshold=9999
        )

        assert priority == []
        assert remaining == []


class TestGetSerializedVideos:
    """Tests for serialized video detection.

    Note: getSerializedVideos returns a tuple of:
    - serialized: list of lists, grouped by creator
    - remaining: videos that didn't match serialized patterns
    """

    def test_getSerializedVideos_with_part(self):
        """Detect videos with 'part' in title followed by a number."""
        videos = [
            (0, 'PL1', 'v1', 100.0, 'Creator', 123, 'Tutorial Part 1'),
            (1, 'PL1', 'v2', 100.0, 'Creator', 124, 'Tutorial Part 2'),
            (2, 'PL1', 'v3', 100.0, 'Creator', 125, 'Random Video'),
        ]
        numbered_keywords = ['part', 'episode']

        serialized, remaining = getSerializedVideos(
            videos,
            numbered_keywords,
            ['finale']  # non-numbered keywords
        )

        # Flatten the nested list to count total serialized videos
        all_serialized = [v for sublist in serialized for v in sublist]
        assert len(all_serialized) == 2
        assert len(remaining) == 1

    def test_getSerializedVideos_with_episode(self):
        """Detect videos with 'episode' in title followed by a number."""
        videos = [
            (0, 'PL1', 'v1', 100.0, 'Creator', 123, 'Series Episode 1'),
            (1, 'PL1', 'v2', 100.0, 'Creator', 124, 'Series Episode 2'),
            (2, 'PL1', 'v3', 100.0, 'Creator', 125, 'One-off Video'),
        ]
        numbered_keywords = ['part', 'episode']

        serialized, remaining = getSerializedVideos(
            videos,
            numbered_keywords,
            ['finale']
        )

        all_serialized = [v for sublist in serialized for v in sublist]
        assert len(all_serialized) == 2

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
            ['finale']
        )

        all_serialized = [v for sublist in serialized for v in sublist]
        assert len(all_serialized) == 2

    def test_getSerializedVideos_no_matches(self):
        """Return empty sublists when no serialized videos found."""
        videos = [
            (0, 'PL1', 'v1', 100.0, 'Creator A', 123, 'Regular Video'),
            (1, 'PL1', 'v2', 100.0, 'Creator B', 124, 'Another Video'),
        ]
        numbered_keywords = ['part', 'episode']

        serialized, remaining = getSerializedVideos(
            videos,
            numbered_keywords,
            ['finale']
        )

        # No videos should match - all sublists should be empty
        all_serialized = [v for sublist in serialized for v in sublist]
        assert len(all_serialized) == 0
        assert len(remaining) == 2
