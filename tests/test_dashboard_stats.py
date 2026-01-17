"""
Test suite for dashboard statistics / turnaround metrics calculation.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from pywertube.dashboard_stats import (
    parse_date,
    calculate_turnarounds_from_history,
    compute_turnaround_stats,
    calculate_turnaround_metrics
)


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_datetime_object(self):
        dt = datetime(2026, 1, 15, 10, 30, 0)
        result = parse_date(dt)
        assert result == dt

    def test_parse_date_string_full(self):
        result = parse_date("2026-01-15 10:30:00")
        assert result == datetime(2026, 1, 15)

    def test_parse_date_string_date_only(self):
        result = parse_date("2026-01-15")
        assert result == datetime(2026, 1, 15)

    def test_parse_invalid_string(self):
        with pytest.raises(ValueError):
            parse_date("not-a-date")

    def test_parse_invalid_type(self):
        with pytest.raises(ValueError):
            parse_date(12345)


class TestCalculateTurnaroundsFromHistory:
    """Tests for calculate_turnarounds_from_history function."""

    def test_empty_history(self):
        result = calculate_turnarounds_from_history({})
        assert result == {}

    def test_single_snapshot_no_turnaround(self):
        """Single snapshot can't produce turnaround data."""
        history = {
            1: [("2026-01-15", 5)]
        }
        result = calculate_turnarounds_from_history(history)
        assert result == {}

    def test_no_decrease_no_turnaround(self):
        """If video count never decreases, no turnaround."""
        history = {
            1: [
                ("2026-01-15", 3),
                ("2026-01-16", 5),  # Increased
                ("2026-01-17", 5),  # Same
            ]
        }
        result = calculate_turnarounds_from_history(history)
        assert result == {}

    def test_simple_decrease(self):
        """Simple case: 5 videos -> 3 videos over 2 days."""
        history = {
            1: [
                ("2026-01-15", 5),
                ("2026-01-17", 3),  # 2 videos watched over 2 days
            ]
        }
        result = calculate_turnarounds_from_history(history)

        assert 1 in result
        assert len(result[1]) == 2  # 2 videos watched
        # 2 days = 48 hours
        assert all(t == 48.0 for t in result[1])

    def test_multiple_decreases(self):
        """Multiple decreases over time."""
        history = {
            1: [
                ("2026-01-15", 10),
                ("2026-01-16", 8),   # 2 videos watched, 1 day = 24 hours
                ("2026-01-18", 5),   # 3 videos watched, 2 days = 48 hours
            ]
        }
        result = calculate_turnarounds_from_history(history)

        assert 1 in result
        assert len(result[1]) == 5  # 2 + 3 = 5 videos watched
        # First 2 entries should be 24 hours, next 3 should be 48 hours
        assert result[1].count(24.0) == 2
        assert result[1].count(48.0) == 3

    def test_increase_then_decrease(self):
        """Increase followed by decrease - only count the decrease."""
        history = {
            1: [
                ("2026-01-15", 5),
                ("2026-01-16", 8),   # Increased (new videos added)
                ("2026-01-17", 6),   # 2 videos watched, 1 day = 24 hours
            ]
        }
        result = calculate_turnarounds_from_history(history)

        assert 1 in result
        assert len(result[1]) == 2  # Only the decrease counts
        assert all(t == 24.0 for t in result[1])

    def test_multiple_creators(self):
        """Multiple creators tracked independently."""
        history = {
            1: [
                ("2026-01-15", 5),
                ("2026-01-16", 3),  # 2 videos, 24 hours
            ],
            2: [
                ("2026-01-15", 10),
                ("2026-01-17", 7),  # 3 videos, 48 hours
            ]
        }
        result = calculate_turnarounds_from_history(history)

        assert 1 in result
        assert 2 in result
        assert len(result[1]) == 2
        assert len(result[2]) == 3
        assert all(t == 24.0 for t in result[1])
        assert all(t == 48.0 for t in result[2])

    def test_datetime_objects(self):
        """Test with datetime objects instead of strings."""
        history = {
            1: [
                (datetime(2026, 1, 15, 10, 0, 0), 5),
                (datetime(2026, 1, 16, 10, 0, 0), 3),  # 2 videos, exactly 24 hours
            ]
        }
        result = calculate_turnarounds_from_history(history)

        assert 1 in result
        assert len(result[1]) == 2
        assert all(t == 24.0 for t in result[1])

    def test_same_day_snapshots(self):
        """Snapshots on the same day with different times."""
        history = {
            1: [
                (datetime(2026, 1, 15, 8, 0, 0), 5),
                (datetime(2026, 1, 15, 14, 0, 0), 3),  # 2 videos, 6 hours
            ]
        }
        result = calculate_turnarounds_from_history(history)

        assert 1 in result
        assert len(result[1]) == 2
        assert all(t == 6.0 for t in result[1])

    def test_zero_time_difference_skipped(self):
        """If timestamps are identical, skip (avoid division issues)."""
        history = {
            1: [
                (datetime(2026, 1, 15, 10, 0, 0), 5),
                (datetime(2026, 1, 15, 10, 0, 0), 3),  # Same timestamp
            ]
        }
        result = calculate_turnarounds_from_history(history)
        # Should be empty since time diff is 0
        assert result == {}


