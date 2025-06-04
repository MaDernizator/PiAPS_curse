from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notification import Notification
from app.models.address import Address
from app.models.user import User
from app.main.extensions import db

notification_bp = Blueprint("notification", __name__)


def _format_message(event: str) -> str:
    parts = event.split(":")
    if parts[0] == "invited" and len(parts) == 4:
        addr = Address.query.get(int(parts[1]))
        inviter = User.query.get(int(parts[2]))
        if addr and inviter:
            return (
                f"{inviter.name} пригласил вас на адрес "
                f"{addr.street} {addr.building_number}, кв. {addr.unit_number}"
            )
    elif parts[0] in {"resident_added", "resident_removed", "role_changed"} and len(parts) >= 2:
        addr = Address.query.get(int(parts[1]))
        if addr:
            changes = {
                "resident_added": "добавлен новый жилец",
                "resident_removed": "жилец удалён",
                "role_changed": "изменена роль жильца",
            }
            return (
                f"На адресе {addr.street} {addr.building_number}, кв. {addr.unit_number} "
                f"{changes.get(parts[0], '')}"
            )
    return event

@notification_bp.route("/", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    only_unread = request.args.get("unread") == "1"
    query = Notification.query.filter_by(user_id=user_id)
    if only_unread:
        query = query.filter_by(viewed=False)
    results = query.order_by(Notification.sent_at.desc()).all()
    return jsonify([
        {
            "id": n.id,
            "event": n.event,
            "message": _format_message(n.event),
            "sent_at": n.sent_at.isoformat(),
            "viewed": n.viewed,
        }
        for n in results
    ])

@notification_bp.route("/<int:notification_id>/view", methods=["PUT"])
@jwt_required()
def mark_viewed(notification_id):
    user_id = int(get_jwt_identity())
    n = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()
    n.viewed = True
    db.session.commit()
    return jsonify({"status": "ok"})
