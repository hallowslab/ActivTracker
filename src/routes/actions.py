import json
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from auth_helpers import current_user, login_required
from database import db_session
from forms import (
    EditActionForm,
    EditActivityForm,
    EditMeasurementForm,
    LogActivityForm,
    LogMeasurementForm,
    NewActionForm,
)
from models import Action, ActivityLog

action_bp = Blueprint("action", __name__, url_prefix="/actions")


def _measurement_label(action: Action) -> str:
    return f"{action.name} ({action.unit})" if action.unit else action.name


def _convert_logs_kind(action: Action, new_kind: str) -> int:
    """
    Transform existing logs when an action switches kind.

    count -> measure: each log's delta becomes the reading value (delta reset to 0).
    measure -> count: each log's value becomes the delta, rounded to int (value reset to None).
    Returns the number of logs converted.
    """
    logs = db_session.query(ActivityLog).filter_by(action_id=action.id).all()
    converted = 0
    for log in logs:
        if new_kind == "measure" and log.value is None:
            log.value = float(log.delta)
            log.delta = 0
            converted += 1
        elif new_kind == "count" and log.value is not None:
            log.delta = int(round(log.value))
            log.value = None
            converted += 1
    return converted


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
    """
    Create a new Action belonging to the current authenticated user from submitted form data.

    On valid submission, parses the form's `properties` field as JSON (empty string -> {}), creates and persists the Action, flashes a success message, and redirects to the actions list. If the properties JSON is invalid, flashes an error and redirects back to the new-action page. On GET or when validation fails, renders the "new_action.j2" template with the form for user correction.

    Returns:
        A Flask response: a redirect (to the actions list on success or back to the new-action page on JSON error) or the rendered "new_action.j2" template when displaying the form or on validation failure.
    """
    user = current_user()
    assert user is not None

    form = NewActionForm()
    if form.validate_on_submit():
        name = form.name.data
        notes = form.notes.data
        kind = form.kind.data or "count"
        unit = (form.unit.data or "").strip()
        properties_raw = form.properties.data or "{}"
        properties = {}

        try:
            properties = json.loads(properties_raw.strip())
            if not isinstance(properties, dict):
                flash("Properties must be a JSON object.", "error")
                return render_template("new_action.j2", form=form)
        except json.JSONDecodeError:
            flash("Invalid JSON in properties", "error")
            return render_template("new_action.j2", form=form)

        action = Action(
            name=name,
            user_id=user.id,
            notes=notes,
            kind=kind,
            unit=unit,
            properties=properties,
        )
        db_session.add(action)

        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            form.name.errors = ["Duplicate action name."]
            return render_template("new_action.j2", form=form)

        flash(f"Action '{name}' created successfully!", "info")
        return redirect(url_for("action.list_actions"))

    return render_template("new_action.j2", form=form)


