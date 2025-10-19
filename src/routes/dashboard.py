import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
import numpy as np

from database import db_session
from models import Action
from auth_helpers import login_required, current_user
from model_helpers import summarize_actions, get_activity_timeseries
from forms import ActivitySummaryForm

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


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
