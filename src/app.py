import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_wtf.csrf import CSRFProtect

from cli import collect_static, create_test_data
from database import db_session
from routes.actions import action_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.settings import settings_bp

app = Flask(__name__, static_folder="static", template_folder="templates")
csrf = CSRFProtect()

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
    """
    Remove the current database session when the application context is torn down.
    
    Parameters:
        exception (Exception | None): Optional exception passed by Flask's teardown machinery; this function ignores it.
    """
    db_session.remove()


@app.route("/")
def index():
    """
    Redirects the client to the dashboard index route.
    
    Returns:
        A redirect response that directs the client to the 'dashboard.index' endpoint.
    """
    return redirect(url_for("dashboard.index"))


def load_secret(path: Path = Path(".secret")):
    """
    Load and return the contents of a secret file.
    
    Parameters:
        path (Path): Path to the secret file (defaults to ".secret").
    
    Returns:
        str or None: The file contents as a string if the path exists and is a file, otherwise None.
    """
    try:
        if path.exists() and path.is_file():
            with path.open() as f:
                return f.read()
    except:
        raise


def init():
    """
    Initialize and configure the Flask application, including loading environment variables, setting the secret key, and enabling CSRF protection.
    
    Returns:
        The configured Flask application instance.
    
    Raises:
        RuntimeError: If FLASK_ENV is "production" and the secret key file cannot be loaded.
    """
    load_dotenv()
    print(f"FLASK_ENV: {FLASK_ENV}, DEBUG: {_DEBUG}")
    app.secret_key = "!DEBUG!"
    if FLASK_ENV == "production":
        try:
            app.secret_key = load_secret()
        except:
            raise RuntimeError("Secret key file missing in production")
    print(f"SECRET: {app.secret_key}")
    csrf.init_app(app=app)
    return app


if __name__ == "__main__":
    init().run(host="0.0.0.0", port=5000, debug=_DEBUG)