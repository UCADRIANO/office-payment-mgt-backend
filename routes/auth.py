from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from core.db import db
from core.security import verify_password, hash_password
from models.schema import LoginSchema, ChangePasswordSchema, CreateUserSchema
from bson import ObjectId
from pydantic import ValidationError

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    try:
        data = LoginSchema(**request.get_json())
    except ValidationError as e:
        return {
            "message": e.errors(), 
            "statusCode": 400, 
            "data": {}
        }, 400

    user = db.users.find_one({"army_number": data.army_number})
    if not user:
        return {
            "message": "Invalid credentials", 
            "statusCode": 401, 
            "data": {}
        }, 401

    user = db.users.find_one({"army_number": data.army_number})
    if not user or not verify_password(data.password, user["password_hash"]):
        return {
            "message": "Invalid credentials", 
            "statusCode": 401,
            "data": {}
        }, 401


    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={
            "role": user["role"],
            "army_number": user["army_number"],
            "allowed_dbs": user.get("allowed_dbs", [])
        }
    )

    user_schema = CreateUserSchema(**user)
    user_data = user_schema.dict(exclude={"password_hash"})
    user_data = user_schema.dict(exclude={"created_at"})

    return {
        "message": "Login successfully",
        "statusCode": 200,
        "data": {
            "token": token,
            "user": user_data
        }
    }


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user_id = get_jwt_identity()

    try:
        data = ChangePasswordSchema(**request.get_json())
    except ValidationError as e:
        return {"message": e.errors()}, 400

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"message": "User not found"}, 404

    valid = False

    if user.get("generated_password_hash") and verify_password(data.old_password, user["generated_password_hash"]):
        valid = True
    elif user.get("password_hash") and verify_password(data.old_password, user["password_hash"]):
        valid = True

    if not valid:
        return {"message": "Old password incorrect"}, 400

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password_hash": hash_password(data.new_password),
                "generated_password_hash": None,
            }
        }
    )

    return {"msg": "Password updated successfully"}
