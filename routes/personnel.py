from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from core.security import hash_password
from models.personnel import Personnel
from pydantic import ValidationError
from core.db import db
from bson import ObjectId, errors

personnel_bp = Blueprint("personnels", __name__)

@personnel_bp.post("/")
@jwt_required()
def create_personnel():
    data = request.get_json()

    db_id = data.get("db_id")
    if not db_id:
        return jsonify({"message": "db_id is required", "statusCode": 400}), 400

    # Validate DB ID
    try:
        obj_id = ObjectId(db_id)
    except:
        return jsonify({"message": "Invalid db_id", "statusCode": 400}), 400

    # Ensure DB exists
    if not db.dbs.find_one({"_id": obj_id}):
        return jsonify({"message": "DB not found", "statusCode": 404}), 404

    # Unique army_number within the same db
    if db.personnels.find_one({"army_number": data["army_number"], "db_id": db_id}):
        return jsonify({
            "message": "Personnel with this army_number already exists in this DB",
            "statusCode": 400
        }), 400

    try:
        personnel_schema = Personnel(**data)
    except ValidationError as e:
        return jsonify({"message": e.errors(), "statusCode": 400}), 400

    doc = personnel_schema.dict(by_alias=True)
    doc.pop("_id", None)
    db.personnels.insert_one(doc)

    return jsonify({
        "message": "Personnel created successfully",
        "statusCode": 201,
        "data": {}
    }), 201


@personnel_bp.get("/")
@jwt_required()
def get_all_personnels():
    db_id = request.args.get("db_id")

    query = {}
    if db_id:
        query["db_id"] = db_id

    personnels = list(db.personnels.find(query))

    # Transform documents for frontend
    formatted_personnels = []
    for p in personnels:
        p_formatted = p.copy()  # avoid modifying original
        p_formatted["id"] = str(p_formatted.pop("_id"))  # replace _id with id
        p_formatted.pop("db_id", None)  # remove db_id if exists
        formatted_personnels.append(p_formatted)

    return jsonify({
        "message": "Personnels fetched successfully",
        "statusCode": 200,
        "data": formatted_personnels
    }), 200


@personnel_bp.get("/<personnelId>")
@jwt_required()
def get_personnel(personnelId):
    try:
        obj_id = ObjectId(personnelId)
    except:
        return jsonify({"message": "Invalid personnel ID", "statusCode": 400}), 400

    personnel = db.personnels.find_one({"_id": obj_id})
    if not personnel:
        return jsonify({
            "message": "Personnel not found",
            "statusCode": 404
        }), 404

    # personnel["_id"] = str(personnel["_id"])
    personnel["id"] = str(personnel.pop("_id"))  # replace _id with id
    personnel.pop("db_id", None)  # remove db_id if exists

    return jsonify({
        "message": "Personnel fetched successfully",
        "statusCode": 200,
        "data": personnel
    }), 200


@personnel_bp.patch("/<personnelId>")
@jwt_required()
def update_personnel(personnelId):
    try:
        obj_id = ObjectId(personnelId)
    except:
        return jsonify({"message": "Invalid personnel ID", "statusCode": 400}), 400

    personnel = db.personnels.find_one({"_id": obj_id})
    if not personnel:
        return jsonify({
            "message": "Personnel not found",
            "statusCode": 404
        }), 404

    data = request.get_json() or {}

    # If db_id is being changed, validate it
    if "db_id" in data:
        new_db_id = data["db_id"]
        try:
            new_obj_id = ObjectId(new_db_id)
        except:
            return jsonify({"message": "Invalid db_id", "statusCode": 400}), 400

        if not db.dbs.find_one({"_id": new_obj_id}):
            return jsonify({"message": "DB not found", "statusCode": 404}), 404

    # If army_number is changing, ensure uniqueness per DB
    new_army_num = data.get("army_number", personnel["army_number"])
    new_db_id = data.get("db_id", personnel["db_id"])

    exists = db.personnels.find_one({
        "army_number": new_army_num,
        "db_id": new_db_id,
        "_id": {"$ne": obj_id}
    })

    if exists:
        return jsonify({
            "message": "Personnel with this army_number already exists in this DB",
            "statusCode": 400
        }), 400

    updated = {**personnel, **data}

    try:
        updated_schema = Personnel(**updated)
    except ValidationError as e:
        return jsonify({"message": e.errors(), "statusCode": 400}), 400

    print(f"------ Updated schema -------, {updated_schema}")

    payload = updated_schema.dict(by_alias=True)
    payload.pop("_id", None) 
    payload.pop("id", None) 
    db.personnels.update_one(
        {"_id": obj_id},
        {"$set": payload}
    )

    return jsonify({
        "message": "Personnel updated successfully",
        "statusCode": 200
    }), 200


@personnel_bp.delete("/<personnelId>")
@jwt_required()
def delete_personnel(personnelId):
    try:
        obj_id = ObjectId(personnelId)
    except:
        return jsonify({"message": "Invalid personnel ID", "statusCode": 400}), 400

    personnel = db.personnels.find_one({"_id": obj_id})
    if not personnel:
        return jsonify({"message": "Personnel not found", "statusCode": 404}), 404

    db.personnels.delete_one({"_id": obj_id})

    return jsonify({
        "message": "Personnel deleted successfully",
        "statusCode": 200
    }), 200
