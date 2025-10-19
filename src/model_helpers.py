from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from database import db_session
from models import Action, ActivityLog


def summarize_actions(user_id: int, period: str = "week"):
    """
    Returns summary of actions for a given period.
    period: "day", "week", "month"
    """
    now = datetime.now(timezone.utc)

    if period == "day":
        start = now - timedelta(days=1)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    else:
        raise ValueError("Invalid period")

    # Aggregate total delta per action
    results = (
        db_session.query(
            Action.name, func.coalesce(func.sum(ActivityLog.delta), 0).label("total")
        )
        .outerjoin(ActivityLog, ActivityLog.action_id == Action.id)
        .filter(Action.user_id == user_id)
        .filter((ActivityLog.timestamp >= start) | (ActivityLog.timestamp == None))
        .group_by(Action.id)
        .all()
    )

    summary = {name: total or 0 for name, total in results}
    return summary


def get_activity_timeseries(user_id: int, action_id: int, days: int = 30):
    """
    Returns a time series for a single action over the last `days` days.
    Output: list of dicts [{'date': 'YYYY-MM-DD', 'delta': int}, ...]
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    logs = (
        db_session.query(ActivityLog.timestamp, ActivityLog.delta)
        .join(Action, Action.id == ActivityLog.action_id)
        .filter(Action.user_id == user_id)
        .filter(ActivityLog.action_id == action_id)
        .filter(ActivityLog.timestamp >= start)
        .order_by(ActivityLog.timestamp.asc())
        .all()
    )

    # Aggregate deltas per day
    daily_totals = defaultdict(int)
    for ts, delta in logs:
        day = ts.date().isoformat()
        daily_totals[day] += delta

    # Fill missing days with 0
    timeseries = []
    for i in range(days + 1):
        day = (start + timedelta(days=i)).date().isoformat()
        timeseries.append({"date": day, "delta": daily_totals.get(day, 0)})

    return timeseries
