from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.enums import UserRole
import os

log_bp = Blueprint("log", __name__)

@log_bp.route("/", methods=["GET"])
@jwt_required()
def get_logs():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != UserRole.ADMIN:
        return jsonify({"error": "forbidden"}), 403

    start = int(request.args.get("start", 0))
    log_file = current_app.config.get("LOG_FILE", os.path.join("logs", "app.log"))
    if not os.path.exists(log_file):
        return jsonify({"lines": [], "total": 0})

    with open(log_file, "r") as f:
        lines = f.readlines()
    total = len(lines)
    return jsonify({"lines": lines[start:], "total": total})
