"""
Turnaround metrics calculation for PlaylistPro.

Calculates how long it takes to watch videos from each creator by comparing
historical snapshots of the Watch Later playlist.
"""

from __future__ import annotations
from datetime import datetime
from statistics import mean, median, stdev
from typing import Any


def parse_date(date_value: str | datetime) -> datetime:
    """
    Parse a date value that could be a string or datetime object.

    Args:
        date_value: Either a datetime object or a string in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format

    Returns:
        datetime object

    Raises:
        ValueError: If the date cannot be parsed
    """
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, str):
        # Try full datetime format first, then date only
        date_part = date_value.split(' ')[0]
        return datetime.strptime(date_part, '%Y-%m-%d')
    raise ValueError(f"Cannot parse date: {date_value}")


def calculate_turnarounds_from_history(
    creator_history: dict[int, list[tuple[str | datetime, int]]]
) -> dict[int, list[float]]:
    """
    Calculate turnaround times from creator history data.

    Turnaround is measured when a creator's video count decreases between snapshots,
    indicating videos were watched.

    Args:
        creator_history: Dict mapping creator_id to list of (date, video_count) tuples,
                        sorted by date ascending

    Returns:
        Dict mapping creator_id to list of turnaround times in hours
    """
    creator_turnarounds: dict[int, list[float]] = {}

    for creator_id, history in creator_history.items():
        turnarounds = []

        for i in range(1, len(history)):
            prev_date, prev_count = history[i-1]
            curr_date, curr_count = history[i]

            # If count decreased, videos were watched
            if curr_count < prev_count:
                videos_watched = prev_count - curr_count

                try:
                    d1 = parse_date(prev_date)
                    d2 = parse_date(curr_date)

                    # Calculate total seconds between snapshots
                    delta = d2 - d1
                    total_seconds = delta.total_seconds()

                    if total_seconds > 0:
                        # Convert to hours
                        hours_between = total_seconds / 3600
                        # Add one turnaround entry per video watched
                        for _ in range(videos_watched):
                            turnarounds.append(hours_between)
                except (ValueError, TypeError) as e:
                    # Skip entries with unparseable dates
                    continue

        if turnarounds:
            creator_turnarounds[creator_id] = turnarounds

    return creator_turnarounds


def compute_turnaround_stats(
    creator_turnarounds: dict[int, list[float]],
    creators_map: dict[int, Any]
) -> dict:
    """
    Compute statistics from turnaround data.

    Args:
        creator_turnarounds: Dict mapping creator_id to list of turnaround times in hours
        creators_map: Dict mapping creator_id to creator objects (with .creators attribute for name)

    Returns:
        Dict with turnaround statistics:
        - has_data: bool
        - global_mean: float (hours)
        - global_median: float (hours)
        - global_stdev: float (hours)
        - total_videos_watched: int
        - creators: list of per-creator stats sorted by avg turnaround
    """
    if not creator_turnarounds:
        return {'has_data': False}

    # Calculate per-creator averages
    creator_avg_turnarounds = []
    for creator_id, turnarounds in creator_turnarounds.items():
        creator_obj = creators_map.get(creator_id)
        creator_name = creator_obj.creators if creator_obj and hasattr(creator_obj, 'creators') else 'Unknown'
        avg = mean(turnarounds)
        creator_avg_turnarounds.append({
            'CreatorID': creator_id,
            'CreatorName': creator_name,
            'AvgTurnaround': round(avg, 1),
            'VideosWatched': len(turnarounds)
        })

    # Sort by average turnaround (fastest first)
    creator_avg_turnarounds.sort(key=lambda x: x['AvgTurnaround'])

    # Calculate global stats across all turnaround events
    all_turnarounds = []
    for turnarounds in creator_turnarounds.values():
        all_turnarounds.extend(turnarounds)

    global_mean = mean(all_turnarounds) if all_turnarounds else 0
    global_median = median(all_turnarounds) if all_turnarounds else 0
    global_stdev = stdev(all_turnarounds) if len(all_turnarounds) > 1 else 0

    return {
        'has_data': True,
        'global_mean': round(global_mean, 1),
        'global_median': round(global_median, 1),
        'global_stdev': round(global_stdev, 1),
        'total_videos_watched': len(all_turnarounds),
        'creators': creator_avg_turnarounds
    }


def calculate_turnaround_metrics(creators_map: dict, stats_query_func: callable = None) -> dict:
    """
    Calculate turnaround metrics by comparing historical snapshots.

    This is the main entry point that combines data fetching with calculation.

    Args:
        creators_map: Dict mapping creator_id to creator objects
        stats_query_func: Optional function that returns list of stats with .CreatorID, .date, .Frequency
                         If None, uses the default database query

    Returns:
        Dict with turnaround statistics (see compute_turnaround_stats)
    """
    # Get all historical creator stats
    if stats_query_func:
        all_stats = stats_query_func()
    else:
        # Default: query from database
        from . import WatchLaterCreatorStat
        all_stats = WatchLaterCreatorStat.query.order_by(WatchLaterCreatorStat.date.asc()).all()

    if not all_stats:
        return {'has_data': False}

    # Group by creator
    creator_history: dict[int, list[tuple[str | datetime, int]]] = {}
    for stat in all_stats:
        if stat.CreatorID not in creator_history:
            creator_history[stat.CreatorID] = []
        creator_history[stat.CreatorID].append((stat.date, stat.Frequency))

    # Calculate turnarounds
    creator_turnarounds = calculate_turnarounds_from_history(creator_history)

    # Compute and return stats
    return compute_turnaround_stats(creator_turnarounds, creators_map)