class TestComputeTurnaroundStats:
    """Tests for compute_turnaround_stats function."""

    def test_empty_turnarounds(self):
        result = compute_turnaround_stats({}, {})
        assert result == {'has_data': False}

    def test_simple_stats(self):
        turnarounds = {
            1: [24.0, 24.0],  # 2 videos, 24 hours each
        }
        creators_map = {1: MagicMock(creators="Creator A")}

        result = compute_turnaround_stats(turnarounds, creators_map)

        assert result['has_data'] is True
        assert result['global_mean'] == 24.0
        assert result['global_median'] == 24.0
        assert result['global_stdev'] == 0  # All same value, stdev requires >1 unique
        assert result['total_videos_watched'] == 2
        assert len(result['creators']) == 1
        assert result['creators'][0]['CreatorName'] == "Creator A"
        assert result['creators'][0]['AvgTurnaround'] == 24.0

    def test_multiple_creators_sorted(self):
        """Creators should be sorted by average turnaround (fastest first)."""
        turnarounds = {
            1: [48.0, 48.0],  # Slower
            2: [12.0, 12.0],  # Faster
        }
        creators_map = {
            1: MagicMock(creators="Slow Creator"),
            2: MagicMock(creators="Fast Creator"),
        }

        result = compute_turnaround_stats(turnarounds, creators_map)

        assert result['creators'][0]['CreatorName'] == "Fast Creator"
        assert result['creators'][1]['CreatorName'] == "Slow Creator"

    def test_unknown_creator(self):
        """Creator not in map should be labeled 'Unknown'."""
        turnarounds = {999: [24.0]}
        creators_map = {}

        result = compute_turnaround_stats(turnarounds, creators_map)

        assert result['creators'][0]['CreatorName'] == "Unknown"

    def test_global_stats_across_creators(self):
        """Global stats should aggregate across all creators."""
        turnarounds = {
            1: [10.0, 20.0],  # mean=15
            2: [30.0, 40.0],  # mean=35
        }
        creators_map = {
            1: MagicMock(creators="A"),
            2: MagicMock(creators="B"),
        }

        result = compute_turnaround_stats(turnarounds, creators_map)

        # All values: 10, 20, 30, 40
        # Mean: 25, Median: 25
        assert result['global_mean'] == 25.0
        assert result['global_median'] == 25.0
        assert result['total_videos_watched'] == 4


class TestCalculateTurnaroundMetrics:
    """Integration tests for calculate_turnaround_metrics."""

    def test_with_mock_query(self):
        """Test the full pipeline with a mock query function."""
        # Create mock stats
        mock_stats = [
            MagicMock(CreatorID=1, date="2026-01-15", Frequency=5),
            MagicMock(CreatorID=1, date="2026-01-16", Frequency=3),
            MagicMock(CreatorID=2, date="2026-01-15", Frequency=10),
            MagicMock(CreatorID=2, date="2026-01-17", Frequency=8),
        ]

        creators_map = {
            1: MagicMock(creators="Creator A"),
            2: MagicMock(creators="Creator B"),
        }

        def mock_query():
            return mock_stats

        result = calculate_turnaround_metrics(creators_map, stats_query_func=mock_query)

        assert result['has_data'] is True
        assert result['total_videos_watched'] == 4  # 2 + 2
        assert len(result['creators']) == 2

    def test_empty_query(self):
        """Empty query should return has_data=False."""
        def mock_query():
            return []

        result = calculate_turnaround_metrics({}, stats_query_func=mock_query)
        assert result == {'has_data': False}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
