from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth_helpers import login_required, current_user
from database import db_session
from werkzeug.security import generate_password_hash, check_password_hash
from models import User

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def logout_user():
    session.clear()


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def account_settings():
    user = current_user()
    assert user is not None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "change_password":
            old_password = request.form.get("old_password") or None
            new_password = request.form.get("new_password") or None
            confirm_password = request.form.get("confirm_password") or None

            if not old_password or not new_password or not confirm_password:
                flash("You need to provide input all password fields", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")
            elif not check_password_hash(user.password_hash, old_password):
                flash("Old password is incorrect.", "error")
            else:
                user.password = generate_password_hash(new_password)
                db_session.commit()
                flash("Password updated successfully.", "success")

        elif action == "delete_account":
            user_id = user.id
            logout_user()
            user_to_delete = User.query.get(user_id)
            if user_to_delete:
                db_session.delete(user_to_delete)
                db_session.commit()
            flash("Your account has been deleted.", "success")
            return redirect(url_for("auth.login"))

    return render_template("settings.j2")
