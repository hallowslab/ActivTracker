import os
from pathlib import Path
from flask import Flask, render_template
from dotenv import load_dotenv
import numpy as np

from auth_helpers import current_user, login_required
from model_helpers import get_activity_timeseries
from routes.auth import auth_bp
from routes.actions import action_bp
from routes.api import api_bp
from routes.dashboard import dashboard_bp
from models import Action
from database import db_session
from cli import create_test_data

app = Flask(__name__, static_folder="static", template_folder="templates")

FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
_DEBUG: bool = True if FLASK_ENV == "development" else False

# Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(action_bp)
app.register_blueprint(api_bp)
app.register_blueprint(dashboard_bp)

# Commands
app.cli.add_command(create_test_data)


@app.route("/")
@login_required
def index():
    user = current_user()
    assert user is not None

    actions = db_session.query(Action).filter_by(user_id=user.id).all()
    activity_data = []
    total_actions = 0

    # Prepare summary for chart
    summary_counts = {}

    for action in actions:
        timeseries = get_activity_timeseries(user.id, action.id, days=30)
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
        trend_change = (
            round(((last_total - first_total) / first_total * 100), 1)
            if first_total
            else 0
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
        period="last 30 days",
        trend_change=trend_change,
        labels=summary_labels,
        values=summary_values,
    )


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def load_secret(path: Path = Path(".secret")):
    try:
        if path.exists() and path.is_file():
            with path.open() as f:
                return f.read()
    except:
        raise


def init():
    load_dotenv()
    print(f"FLASK_ENV: {FLASK_ENV}, DEBUG: {_DEBUG}")
    app.secret_key = "!DEBUG!"
    if FLASK_ENV == "production":
        try:
            app.secret_key = load_secret()
        except:
            raise RuntimeError("Secret key file missing in production")
    print(f"SECRET: {app.secret_key}")
    return app


if __name__ == "__main__":
    init().run(host="0.0.0.0", port=5000, debug=_DEBUG)
