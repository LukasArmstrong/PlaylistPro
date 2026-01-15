"""
YouTube API quota tracking for PlaylistPro.

Tracks daily API quota usage per Google Cloud project to avoid
exceeding YouTube API limits (default: 10,000 units/day).
"""

import datetime as dt
from sqlalchemy import func

from .logging_config import getLogger
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
    gLogger = getLogger()
    gLogger.debug("Entering...")

    today = dt.date.today().strftime('%Y-%m-%d')
    gLogger.debug(f"Checking quota for project {projectID} on {today}")

    # Get the most recent date for this project
    gLogger.debug("Getting latest date...")
    result = db.session.query(func.max(QuotaLimit.date)).filter(
        QuotaLimit.projectID == projectID
    ).scalar()
    gLogger.debug("Latest date obtained!")

    gLogger.debug("Checking if date is today...")
    if result == today:
        gLogger.debug("Date is today...")
        # Get today's quota
        quota_record = QuotaLimit.query.filter_by(
            date=today,
            projectID=projectID
        ).first()

        if quota_record:
            gLogger.debug("Returning used quota and date...")
            return quota_record.Amount, True

    gLogger.debug("Date is not today or no record found...")
    gLogger.debug("Reseting quota...")
    return 0, False


def setQuotaUsed(inDB, quota, projectID):
    """
    Store the API quota used for today.

    Args:
        inDB: Whether a record for today already exists
        quota: The quota amount to store
        projectID: Google Cloud project ID
    """
    gLogger = getLogger()
    gLogger.debug("Entering...")

    today = dt.date.today().strftime('%Y-%m-%d')

    if not inDB:
        gLogger.debug("Creating new quota record...")
        quota_record = QuotaLimit(
            date=today,
            Amount=quota,
            projectID=projectID
        )
        db.session.add(quota_record)
    else:
        gLogger.debug("Updating quota record...")
        quota_record = QuotaLimit.query.filter_by(
            date=today,
            projectID=projectID
        ).first()

        if quota_record:
            quota_record.Amount = quota
        else:
            # Fallback: create if not found
            quota_record = QuotaLimit(
                date=today,
                Amount=quota,
                projectID=projectID
            )
            db.session.add(quota_record)

    db.session.commit()
    gLogger.debug("Quota Set!")
    gLogger.debug("Leaving...")
