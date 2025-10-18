from flask import Blueprint, request, jsonify
from database import db_session
from models import Action, ActivityLog
from datetime import datetime, timezone

from auth_helpers import user_from_token, token_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


# List actions
@api_bp.route("/actions", methods=["GET"])
@token_required
def api_list_actions():
    user = user_from_token()
    assert user is not None

    actions = db_session.query(Action).filter_by(user_id=user.id).all()
    return jsonify(
        [
            {"id": a.id, "name": a.name, "notes": a.notes, "properties": a.properties}
            for a in actions
        ]
    )


# Log a new activity
@api_bp.route("/actions/<int:action_id>/logs", methods=["POST"])
@token_required
def api_add_log(action_id):
    user = user_from_token()
    assert user is not None

    action = db_session.query(Action).filter_by(id=action_id, user_id=user.id).first()
    if not action:
        return jsonify({"error": "Action not found"}), 404

    data = request.get_json()
    note = data.get("note", "")
    delta = int(data.get("delta", 1))
    properties = data.get("properties", {})

    log = ActivityLog(
        action_id=action.id,
        timestamp=datetime.now(timezone.utc),
        delta=delta,
        note=note,
        properties=properties,
    )
    db_session.add(log)
    db_session.commit()

    return jsonify({"status": "ok", "message": f"Logged '{action.name}'"}), 201
