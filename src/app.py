import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

from routes.auth import auth_bp
from routes.actions import action_bp
from routes.api import api_bp
from routes.dashboard import dashboard_bp
from routes.settings import settings_bp
from models import Action
from database import db_session
from forms import TimeframeForm
from cli import create_test_data, collect_static

app = Flask(__name__, static_folder="static", template_folder="templates")

FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
_DEBUG: bool = True if FLASK_ENV == "development" else False

# Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(action_bp)
app.register_blueprint(api_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(settings_bp)

# Commands
app.cli.add_command(create_test_data)
app.cli.add_command(collect_static)






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
