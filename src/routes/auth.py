from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from database import db_session

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
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if db_session.query(User).filter_by(username=username).first():
            flash("Username exists!")
            return redirect(url_for("auth.register"))
        user = User(username=username, password_hash=generate_password_hash(password))
        db_session.add(user)
        db_session.commit()
        flash("Registered! Log in now.")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


# Login route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db_session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash("Logged in!")
            return redirect(url_for("index"))
        flash("Invalid credentials")
        return redirect(url_for("auth.login"))
    return render_template("login.html")


# Logout route
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out!")
    return redirect(url_for("index"))
