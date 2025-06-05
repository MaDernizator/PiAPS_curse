from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.resident_service import ResidentService
from app.models.enums import ResidentRole

resident_bp = Blueprint("resident", __name__)

@resident_bp.route("/<int:address_id>", methods=["GET"])
@jwt_required()
def list_residents(address_id):
    user_id = int(get_jwt_identity())
    try:
        residents = ResidentService.list_residents(user_id, address_id)
        return jsonify(residents), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@resident_bp.route("/<int:address_id>/<int:target_user_id>/toggle-block", methods=["PUT"])
@jwt_required()
def toggle_block_resident(address_id, target_user_id):
    user_id = int(get_jwt_identity())
    try:
        ResidentService.block_resident(user_id, address_id, target_user_id)
        return jsonify({"message": "Resident block toggled"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@resident_bp.route("/<int:address_id>/<int:target_user_id>/role", methods=["PUT"])
@jwt_required()
def update_resident_role(address_id, target_user_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    new_role = data.get("role")

    if new_role not in ResidentRole.__members__:
        return jsonify({"error": "Invalid role"}), 400

    try:
        ResidentService.update_role(user_id, address_id, target_user_id, new_role)
        return jsonify({"message": "Role updated"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