# Edit action
@action_bp.route("/edit/action/<int:action_id>", methods=["GET", "POST"])
@login_required
def edit_action(action_id):
    """
    Render and handle the edit form for an Action owned by the current user.

    Validates submitted form data, updates the Action's `name`, `notes`, and `properties` (parsed from JSON), commits changes to the database on success, and flashes status messages. If the Action is not found the user is redirected to the actions list. If `properties` contains invalid JSON the form is re-rendered with an error and no database commit is performed. On GET the `properties` field is pre-populated with pretty-printed JSON when appropriate.

    Parameters:
        action_id (int|str): Identifier of the Action to edit.

    Returns:
        A Flask response that either renders the edit form (with the form and action) or redirects to the actions list.
    """
    user = current_user()
    assert user is not None

    action = db_session.query(Action).filter_by(id=action_id, user_id=user.id).first()
    if not action:
        flash("Action not found.", "error")
        return redirect(url_for("action.list_actions"))

    form = EditActionForm(obj=action)  # Pre-fill form with existing data

    if form.validate_on_submit():
        assert form.name.data is not None
        old_kind = action.kind
        new_kind = form.kind.data or "count"
        action.name = form.name.data
        action.kind = new_kind
        action.unit = (form.unit.data or "").strip()
        action.notes = form.notes.data or ""

        properties_raw = form.properties.data or "{}"
        try:
            parsed = json.loads(properties_raw.strip())
            if not isinstance(parsed, dict):
                flash("Properties must be a JSON object.", "error")
                return render_template("edit_action.j2", form=form, action=action)
            action.properties = parsed
        except json.JSONDecodeError:
            flash("Invalid JSON in properties", "error")
            return render_template("edit_action.j2", form=form, action=action)

        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            form.name.errors = ["Duplicate action name."]
            return render_template("edit_action.j2", form=form, action=action)

        if new_kind != old_kind:
            converted = _convert_logs_kind(action, new_kind)
            db_session.commit()
            if converted:
                flash(
                    f"Converted {converted} existing log(s) to the new tracking type.",
                    "info",
                )

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
    """
    Render and process the edit activity form for an ActivityLog owned by the current user.

    Parameters:
        log_id (int): ID of the ActivityLog to edit.

    Behavior:
        - If no ActivityLog with the given ID exists for the current user, flashes an error and redirects to the actions list.
        - On valid form submission, updates the log's delta, notes (defaults to empty string), and properties (parsed from JSON); on JSON parse error flashes an error and re-renders the edit template.
        - Commits changes to the database on successful update and flashes a success message.

    Returns:
        A Flask response: redirects to the actions list when the log is not found, redirects to the related action's history after a successful update, or renders the edit_activity.j2 template for GET requests, validation failures, or JSON parse errors.
    """
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

    if log.action.kind == "measure":
        form = EditMeasurementForm(obj=log)
        form.value.label.text = _measurement_label(log.action)

        if form.validate_on_submit():
            assert form.value.data is not None
            log.value = form.value.data
            log.notes = form.notes.data or ""

            properties_raw = form.properties.data or "{}"
            try:
                parsed = json.loads(properties_raw)
                if not isinstance(parsed, dict):
                    flash("Properties must be a JSON object.", "error")
                    return render_template(
                        "edit_activity.j2", form=form, log=log, is_measure=True
                    )
                log.properties = parsed
            except json.JSONDecodeError:
                flash("Invalid JSON in properties", "error")
                return render_template(
                    "edit_activity.j2", form=form, log=log, is_measure=True
                )

            db_session.commit()
            flash("Activity updated successfully!", "info")
            return redirect(
                url_for("action.view_action_history", action_id=log.action_id)
            )

        if request.method == "GET":
            form.properties.data = (
                json.dumps(log.properties, indent=2)
                if isinstance(log.properties, dict)
                else log.properties
            )

        return render_template("edit_activity.j2", form=form, log=log, is_measure=True)

    form = EditActivityForm(obj=log)

    if form.validate_on_submit():
        assert form.delta.data is not None
        log.delta = form.delta.data
        log.notes = form.notes.data or ""

        properties_raw = form.properties.data or "{}"
        try:
            parsed = json.loads(properties_raw)
            if not isinstance(parsed, dict):
                flash("Properties must be a JSON object.", "error")
                return render_template("edit_activity.j2", form=form, log=log)
            log.properties = parsed
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
    """
    Render the log-activity form for an action and create a new ActivityLog when the submitted form is valid.

    Parameters:
        action_id (int): ID of the action to log the activity for.

    Returns:
        A Flask response: on GET or when the form is invalid, renders the log activity template with the form and action; on successful submission, redirects to the action's history view; if the action does not exist, redirects to the actions list; if the properties field contains invalid JSON, redirects back to the log page.
    """
    user = current_user()
    assert user is not None

    action = db_session.query(Action).filter_by(id=action_id, user_id=user.id).first()
    if not action:
        flash("Action not found", "error")
        return redirect(url_for("action.list_actions"))

    if action.kind == "measure":
        form = LogMeasurementForm()
        form.value.label.text = _measurement_label(action)

        if form.validate_on_submit():
            assert form.value.data is not None

            properties_raw = form.properties.data
            try:
                properties = json.loads(properties_raw) if properties_raw else {}
            except json.JSONDecodeError:
                flash("Invalid JSON in properties", "error")
                return render_template("log_activity.j2", form=form, action=action)

            log = ActivityLog(
                action_id=action.id,
                timestamp=datetime.now(timezone.utc),
                delta=0,
                value=form.value.data,
                notes=form.notes.data,
                properties=properties,
            )
            db_session.add(log)
            db_session.commit()

            flash(
                f"Logged {form.value.data} {action.unit} for '{action.name}'", "success"
            )
            return redirect(url_for("action.view_action_history", action_id=action.id))

        return render_template("log_activity.j2", form=form, action=action)

    form = LogActivityForm()

    if form.validate_on_submit():
        assert form.delta.data is not None
        delta = form.delta.data
        notes = form.notes.data

        properties_raw = form.properties.data
        try:
            properties = json.loads(properties_raw) if properties_raw else {}
        except json.JSONDecodeError:
            flash("Invalid JSON in properties", "error")
            return render_template("log_activity.j2", form=form, action=action)

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
