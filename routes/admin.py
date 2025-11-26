from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from core.security import hash_password
from models.schema import CreateUserSchema, Role
import secrets
from pydantic import ValidationError
from core.db import db
from bson import ObjectId, errors

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
    hashed_password = hash_password(data['password'])

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
            "id": str(result.inserted_id)
        }
    }), 201


@admin_bp.patch("/users/<userId>")
@jwt_required()
def update_user(userId: str):
    # Admin check
    r = admin_only()
    if r:
        return r

    # Convert userId to ObjectId
    try:
        obj_id = ObjectId(userId)
    except errors.InvalidId:
        return jsonify({
            "message": "Invalid user ID",
            "statusCode": 400,
            "data": {}
        }), 400

    # Fetch the user
    user = db.users.find_one({"_id": obj_id})
    if not user:
        return jsonify({
            "message": "User not found",
            "statusCode": 404,
            "data": {}
        }), 404

    # Get input data
    data = request.get_json() or {}

    # Prevent changing immutable fields
    for field in ["role", "password_hash", "_id", "army_number", "access_all_db", "created_at"]:
        data.pop(field, None)

    # Merge existing user with updates
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

    # Update in MongoDB
    db.users.update_one(
        {"_id": obj_id},
        {"$set": user_schema.dict(exclude={"password_hash"})}
    )

    return jsonify({
        "message": "User updated successfully",
        "statusCode": 200,
        "data": user_schema.dict(by_alias=False, exclude={"password_hash", "created_at"})
    }), 200


@admin_bp.delete("/users/<userId>")
@jwt_required()
def delete_user(userId: str):
    # Admin check
    r = admin_only()
    if r:
        return r

    # Check if user exists
    user = db.users.find_one({"_id": userId})
    if not user:
        return jsonify({
            "message": "User not found",
            "statusCode": 404,
            "data": {}
        }), 404

    current_user_id = get_jwt_identity()
    if str(current_user_id) == str(userId):
        return jsonify({
            "message": "Admins cannot delete themselves",
            "statusCode": 400,
            "data": {}
        }), 400

    # Delete user
    db.users.delete_one({"_id": userId})

    return jsonify({
        "message": "User deleted successfully",
        "statusCode": 200,
        "data": {}
    }), 200


@admin_bp.get("/users")
@jwt_required()
def get_all_users():
    # Admin check
    r = admin_only()
    if r:
        return r

    users = list(db.users.find({"role": {"$ne": "admin"}}))

    clean_users = []
    for user in users:
        clean_users.append(
            CreateUserSchema(**user).dict(
                exclude={"password_hash", "created_at"},
                by_alias=False
            )
)

    return jsonify({
        "message": "Users fetched successfully",
        "statusCode": 200,
        "data": clean_users
    }), 200
