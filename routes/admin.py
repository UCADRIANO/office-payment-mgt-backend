from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from core.security import hash_password
from models.schema import CreateUserSchema, Role
from models.personnel import CreateDBSchema
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
    # Admin check
    r = admin_only()
    if r:
        return r

    data = request.get_json()

    # Force role to user
    data["role"] = Role.user.value

    # Check duplicate army_number
    if db.users.find_one({"army_number": data.get("army_number")}):
        return jsonify({
            "message": "User already exists",
            "statusCode": 400,
            "data": {}
        }), 400

    # Validate allowed_dbs (now using DB IDs)
    allowed = data.get("allowed_dbs", [])

    if not isinstance(allowed, list):
        return jsonify({
            "message": "allowed_dbs must be a list",
            "statusCode": 400,
            "data": {}
        }), 400

    validated_db_ids = []

    for db_id in allowed:
        # Ensure valid ObjectId
        try:
            obj_id = ObjectId(db_id)
        except:
            return jsonify({
                "message": "Invalid DB ID format",
                "statusCode": 400,
                "data": {"invalid": db_id}
            }), 400

        # Ensure the DB exists
        if not db.dbs.find_one({"_id": obj_id}):
            return jsonify({
                "message": "Database not found",
                "statusCode": 404,
                "data": {"invalid": db_id}
            }), 404

        # Store DB id as string (schema expects List[str])
        validated_db_ids.append(db_id)

    # Replace allowed_dbs with validated list
    data["allowed_dbs"] = validated_db_ids

    # Hash password
    hashed_password = hash_password(data["password"])
    data["password_hash"] = hashed_password
    data['is_generated'] = True

    # Pydantic validation
    try:
        user_schema = CreateUserSchema(**data)
    except ValidationError as e:
        return jsonify({
            "message": e.errors(),
            "statusCode": 400,
            "data": {}
        }), 400

    # Insert into MongoDB
    result = db.users.insert_one(
        user_schema.dict(by_alias=True, exclude_none=True)
    )

    return jsonify({
        "message": "User created successfully",
        "statusCode": 201,
        "data": {"id": str(result.inserted_id)}
    }), 201


@admin_bp.patch("/users/<userId>")
@jwt_required()
def update_user(userId: str):
    # Admin check
    r = admin_only()
    if r:
        return r

    try:
        obj_id = ObjectId(userId)
    except errors.InvalidId:
        return jsonify({"message": "Invalid user ID", "statusCode": 400}), 400

    user = db.users.find_one({"_id": obj_id})
    if not user:
        return jsonify({"message": "User not found", "statusCode": 404}), 404

    data = request.get_json() or {}

    # Remove forbidden update fields
    for field in ["_id", "role", "password_hash", "access_all_db", "army_number", "created_at"]:
        data.pop(field, None)

    # Validate allowed_dbs if included
    if "allowed_dbs" in data:
        if not isinstance(data["allowed_dbs"], list):
            return jsonify({
                "message": "allowed_dbs must be a list",
                "statusCode": 400
            }), 400

    # Convert string IDs in request to ObjectIds
    try:
        requested_ids = [str(dbid) for dbid in data["allowed_dbs"]]
    except Exception:
        return jsonify({
            "message": "One or more allowed_dbs values are not valid ObjectIds",
            "statusCode": 400
        }), 400

    # Fetch all valid DB IDs
    existing_ids = {str(d["_id"]) for d in db.dbs.find({}, {"_id": 1})}

    # Compare
    invalid = [str(id) for id in requested_ids if id not in existing_ids]

    if invalid:
        return jsonify({
            "message": "Invalid DB IDs in allowed_dbs",
            "statusCode": 400,
            "data": {"invalid": invalid}
        }), 400

    # Replace string IDs with ObjectIds for storage
    data["allowed_dbs"] = requested_ids

    # Merge updates
    user_json = {
        **user,
        "_id": str(user["_id"]),
        "allowed_dbs": [str(i) for i in user.get("allowed_dbs", [])]
    }

    updated_data = {**user_json, **data}

    # Validate with Pydantic
    try:
        validated = CreateUserSchema(**updated_data)
    except ValidationError as e:
        return jsonify({"message": e.errors(), "statusCode": 400}), 400

    # Update
    db.users.update_one(
        {"_id": obj_id},
        {"$set": validated.dict(
            by_alias=False, exclude_none=True, exclude={"password_hash"})}
    )

    return jsonify({
        "message": "User updated successfully",
        "statusCode": 200,
        "data": {}
    }), 200


