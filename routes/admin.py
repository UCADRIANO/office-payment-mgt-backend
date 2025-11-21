from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from core.security import hash_password
from models.schema import CreateUserSchema, Role
import secrets
from pydantic import ValidationError
from core.db import db
from bson import ObjectId

admin_bp = Blueprint("admin", __name__)


def admin_only():
    claims = get_jwt()
    if claims.get("role") != Role.admin.value:
        return jsonify({
            "message": "Unauthorized access - Admin only",
            "data": {}
        }), 403

@admin_bp.post("/users")
@jwt_required()
def create_user():
    # Check if current user is admin
    r = admin_only()
    if r:
        return r

    # Get request JSON
    data = request.get_json()

    # Force role to user
    data["role"] = Role.user.value

    # Check if army_number already exists
    if db.users.find_one({"army_number": data.get("army_number")}):
        return jsonify({
            "message": "User already exists",
            "statusCode": 400,
            "data": {}
        }), 400

    # Generate random password
    gen_pass = secrets.token_urlsafe(8)
    hashed_password = hash_password(gen_pass)

    # Combine input data with hashed password
    user_data = {**data, "password_hash": hashed_password}

    # Validate input with Pydantic
    try:
        user_schema = CreateUserSchema(**user_data)
    except ValidationError as e:
        return jsonify({
            "message": e.errors(),
            "statusCode": 400,
            "data": {}
        }), 400

    # Insert into MongoDB
    result = db.users.insert_one(user_schema.dict())

    return jsonify({
        "message": "User created successfully",
        "statusCode": 201,
        "data": {
            "generated_password": gen_pass,
            "id": str(result.inserted_id)
        }
    }), 201


@admin_bp.put("/users/<userId>")
@jwt_required()
def update_user(userId: str):
    print("-----", userId, "-----")
    # Admin check
    r = admin_only()
    if r:
        return r

    # Find the user
    user = db.users.find_one({"_id": userId})
    if not user:
        return jsonify({
            "message": "User not found",
            "statusCode": 404,
            "data": {}
        }), 404

    # Get input data
    data = request.get_json() or {}

    # Prevent changing immutable fields
    data.pop("role", None)
    data.pop("password_hash", None)
    data.pop("_id", None)
    data.pop("army_number", None)
    data.pop("access_all_db", None)

    # Merge existing data with updates
    updated_data = {**user, **data}

    # Validate using Pydantic
    try:
        user_schema = CreateUserSchema(**updated_data)
    except ValidationError as e:
        return jsonify({
            "message": e.errors(),
            "statusCode": 400,
            "data": {}
        }), 400

    # Update in MongoDB (excluding password_hash)
    db.users.update_one(
        {"_id": userId},
        {"$set": user_schema.dict(exclude={"password_hash"})}
    )

    return jsonify({
        "message": "User updated successfully",
        "statusCode": 200,
        "data": { **updated_data }
    }), 200