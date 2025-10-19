from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth_helpers import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import User
from database import db_session
from forms import ChangePasswordForm, DeleteAccountForm

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def logout_user():
    session.clear()


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def account_settings():
    user = current_user()
    assert user is not None

    change_form = ChangePasswordForm(prefix="change")
    delete_form = DeleteAccountForm(prefix="delete")

    if change_form.validate_on_submit():
        old_password = change_form.old_password.data
        new_password = change_form.new_password.data
        assert old_password is not None
        assert new_password is not None

        # Handle password change
        if not check_password_hash(user.password_hash, old_password):
            flash("Old password is incorrect.", "error")
        else:
            user.password_hash = generate_password_hash(new_password)
            db_session.commit()
            flash("Password updated successfully.", "success")

    elif delete_form.validate_on_submit():
        # Handle account deletion
        user_id = user.id
        logout_user()
        user_to_delete = db_session.query(User).filter_by(id=user_id).one_or_none()
        if user_to_delete:
            db_session.delete(user_to_delete)
            db_session.commit()
        flash("Your account has been deleted.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "settings.j2",
        change_form=change_form,
        delete_form=delete_form
    )
