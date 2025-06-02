from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.address_service import AddressService
from app.dto.address_schema import AddressCreateSchema

address_bp = Blueprint("address", __name__)

@address_bp.route("/", methods=["POST"])
@jwt_required()
def create_address():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    errors = AddressCreateSchema().validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    address = AddressService.create_address(data, user_id)
    return jsonify(address), 201


@address_bp.route("/", methods=["GET"])
@jwt_required()
def list_user_addresses():
    user_id = int(get_jwt_identity())
    result = AddressService.list_user_addresses(user_id)
    return jsonify(result), 200


@address_bp.route("/join", methods=["POST"])
@jwt_required()
def join_by_code():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    code = data.get("owner_code")
    if not code:
        return jsonify({"error": "Owner code is required"}), 400

    try:
        address = AddressService.join_by_code(user_id, code)
        return jsonify({"message": f"Successfully joined address {address['id']}"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
