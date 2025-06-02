from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.invitation_service import InvitationService
from app.dto.invitation_schema import InvitationCreateSchema

invitation_bp = Blueprint("invitation", __name__)

@invitation_bp.route("/", methods=["POST"])
@jwt_required()
def invite_user():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    errors = InvitationCreateSchema().validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        result = InvitationService.create_invitation(data, user_id)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@invitation_bp.route("/accept", methods=["POST"])
@jwt_required()
def accept_invitation():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    code = data.get("code")
    if not code:
        return jsonify({"error": "Invitation code is required"}), 400

    try:
        InvitationService.accept_invitation(code, user_id)
        return jsonify({"message": "Invitation accepted"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
