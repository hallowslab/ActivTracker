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
    session.clear()
    flash("Logged out!", "info")
    return redirect(url_for("dashboard.index"))
