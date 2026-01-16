"""
YouTube API quota tracking for PlaylistPro.

Tracks daily API quota usage per Google Cloud project to avoid
exceeding YouTube API limits (default: 10,000 units/day).
"""

import datetime as dt
from sqlalchemy import func

from .db import db
from .models import QuotaLimit


def getQuotaUsed(projectID):
    """
    Get the API quota used for today.

    Args:
        projectID: Google Cloud project ID

    Returns:
        tuple: (amount_used, is_today) where is_today indicates if
               the record exists for today
    """
    today = dt.date.today().strftime('%Y-%m-%d')

    result = db.session.query(func.max(QuotaLimit.date)).filter(
        QuotaLimit.projectID == projectID
    ).scalar()

    if result == today:
        quota_record = QuotaLimit.query.filter_by(
            date=today,
            projectID=projectID
        ).first()
        if quota_record:
            return quota_record.Amount, True

    return 0, False


def setQuotaUsed(inDB, quota, projectID):
    """
    Store the API quota used for today.

    Args:
        inDB: Whether a record for today already exists
        quota: The quota amount to store
        projectID: Google Cloud project ID
    """
    today = dt.date.today().strftime('%Y-%m-%d')

    if not inDB:
        quota_record = QuotaLimit(
            date=today,
            Amount=quota,
            projectID=projectID
        )
        db.session.add(quota_record)
    else:
        quota_record = QuotaLimit.query.filter_by(
            date=today,
            projectID=projectID
        ).first()

        if quota_record:
            quota_record.Amount = quota
        else:
            quota_record = QuotaLimit(
                date=today,
                Amount=quota,
                projectID=projectID
            )
            db.session.add(quota_record)

    db.session.commit()
