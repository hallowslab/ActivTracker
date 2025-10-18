import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
import numpy as np

from database import db_session
from models import Action
from auth_helpers import login_required, current_user
from model_helpers import summarize_actions, get_activity_timeseries

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/summary")
@login_required
def view_summary():
    user = current_user()
    assert user is not None

    period = request.args.get("period", "week")  # default to week
    summary = summarize_actions(user.id, period)
    labels = list(summary.keys())
    values = list(summary.values())
    print(f"LABELS: {labels}, Values: {values}")
    # data = {"labels": labels, "values": values, "period": period}
    return render_template("summary.j2", labels=labels, values=values, period=period)


@dashboard_bp.route("/summary/activity/<int:action_id>")
@login_required
def activity_summary(action_id):
    user = current_user()
    assert user is not None

    days = int(request.args.get("days", 30))  # last 30 days by default
    timeseries = get_activity_timeseries(user.id, action_id, days=days)

    labels = [entry["date"] for entry in timeseries]
    values = [entry["delta"] for entry in timeseries]

    actions = db_session.query(Action).filter_by(user_id=user.id)
    action = actions.filter_by(id=action_id, user_id=user.id).first()

    x = np.arange(len(values))
    y = np.array(values)
    slope, intercept = np.polyfit(x, y, 1)
    trend_line = (intercept + slope * x).tolist()

    data = {
        "action": action,
        "actions": actions.all(),
        "labels": labels,
        "_values": values,
        "days": days,
        "trend_line": trend_line,
    }
    if not action:
        flash("Action not found", "error")
        return redirect(url_for("action.list_actions"))

    return render_template("activity_summary.j2", data=data)


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
