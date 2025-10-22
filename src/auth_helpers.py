from datetime import datetime, timezone
from functools import wraps

from flask import flash, jsonify, redirect, request, session, url_for

from database import db_session
from models import User


def current_user():
    """
    Get the User object for the currently logged-in session, or None if no valid user is present.
    
    If the session contains a user_id that does not correspond to a User in the database, the session is cleared before returning None.
    
    Returns:
        user (User|None): The User matching the session's user_id, or None if not logged in or the session was invalid.
    """
    user_id = session.get("user_id")
    if user_id:
        return db_session.query(User).filter_by(id=user_id).first()
    # Ensure the user actually exists in the DB
    user = db_session.query(User).filter_by(id=user_id).first()
    if user is None:
        # Session refers to a stale or invalid user
        session.clear()
        return None
    return user


def login_required(view_func):
    """Decorator to ensure the user is logged in before accessing a route."""

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in first", "error")
            return redirect(url_for("auth.login"))

        # Ensure the user actually exists in the DB
        user = db_session.query(User).filter_by(id=user_id).first()
        if user is None:
            # Session refers to a stale or invalid user
            session.clear()
            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for("auth.login"))

        return view_func(*args, **kwargs)

    return wrapped_view


def user_from_token():
    """Returns the user of the supplied API token if it's valid, or None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    try:
        token_type, token = auth_header.split()
        if token_type.lower() != "bearer":
            return None

        user = db_session.query(User).filter_by(api_token=token).first()
        if not user or not user.token_expiry:
            return None

        # Convert token_expiry to aware UTC datetime if it's naive
        token_expiry = user.token_expiry
        if token_expiry.tzinfo is None:
            token_expiry = token_expiry.replace(tzinfo=timezone.utc)

        if token_expiry > datetime.now(timezone.utc):
            return user

        return None
    except ValueError:
        return None


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
            if not user or not user.token_expiry:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Convert token_expiry to aware UTC datetime if naive
            token_expiry = user.token_expiry
            if token_expiry.tzinfo is None:
                token_expiry = token_expiry.replace(tzinfo=timezone.utc)

            if token_expiry < datetime.now(timezone.utc):
                return jsonify({"error": "Invalid or expired token"}), 401

        except ValueError:
            return jsonify({"error": "Invalid Authorization header"}), 401

        return view_func(*args, **kwargs)

    return wrapped_view