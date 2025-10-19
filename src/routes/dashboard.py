import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
import numpy as np

from database import db_session
from models import Action
from auth_helpers import login_required, current_user
from model_helpers import get_activity_timeseries
from forms import ActivitySummaryForm, TimeframeForm

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    user = current_user()
    assert user is not None

    form = TimeframeForm()

    # Default days
    days = 30

    if form.validate_on_submit():
        days = form.days.data
    elif request.method == "GET":
        # Pre-fill form from query param if provided
        try:
            days_param = int(request.args.get("days", 30))
            if 7 <= days_param <= 90:
                days = days_param
        except ValueError:
            pass
        form.days.data = days

    actions = db_session.query(Action).filter_by(user_id=user.id).all()
    activity_data = []
    total_actions = 0

    # Prepare summary for chart
    summary_counts = {}

    for action in actions:
        assert days is not None
        timeseries = get_activity_timeseries(user.id, action.id, days=days)
        labels = [entry["date"] for entry in timeseries]
        values = [entry["delta"] for entry in timeseries]
        total_actions += sum(values)

        # trend line
        x = np.arange(len(values))
        y = np.array(values)
        if len(values) > 1:
            slope, intercept = np.polyfit(x, y, 1)
            trend_line = (intercept + slope * x).tolist()
        else:
            trend_line = values

        activity_data.append(
            {
                "name": action.name,
                "values": values,
                "trend_line": trend_line,
                "labels": labels,
            }
        )

        # accumulate for summary
        summary_counts[action.name] = sum(values)

    # compute simple trend change
    if len(activity_data) > 0:
        first_total = sum(sum(a["values"][:7]) for a in activity_data)
        last_total = sum(sum(a["values"][-7:]) for a in activity_data)
        trend_change = round(((last_total - first_total) / first_total * 100), 1) if first_total else 0
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
        form=form
    )

@dashboard_bp.route("/summary/activity", methods=["GET", "POST"])
@login_required
def activity_summary():
    user = current_user()
    assert user is not None

    actions = db_session.query(Action).filter_by(user_id=user.id).all()
    if not actions:
        flash("No actions found", "error")
        return redirect(url_for("action.list_actions"))

    form = ActivitySummaryForm(request.args)  # Handle GET params

    # Populate select choices dynamically
    form.action_id.choices = [(a.id, a.name) for a in actions]

    # Set default values
    if not form.action_id.data:
        form.action_id.data = actions[0].id

    if not form.days.data:
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
    values = [entry["delta"] for entry in timeseries]

    import numpy as np

    x = np.arange(len(values))
    y = np.array(values)
    slope, intercept = np.polyfit(x, y, 1)
    trend_line = (intercept + slope * x).tolist()

    data = {
        "action": action,
        "actions": actions,
        "labels": labels,
        "_values": values,
        "days": days,
        "trend_line": trend_line,
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
