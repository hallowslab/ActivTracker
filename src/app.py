import os
from pathlib import Path
from flask import Flask, render_template
from dotenv import load_dotenv

from auth_helpers import current_user
from routes.auth import auth_bp
from routes.actions import action_bp
from routes.api import api_bp
from routes.dashboard import dashboard_bp
from database import db_session

app = Flask(__name__)
app.secret_key = None

app.register_blueprint(auth_bp)
app.register_blueprint(action_bp)
app.register_blueprint(api_bp)
app.register_blueprint(dashboard_bp)


@app.route("/")
def index():
    return render_template("index.html", user=current_user())


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
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    _DEBUG: bool = True if FLASK_ENV == "development" else False
    if FLASK_ENV == "production":
        try:
            load_secret()
        except:
            raise
    else:
        app.secret_key = "!DEBUG!"
    app.run(host="0.0.0.0", port=5000, debug=_DEBUG)


if __name__ == "__main__":
    init()