@admin_bp.delete("/users/<userId>")
@jwt_required()
def delete_user(userId: str):
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

    # Check if user exists
    user = db.users.find_one({"_id": obj_id})
    if not user:
        return jsonify({
            "message": "User not found",
            "statusCode": 404,
            "data": {}
        }), 404

    current_user_id = get_jwt_identity()
    if str(current_user_id) == str(obj_id):
        return jsonify({
            "message": "Admins cannot delete themselves",
            "statusCode": 400,
            "data": {}
        }), 400

    # Delete user
    db.users.delete_one({"_id": obj_id})

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

        user.pop("password_hash", None)
        user.pop("created_at", None)

        # Populate allowed_dbs with full DB details
        if user.get("allowed_dbs"):
            object_ids = [ObjectId(db_id) for db_id in user["allowed_dbs"]]

            db_docs = list(db.dbs.find({"_id": {"$in": object_ids}}))

            full_dbs = [
                CreateDBSchema(**db_doc).dict(by_alias=False,
                                              exclude={"created_at"})
                for db_doc in db_docs
            ]

            user["allowed_dbs"] = full_dbs
        else:
            user["allowed_dbs"] = []

        clean_user = CreateUserSchema(**user).dict(
            exclude={"password_hash", "created_at"},
            by_alias=False
        )

        clean_users.append(clean_user)

    return jsonify({
        "message": "Users fetched successfully",
        "statusCode": 200,
        "data": clean_users
    }), 200


@admin_bp.post("dbs")
@jwt_required()
def create_db():
    # Check if current user is admin
    r = admin_only()
    if r:
        return r

    # Get request JSON
    data = request.get_json()

    # Check if db already exists
    if db.dbs.find_one({"short_code": data.get("short_code")}):
        return jsonify({
            "message": "Database already exists",
            "statusCode": 400,
            "data": {}
        }), 400

        # Validate input with Pydantic
    try:
        db_schema = CreateDBSchema(**data)
    except ValidationError as e:
        return jsonify({
            "message": e.errors(),
            "statusCode": 400,
            "data": {}
        }), 400

    db_dict = db_schema.dict(by_alias=True, exclude_none=True)

    # Insert into MongoDB
    db.dbs.insert_one(db_dict)

    return jsonify({
        "message": "Database created successfully",
        "statusCode": 201,
        "data": {}
    }), 201


@admin_bp.get("/dbs")
@jwt_required()
def get_all_dbs():
    # Get current user
    current_user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return jsonify({
            "message": "User not found",
            "statusCode": 404,
            "data": {}
        }), 404

    # If user is admin, return all databases
    if user.get("role") == Role.admin.value:
        dbs = list(db.dbs.find())
    else:
        # For non-admin users, filter databases based on allowed_dbs
        allowed_db_ids = user.get("allowed_dbs", [])
        if allowed_db_ids:
            object_ids = [ObjectId(db_id) for db_id in allowed_db_ids]
            dbs = list(db.dbs.find({"_id": {"$in": object_ids}}))
        else:
            dbs = []

    clean_dbs = []
    for item in dbs:
        clean_dbs.append(
            CreateDBSchema(**item).dict(
                exclude={"created_at"},
                by_alias=False
            )
        )

    return jsonify({
        "message": "Database fetched successfully",
        "statusCode": 200,
        "data": clean_dbs
    }), 200


@admin_bp.patch("/dbs/<dbId>")
@jwt_required()
def update_db(dbId: str):
    # Admin check
    r = admin_only()
    if r:
        return r

    try:
        obj_id = ObjectId(dbId)
    except errors.InvalidId:
        return jsonify({
            "message": "Invalid database ID",
            "statusCode": 400,
            "data": {}
        }), 400

    # Fetch the db
    database = db.dbs.find_one({"_id": obj_id})
    if not database:
        return jsonify({
            "message": "Database not found",
            "statusCode": 404,
            "data": {}
        }), 404

    # Get input data
    data = request.get_json() or {}

    # Prevent changing immutable fields
    for field in ["_id", "created_at"]:
        data.pop(field, None)

    # Merge existing db with updates
    updated_data = {**database, **data}

    # Validate using Pydantic
    try:
        db_schema = CreateDBSchema(**updated_data)
    except ValidationError as e:
        return jsonify({
            "message": e.errors(),
            "statusCode": 400,
            "data": {}
        }), 400

    # Update in MongoDB
    update_dict = db_schema.dict(
        exclude={"created_at", "id"},
        by_alias=True,
        exclude_none=True
    )

    db.dbs.update_one(
        {"_id": obj_id},
        {"$set": update_dict}
    )

    return jsonify({
        "message": "Database updated successfully",
        "statusCode": 200,
        "data": db_schema.dict(by_alias=False, exclude={"created_at"})
    }), 200


@admin_bp.delete("/dbs/<dbId>")
@jwt_required()
def delete_db(dbId: str):
    # Admin check
    r = admin_only()
    if r:
        return r

    # Convert to ObjectId
    try:
        obj_id = ObjectId(dbId)
    except errors.InvalidId:
        return jsonify({
            "message": "Invalid database ID",
            "statusCode": 400,
            "data": {}
        }), 400

    # Check if DB exists
    database = db.dbs.find_one({"_id": obj_id})
    if not database:
        return jsonify({
            "message": "Database not found",
            "statusCode": 404,
            "data": {}
        }), 404

    db.dbs.delete_one({"_id": obj_id})

    # Delete all personnel belonging to this DB
    db.personnel.delete_many({"db_id": dbId})

    db.users.update_many(
        {},
        {"$pull": {"allowed_dbs": dbId}}
    )

    return jsonify({
        "message": "Database deleted successfully",
        "statusCode": 200,
        "data": {}
    }), 200
