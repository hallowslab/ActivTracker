from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from database import db_session
from models import Action, ActivityLog


def summarize_actions(user_id: int, period: str = "week"):
    """
    Returns summary of actions for a given period.
    period: "day", "week", "month"

    Count actions: total delta in the window.
    Measurement actions: latest reading in the window (sums are meaningless).
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

    actions = db_session.query(Action).filter(Action.user_id == user_id).all()

    summary = {}
    for action in actions:
        if action.kind == "measure":
            latest = (
                db_session.query(ActivityLog.value)
                .filter(
                    ActivityLog.action_id == action.id,
                    ActivityLog.value.isnot(None),
                    ActivityLog.timestamp >= start,
                )
                .order_by(ActivityLog.timestamp.desc())
                .first()
            )
            summary[action.name] = latest[0] if latest else 0
        else:
            total = (
                db_session.query(func.coalesce(func.sum(ActivityLog.delta), 0))
                .filter(
                    ActivityLog.action_id == action.id,
                    ActivityLog.timestamp >= start,
                )
                .scalar()
            )
            summary[action.name] = total or 0
    return summary


def get_activity_timeseries(user_id: int, action_id: int, days: int = 30):
    """
    Returns a time series for a single action over the last `days` days.
    Output: list of dicts [{'date': 'YYYY-MM-DD', 'value': float|int|None}, ...]

    Count actions: per-day sum of deltas, missing days filled with 0.
    Measurement actions: per-day mean of readings, missing days left as None (gap).
    """
    action = (
        db_session.query(Action)
        .filter(Action.id == action_id, Action.user_id == user_id)
        .first()
    )
    is_measure = bool(action and action.kind == "measure")

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    logs = (
        db_session.query(ActivityLog.timestamp, ActivityLog.delta, ActivityLog.value)
        .join(Action, Action.id == ActivityLog.action_id)
        .filter(Action.user_id == user_id)
        .filter(ActivityLog.action_id == action_id)
        .filter(ActivityLog.timestamp >= start)
        .order_by(ActivityLog.timestamp.asc())
        .all()
    )

    # Aggregate per day
    daily_totals: defaultdict[str, float] = defaultdict(float)
    daily_counts: defaultdict[str, int] = defaultdict(int)
    for ts, delta, value in logs:
        day = ts.date().isoformat()
        if is_measure:
            if value is not None:
                daily_totals[day] += value
                daily_counts[day] += 1
        else:
            daily_totals[day] += delta

    timeseries = []
    for i in range(days + 1):
        day = (start + timedelta(days=i)).date().isoformat()
        if is_measure:
            if daily_counts[day]:
                val: float | int | None = round(
                    daily_totals[day] / daily_counts[day], 2
                )
            else:
                val = None
        else:
            val = daily_totals.get(day, 0)
        timeseries.append({"date": day, "value": val})

    return timeseries
