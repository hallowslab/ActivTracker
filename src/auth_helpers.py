from datetime import datetime, timezone
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from models import User
from database import db_session


def current_user():
    """Returns the currently logged-in user object, or None."""
    user_id = session.get("user_id")
    if user_id:
        return db_session.query(User).filter_by(id=user_id).first()
    return None


def user_from_token():
    """Returns the user of the supplied API token if it's valid. or None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    try:
        token_type, token = auth_header.split()
        if token_type.lower() != "bearer":
            return None
        user = db_session.query(User).filter_by(api_token=token).first()
        if (
            user
            and user.token_expiry
            and user.token_expiry > datetime.now(timezone.utc)
        ):
            return user
        return None
    except ValueError:
        return None


def login_required(view_func):
    """Decorator to ensure the user is logged in before accessing a route."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first", "error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def token_required(view_func):
    """Decorator to ensure the token is valid before accessing an API endpoint."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401
        try:
            token_type, token = auth_header.split()
            if token_type.lower() != "bearer":
                return jsonify({"error": "Invalid token type"}), 401
            user = db_session.query(User).filter_by(api_token=token).first()
            if (
                not user
                or not user.token_expiry
                or user.token_expiry < datetime.now(timezone.utc)
            ):
                return jsonify({"error": "Invalid or expired token"}), 401
        except ValueError:
            return jsonify({"error": "Invalid Authorization header"}), 401

        # Pass the user object to the route
        return view_func(user, *args, **kwargs)

    return wrapped_view
