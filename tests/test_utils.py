"""
Tests for pywertube utility functions.
"""

import pytest
from pywertube.utils import (
    checkType,
    checkTypeReturn,
    durationString2Sec,
    dateString2EpochTime,
    sanitizeTitle,
    filterDict,
    renumberWatchLater,
)


class TestCheckType:
    """Tests for type checking functions."""

    def test_checkType_valid_string(self):
        """checkType should not raise for valid string."""
        checkType("hello", str)

    def test_checkType_valid_int(self):
        """checkType should not raise for valid int."""
        checkType(42, int)

    def test_checkType_valid_list(self):
        """checkType should not raise for valid list."""
        checkType([1, 2, 3], list)

    def test_checkType_invalid_raises(self):
        """checkType should raise TypeError for invalid type."""
        with pytest.raises(TypeError):
            checkType("hello", int)

    def test_checkTypeReturn_valid(self):
        """checkTypeReturn should return True for valid type."""
        assert checkTypeReturn("hello", str) is True

    def test_checkTypeReturn_invalid(self):
        """checkTypeReturn should return False for invalid type."""
        assert checkTypeReturn("hello", int) is False


class TestDurationConversion:
    """Tests for YouTube duration string parsing."""

    def test_durationString2Sec_full(self):
        """Parse duration with hours, minutes, and seconds."""
        assert durationString2Sec("PT1H30M45S") == 5445.0

    def test_durationString2Sec_minutes_seconds(self):
        """Parse duration with only minutes and seconds."""
        assert durationString2Sec("PT5M30S") == 330.0

    def test_durationString2Sec_seconds_only(self):
        """Parse duration with only seconds."""
        assert durationString2Sec("PT45S") == 45.0

    def test_durationString2Sec_hours_only(self):
        """Parse duration with only hours."""
        assert durationString2Sec("PT2H") == 7200.0

    def test_durationString2Sec_minutes_only(self):
        """Parse duration with only minutes."""
        assert durationString2Sec("PT10M") == 600.0

    def test_durationString2Sec_zero(self):
        """Parse zero duration."""
        assert durationString2Sec("PT0S") == 0.0

    def test_durationString2Sec_invalid_type(self):
        """Raise TypeError for non-string input."""
        with pytest.raises(TypeError):
            durationString2Sec(123)


class TestDateConversion:
    """Tests for date string to epoch conversion."""

    def test_dateString2EpochTime_valid(self):
        """Convert valid YouTube date string to epoch."""
        result = dateString2EpochTime("2020-01-01T00:00:00Z")
        assert result == 1577836800.0

    def test_dateString2EpochTime_with_time(self):
        """Convert date string with specific time."""
        result = dateString2EpochTime("2020-06-15T12:30:45Z")
        assert result == 1592224245.0

    def test_dateString2EpochTime_invalid_type(self):
        """Raise TypeError for non-string input."""
        with pytest.raises(TypeError):
            dateString2EpochTime(12345)


class TestSanitizeTitle:
    """Tests for title sanitization."""

    def test_sanitizeTitle_removes_quotes(self):
        """Remove double quotes from title."""
        assert sanitizeTitle('Hello "World"') == 'Hello World'

    def test_sanitizeTitle_removes_single_quotes(self):
        """Remove single quotes from title."""
        assert sanitizeTitle("It's a test") == "Its a test"

    def test_sanitizeTitle_removes_question_mark(self):
        """Remove question marks from title."""
        assert sanitizeTitle("What is this?") == "What is this"

    def test_sanitizeTitle_multiple_chars(self):
        """Remove multiple special characters."""
        assert sanitizeTitle("What's \"this\"?") == "Whats this"

    def test_sanitizeTitle_clean_string(self):
        """Return unchanged if no special chars."""
        assert sanitizeTitle("Clean Title") == "Clean Title"


class TestFilterDict:
    """Tests for dictionary filtering."""

    def test_filterDict_greater_than(self):
        """Filter values greater than threshold."""
        d = {'a': 10, 'b': 20, 'c': 30}
        result = filterDict(d, ">", 15)
        assert result == {'b': 20, 'c': 30}

    def test_filterDict_less_than(self):
        """Filter values less than threshold."""
        d = {'a': 10, 'b': 20, 'c': 30}
        result = filterDict(d, "<", 25)
        assert result == {'a': 10, 'b': 20}

    def test_filterDict_empty_result(self):
        """Return empty dict when nothing matches."""
        d = {'a': 10, 'b': 20}
        result = filterDict(d, ">", 100)
        assert result == {}


class TestRenumberWatchLater:
    """Tests for watch later renumbering."""

    def test_renumberWatchLater_basic(self, sample_watch_later_list):
        """Renumber positions sequentially."""
        # Shuffle positions
        shuffled = [
            (5, 'PLtest123', 'video1', 100.0, 'Creator', 1234567890, 'Title 1'),
            (10, 'PLtest123', 'video2', 200.0, 'Creator', 1234567891, 'Title 2'),
            (3, 'PLtest123', 'video3', 150.0, 'Creator', 1234567892, 'Title 3'),
        ]
        result = renumberWatchLater(shuffled)

        # Check positions are now 0, 1, 2
        assert result[0][0] == 0
        assert result[1][0] == 1
        assert result[2][0] == 2

        # Check other data is preserved
        assert result[0][2] == 'video1'
        assert result[1][2] == 'video2'
        assert result[2][2] == 'video3'

    def test_renumberWatchLater_empty(self):
        """Handle empty list."""
        result = renumberWatchLater([])
        assert result == []
