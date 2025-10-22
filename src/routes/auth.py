from flask import Blueprint, flash, redirect, render_template, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import db_session
from forms import LoginForm, RegisterForm
from models import User

auth_bp = Blueprint("auth", __name__)


# Helper to get current user
def current_user():
    user_id = session.get("user_id")
    if user_id:
        return db_session.query(User).filter_by(id=user_id).first()
    return None


# Register route
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle the user registration form: create a new user when the submitted data is valid, or render the registration page.
    
    On successful registration, adds the new user to the database and redirects to the login page. If the submitted username already exists, flashes an error and redirects back to the registration page. If the form is not submitted or fails validation, renders the registration template with the form instance.
    
    Returns:
        A Flask response — a redirect to the login page on successful registration, a redirect back to the registration page when the username exists, or the rendered registration template when displaying the form.
    """
    form = RegisterForm()
    if form.validate_on_submit():
        assert form.username.data is not None
        assert form.password.data is not None
        username = form.username.data
        password = form.password.data

        if db_session.query(User).filter_by(username=username).first():
            flash("Username exists!", "error")
            return redirect(url_for("auth.register"))

        user = User(username=username, password_hash=generate_password_hash(password))
        db_session.add(user)
        db_session.commit()
        flash("Registered! Log in now.", "info")
        return redirect(url_for("auth.login"))
    return render_template("register.j2", form=form)


# Login route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate credentials submitted via the login form and establish a user session.
    
    If the submitted form is valid and credentials match a user, stores the user's id in the session and redirects to the dashboard index. If credentials are invalid, redirects back to the login page with an error flash. On initial GET or when form validation fails, renders the login template with the form.
    
    Returns:
        A Flask response object — either a redirect to the dashboard on successful login, a redirect back to the login page on failed authentication, or the rendered login template when showing the form.
    """
    form = LoginForm()
    if form.validate_on_submit():
        assert form.username.data is not None
        assert form.password.data is not None
        username = form.username.data
        password = form.password.data

        user = db_session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash("Logged in!", "info")
            return redirect(url_for("dashboard.index"))

        flash("Invalid credentials", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.j2", form=form)


# Logout route
@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Clear the current session, flash a logout confirmation message, and redirect to the dashboard index.
    
    Returns:
        Response: A redirect response to the dashboard index.
    """
    session.clear()
    flash("Logged out!", "info")
    return redirect(url_for("dashboard.index"))