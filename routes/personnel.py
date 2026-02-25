from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.personnel import Personnel, PersonnelStatus
from pydantic import ValidationError
from core.db import db
from bson import ObjectId, errors
from math import ceil

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
        data["status"] = PersonnelStatus.ACTIVE
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

    query = {
        "$or": [{"isDeleted": False}, {"isDeleted": {"$exists": False}}]
    }
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

    db.personnels.update_one({"_id": obj_id}, {"$set": {"isDeleted": True}})

    return jsonify({
        "message": "Personnel deleted successfully",
        "statusCode": 200
    }), 200


@personnel_bp.get("/db/<db_id>")
@jwt_required()
def get_personnel_by_db(db_id):
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    search = request.args.get("search")

    if page < 1:
        page = 1
    if limit < 1:
        limit = 10

    skip = (page - 1) * limit

    query = {
        "$or": [{"isDeleted": False}, {"isDeleted": {"$exists": False}}]
    }

    if db_id:
        query["db_id"] = db_id

    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"middle_name": {"$regex": search, "$options": "i"}},
            {"army_number": {"$regex": search, "$options": "i"}},
        ]

    total = db.personnels.count_documents(query)

    personnels = list(
        db.personnels
        .find(query)
        .skip(skip)
        .limit(limit)
    )

    formatted_personnels = []
    for p in personnels:
        p_formatted = p.copy()
        p_formatted["id"] = str(p_formatted.pop("_id"))
        p_formatted.pop("db_id", None)
        formatted_personnels.append(p_formatted)

    page_count = ceil(total / limit) if total else 1

    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "pageCount": page_count,
        "hasNextPage": page < page_count,
        "hasPrevPage": page > 1
    }

    return jsonify({
        "message": "Personnels fetched successfully",
        "statusCode": 200,
        "data": {
            "data": formatted_personnels,
            "meta": pagination
        },
    }), 200


@personnel_bp.post("/upload")
@jwt_required()
def bulk_personnel_upload():
    data = request.get_json()
    
    if not isinstance(data, list):
        return jsonify({
            "message": "Payload must be an array of Personnel",
            "statusCode": 400
        }), 400

    # Extract db_id (must be same for all entries)
    db_id = data[0].get("db_id")
    if not db_id:
        return jsonify({"message": "db_id is required", "statusCode": 400}), 400

    # Validate DB ID format
    try:
        obj_id = ObjectId(db_id)
    except:
        return jsonify({"message": "Invalid db_id", "statusCode": 400}), 400

    # Ensure DB exists
    if not db.dbs.find_one({"_id": obj_id}):
        return jsonify({"message": "DB not found", "statusCode": 404}), 404

    valid_docs = []
    errors = []

    for index, item in enumerate(data):
        # ensure db_id consistency
        if item.get("db_id") != db_id:
            errors.append({
                "index": index,
                "error": "db_id mismatch in item"
            })
            continue

        # unique army_number per DB
        if db.personnels.find_one({"army_number": item["army_number"], "db_id": db_id}):
            errors.append({
                "index": index,
                "error": f"Personnel with army_number {item['army_number']} already exists"
            })
            continue

        # Pydantic validation
        try:
            p = Personnel(**item)
        except ValidationError as e:
            errors.append({
                "index": index,
                "error": e.errors()
            })
            continue

        doc = p.dict(by_alias=False)
        doc.pop("_id", None)
        valid_docs.append(doc)

    # Insert valid docs
    if valid_docs:
        db.personnels.insert_many(valid_docs)

    return jsonify({
        "message": "Bulk upload completed",
        "statusCode": 207 if errors else 201,
        "data": {
            "inserted": len(valid_docs),
            "failed": errors
        }
    }), 207 if errors else 201


@personnel_bp.delete("/bulk-delete")
@jwt_required()
def bulk_delete_personnel():
    data = request.get_json()

    if not data or "personnels_id" not in data:
        return jsonify({
            "message": "personnels_id is required",
            "statusCode": 400
        }), 400

    personnels_id = data["personnels_id"]

    if not isinstance(personnels_id, list) or not personnels_id:
        return jsonify({
            "message": "personnels_id must be a non-empty list",
            "statusCode": 400
        }), 400

    object_ids = []
    invalid_ids = []

    for pid in personnels_id:
        try:
            object_ids.append(ObjectId(pid))
        except Exception:
            invalid_ids.append(pid)

    if invalid_ids:
        return jsonify({
            "message": "Invalid personnel ID(s)",
            "invalid_ids": invalid_ids,
            "statusCode": 400
        }), 400

    result = db.personnels.update_many(
        {"_id": {"$in": object_ids}},
        {"$set": {"isDeleted": True}}
    )

    if result.matched_count == 0:
        return jsonify({
            "message": "No personnels found to delete",
            "statusCode": 404
        }), 404

    return jsonify({
        "message": "Personnels deleted successfully",
        "statusCode": 200
    }), 200
