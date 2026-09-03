import secrets
from datetime import datetime, timedelta, timezone

import numpy as np
from flask import Blueprint, flash, redirect, render_template, request, url_for

from auth_helpers import current_user, login_required
from database import db_session
from forms import ActivitySummaryForm, TimeframeForm
from model_helpers import get_activity_timeseries
from models import Action

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    Render the dashboard showing per-action activity time series and summary for a selectable timeframe.

    Determines the timeframe (default 30 days, overridable via TimeframeForm or ?days query parameter), gathers the current user's actions, and for each action builds a time series of dates and activity counts plus a linear trend line. Aggregates total actions and per-action summary counts, computes the percentage change between the first and last seven-day totals across all actions, and returns the rendered "dashboard.j2" template populated with:
    - activity_data: list of dicts with keys `name`, `values`, `trend_line`, `labels`
    - total_actions: total count across all actions and days
    - period: human-readable period string (e.g., "last 30 days")
    - trend_change: percent change between initial and final seven-day totals (rounded to 1 decimal)
    - labels, values: summary chart data (action names and totals)
    - form: the TimeframeForm instance
    """
    user = current_user()
    assert user is not None

    form = TimeframeForm()
    days = 30  # default

    if request.method == "POST" and form.validate_on_submit():
        # POST: trust validated form value
        days = form.days.data
    else:
        # GET: try to prefill from query param, but cast safely
        days_arg = request.args.get("days")
        if days_arg is not None:
            try:
                # cast to int before assigning to form field
                form.days.data = int(days_arg)
            except ValueError:
                # invalid int, ignore and keep default
                form.days.data = days

        if form.validate():
            days = form.days.data
        else:
            form.days.data = days

    actions = db_session.query(Action).filter_by(user_id=user.id).all()
    activity_data = []
    total_actions = 0

    # Prepare summary for chart
    summary_counts = {}

    def fit_trend(values):
        x = np.arange(len(values))
        mask = np.array([v is not None for v in values])
        y = np.array([v for v in values if v is not None], dtype=float)
        xm = x[mask]
        if len(y) > 1:
            slope, intercept = np.polyfit(xm, y, 1)
            return (intercept + slope * x).tolist()
        if len(y) == 1:
            return [float(y[0])] * len(values)
        return [None] * len(values)

    for action in actions:
        assert days is not None
        timeseries = get_activity_timeseries(user.id, action.id, days=days)
        labels = [entry["date"] for entry in timeseries]
        values = [entry["value"] for entry in timeseries]
        is_measure = action.kind == "measure"

        if is_measure:
            readings = [v for v in values if v is not None]
            latest = readings[-1] if readings else None
            change = (readings[-1] - readings[0]) if readings else None
            trend_line = fit_trend(values)
        else:
            total_actions += sum(values)
            summary_counts[action.name] = sum(values)
            latest = None
            change = None
            trend_line = fit_trend(values)

        activity_data.append(
            {
                "name": action.name,
                "kind": action.kind,
                "unit": action.unit,
                "values": values,
                "trend_line": trend_line,
                "labels": labels,
                "latest": latest,
                "change": round(change, 2) if change is not None else None,
            }
        )

    # compute trend change (count actions only; measurement sums are meaningless)
    count_series = [a["values"] for a in activity_data if a["kind"] != "measure"]
    if count_series and days >= 14:
        first_total = sum(sum(v for v in a[:7] if v is not None) for a in count_series)
        last_total = sum(sum(v for v in a[-7:] if v is not None) for a in count_series)
        trend_change = (
            round(((last_total - first_total) / first_total * 100), 1)
            if first_total
            else (100.0 if last_total > 0 else 0)
        )
    else:
        trend_change = 0

    # summary chart labels and values
    summary_labels = list(summary_counts.keys())
    summary_values = list(summary_counts.values())

    return render_template(
        "dashboard.j2",
        activity_data=activity_data,
        total_actions=total_actions,
        period=f"last {days} days",
        trend_change=trend_change,
        labels=summary_labels,
        values=summary_values,
        form=form,
    )


@dashboard_bp.route("/summary/activity", methods=["GET", "POST"])
@login_required
def activity_summary():
    """
    Render an activity summary page for a selected user action over a specified period.

    Builds and validates an ActivitySummaryForm (from request values), populates its action choices from the current user's actions, defaults selection and days when missing, computes a per-day activity timeseries and a linear trend line for the chosen action, and returns the rendered "activity_summary.j2" template with the form and a data dict containing:
    - action: the selected Action object
    - actions: list of the user's Action objects
    - labels: list of date labels for the timeseries
    - _values: list of activity deltas
    - days: number of days used for the timeseries
    - trend_line: list of trend values matching labels

    If the user has no actions, flashes "No actions found" and redirects to action.list_actions. If the selected action is not found, flashes "Action not found" and redirects to action.list_actions.

    Returns:
        The rendered template response for the activity summary page or a redirect response when no action is available.
    """
    user = current_user()
    assert user is not None

    actions = db_session.query(Action).filter_by(user_id=user.id).all()
    if not actions:
        flash("No actions found", "error")
        return redirect(url_for("action.list_actions"))

    form = ActivitySummaryForm(request.values)  # Handle GET|POST params

    # Populate select choices dynamically
    form.action_id.choices = [(a.id, a.name) for a in actions]

    # Set default values
    if not form.action_id.data:
        form.action_id.data = actions[0].id

    if not form.days.data:
        form.days.data = 30

    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Invalid input.", "error")
            return render_template("activity_summary.j2", form=form, data=None)
    else:
        if not form.validate():
            form.days.data = 30

    # Extract values
    action_id = form.action_id.data
    days = form.days.data

    action = next((a for a in actions if a.id == action_id), None)
    if not action:
        flash("Action not found", "error")
        return redirect(url_for("action.list_actions"))

    # Compute time series and trend
    timeseries = get_activity_timeseries(user.id, action_id, days=days)
    labels = [entry["date"] for entry in timeseries]
    values = [entry["value"] for entry in timeseries]

    x = np.arange(len(values))
    mask = np.array([v is not None for v in values])
    y = np.array([v for v in values if v is not None], dtype=float)
    if len(y) > 1:
        slope, intercept = np.polyfit(x[mask], y, 1)
        trend_line = (intercept + slope * x).tolist()
    elif len(y) == 1:
        trend_line = [float(y[0])] * len(values)
    else:
        trend_line = [None] * len(values)

    data = {
        "action": action,
        "actions": actions,
        "labels": labels,
        "_values": values,
        "days": days,
        "trend_line": trend_line,
        "is_measure": action.kind == "measure",
    }
    return render_template("activity_summary.j2", form=form, data=data)


# Show token page
@dashboard_bp.route("/token")
@login_required
def show_token():
    user = current_user()
    assert user is not None

    token = user.api_token
    expiry = user.token_expiry
    return render_template("token.j2", token=token, expiry=expiry)


# Generate a new token
@dashboard_bp.route("/token/generate")
@login_required
def generate_token():
    user = current_user()
    assert user is not None

    token = secrets.token_hex(16)
    expiry = datetime.now(timezone.utc) + timedelta(days=30)

    user.api_token = token
    user.token_expiry = expiry
    db_session.commit()

    flash("New API token generated!", "success")
    return redirect(url_for("dashboard.show_token"))
