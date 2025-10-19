import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Action, ActivityLog
from database import db_session
from auth_helpers import login_required, current_user
from forms import EditActionForm, EditActivityForm, LogActivityForm

action_bp = Blueprint("action", __name__, url_prefix="/actions")


# List all actions
@action_bp.route("/")
@login_required
def list_actions():
    user = current_user()
    assert user is not None  # For type checking safety

    actions = db_session.query(Action).filter_by(user_id=user.id).all()
    return render_template("actions.j2", actions=actions, current_user=current_user)


# Create a new action
@action_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_action():
    user = current_user()
    assert user is not None

    if request.method == "POST":
        name = request.form["name"].strip()
        notes = request.form.get("notes", "")
        properties_raw = request.form.get("properties", "{}")

        try:
            properties = json.loads(properties_raw) if properties_raw else {}
        except json.JSONDecodeError:
            flash("Invalid JSON in properties", "error")
            return redirect(url_for("action.new_action"))

        action = Action(name=name, user_id=user.id, notes=notes, properties=properties)
        db_session.add(action)
        db_session.commit()

        flash(f"Action '{name}' created successfully!", "info")
        return redirect(url_for("action.list_actions"))

    return render_template("new_action.j2")


# Edit action
@action_bp.route("/edit/action/<int:action_id>", methods=["GET", "POST"])
@login_required
def edit_action(action_id):
    user = current_user()
    assert user is not None

    action = db_session.query(Action).filter_by(id=action_id, user_id=user.id).first()
    if not action:
        flash("Action not found.", "error")
        return redirect(url_for("action.list_actions"))

    form = EditActionForm(obj=action)  # Pre-fill form with existing data

    if form.validate_on_submit():
        assert form.name.data is not None
        action.name = form.name.data
        action.notes = form.notes.data or ""

        properties_raw = form.properties.data or "{}"
        try:
            action.properties = json.loads(properties_raw)
        except json.JSONDecodeError:
            flash("Invalid JSON in properties", "error")
            return render_template("edit_action.j2", form=form, action=action)

        db_session.commit()
        flash("Action updated successfully!", "info")
        return redirect(url_for("action.list_actions"))

    # Pre-populate the properties text area with JSON
    if request.method == "GET":
        form.properties.data = (
            json.dumps(action.properties, indent=2)
            if isinstance(action.properties, dict)
            else action.properties
        )

    return render_template("edit_action.j2", form=form, action=action)


# Edit activity
@action_bp.route("/edit/log/<int:log_id>", methods=["GET", "POST"])
@login_required
def edit_activity(log_id):
    user = current_user()
    assert user is not None

    log = (
        db_session.query(ActivityLog)
        .join(Action)
        .filter(ActivityLog.id == log_id, Action.user_id == user.id)
        .first()
    )
    if not log:
        flash("Activity not found.", "error")
        return redirect(url_for("action.list_actions"))

    form = EditActivityForm(obj=log)

    if form.validate_on_submit():
        assert form.delta.data is not None
        log.delta = float(form.delta.data)
        log.notes = form.notes.data or ""

        properties_raw = form.properties.data or "{}"
        try:
            log.properties = json.loads(properties_raw)
        except json.JSONDecodeError:
            flash("Invalid JSON in properties", "error")
            return render_template("edit_activity.j2", form=form, log=log)

        db_session.commit()
        flash("Activity updated successfully!", "info")
        return redirect(url_for("action.view_action_history", action_id=log.action_id))

    # Pre-populate JSON text on GET
    if request.method == "GET":
        form.properties.data = (
            json.dumps(log.properties, indent=2)
            if isinstance(log.properties, dict)
            else log.properties
        )

    return render_template("edit_activity.j2", form=form, log=log)


# Increment action (add log)
@action_bp.route("/<int:action_id>/log", methods=["GET", "POST"])
@login_required
def log_activity(action_id):
    user = current_user()
    assert user is not None

    action = db_session.query(Action).filter_by(id=action_id, user_id=user.id).first()
    if not action:
        flash("Action not found", "error")
        return redirect(url_for("action.list_actions"))

    form = LogActivityForm(obj=ActivityLog)

    if form.validate_on_submit():
        assert form.delta.data is not None
        delta = form.delta.data
        notes = form.notes.data

        properties_raw = form.properties.data
        try:
            properties = json.loads(properties_raw) if properties_raw else {}
        except json.JSONDecodeError:
            flash("Invalid JSON in properties", "error")
            return redirect(url_for("action.log_activity", action_id=action.id))

        log = ActivityLog(
            action_id=action.id,
            timestamp=datetime.now(timezone.utc),
            delta=delta,
            notes=notes,
            properties=properties,
        )
        db_session.add(log)
        db_session.commit()

        flash(f"Logged new instance for '{action.name}'", "success")
        return redirect(url_for("action.view_action_history", action_id=action.id))

    return render_template("log_activity.j2", form=form, action=action)


# View action history
@action_bp.route("/<int:action_id>")
@login_required
def view_action_history(action_id):
    user = current_user()
    assert user is not None

    action = db_session.query(Action).filter_by(id=action_id, user_id=user.id).first()
    if not action:
        flash("Action not found", "error")
        return redirect(url_for("action.list_actions"))

    logs = (
        db_session.query(ActivityLog)
        .filter_by(action_id=action.id)
        .order_by(ActivityLog.timestamp.desc())
        .all()
    )

    return render_template(
        "view_action_history.j2", action=action, logs=logs, current_user=current_user
    )
