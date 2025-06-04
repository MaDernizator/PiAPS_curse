from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.notification_service import NotificationService

notification_bp = Blueprint("notification", __name__)

@notification_bp.route("/", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    notifications = NotificationService.list_notifications(user_id)
    return jsonify(notifications), 200

@notification_bp.route("/test", methods=["POST"])
@jwt_required()
def create_test_notification():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    event = data.get("event", "Test notification")
    notification = NotificationService.create_notification(user_id, event)
    return jsonify(notification), 201
