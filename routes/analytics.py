from flask import jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from core.db import db
from bson import ObjectId

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.get("/dashboard")
@jwt_required()
def get_dashboard_analytics():
    now = datetime.utcnow()
    first_day_this_month = datetime(now.year, now.month, 1)
    
    # Handle previous month
    if now.month == 1:
        first_day_prev_month = datetime(now.year-1, 12, 1)
    else:
        first_day_prev_month = datetime(now.year, now.month-1, 1)
    last_day_prev_month = first_day_this_month - timedelta(seconds=1)

    def calculate_percentage(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)

    # --- USERS ---
    total_users = db.users.count_documents({})
    users_this_month = db.users.count_documents({"created_at": {"$gte": first_day_this_month}})
    users_prev_month = db.users.count_documents({
        "created_at": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}
    })
    users_pct = calculate_percentage(users_this_month, users_prev_month)

    # --- PERSONNELS (exclude soft-deleted) ---
    not_deleted_query = {"$or": [{"isDeleted": False}, {"isDeleted": {"$exists": False}}]}
    total_personnel = db.personnels.count_documents(not_deleted_query)
    personnel_this_month = db.personnels.count_documents({**not_deleted_query, "created_at": {"$gte": first_day_this_month}})
    personnel_prev_month = db.personnels.count_documents({
        **not_deleted_query,
        "created_at": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}
    })
    personnel_pct = calculate_percentage(personnel_this_month, personnel_prev_month)

    # --- DELETED PERSONNEL ---
    total_deleted = db.personnels.count_documents({"isDeleted": True})
    deleted_this_month = db.personnels.count_documents({"isDeleted": True, "created_at": {"$gte": first_day_this_month}})
    deleted_prev_month = db.personnels.count_documents({
        "isDeleted": True,
        "created_at": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}
    })
    deleted_pct = calculate_percentage(deleted_this_month, deleted_prev_month)

    # --- NEW PERSONNEL (added this month) ---
    new_personnel = personnel_this_month
    new_personnel_prev_month = personnel_prev_month
    new_personnel_pct = calculate_percentage(new_personnel, new_personnel_prev_month)

    # --- DATABASES ---
    total_dbs = db.dbs.count_documents({})
    dbs_this_month = db.dbs.count_documents({"created_at": {"$gte": first_day_this_month}})
    dbs_prev_month = db.dbs.count_documents({
        "created_at": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}
    })
    dbs_pct = calculate_percentage(dbs_this_month, dbs_prev_month)

    return jsonify({
        "message": "Dashboard analytics fetched successfully",
        "statusCode": 200,
        "data": {
            "users": {
                "total": total_users,
                "percentage_increase": users_pct
            },
            "personnel": {
                "total": total_personnel,
                "percentage_increase": personnel_pct
            },
            "deleted_personnel": {
                "total": total_deleted,
                "percentage_increase": deleted_pct
            },
            "new_personnel": {
                "total": new_personnel,
                "percentage_increase": new_personnel_pct
            },
            "databases": {
                "total": total_dbs,
                "percentage_increase": dbs_pct
            }
        }
    }), 200

@analytics_bp.get("/personnels/db/<db_id>")
@jwt_required()
def get_personnel_analytics_by_db(db_id):
    # Validate DB ID
    try:
        db_obj_id = ObjectId(db_id)
    except:
        return jsonify({"message": "Invalid DB ID", "statusCode": 400}), 400

    now = datetime.utcnow()
    first_day_this_month = datetime(now.year, now.month, 1)

    # Previous month
    if now.month == 1:
        first_day_prev_month = datetime(now.year - 1, 12, 1)
    else:
        first_day_prev_month = datetime(now.year, now.month - 1, 1)
    last_day_prev_month = first_day_this_month - timedelta(seconds=1)

    def percentage_increase(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)

    query_base = {"db_id": str(db_obj_id)}

    # --- TOTAL PERSONNEL ---
    total_personnel = db.personnels.count_documents(query_base)
    personnel_this_month = db.personnels.count_documents({
        **query_base,
        "created_at": {"$gte": first_day_this_month}
    })
    personnel_prev_month = db.personnels.count_documents({
        **query_base,
        "created_at": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}
    })
    total_pct = percentage_increase(personnel_this_month, personnel_prev_month)

    # --- ACTIVE PERSONNEL ---
    active_query = {**query_base, "status": "active"}
    total_active = db.personnels.count_documents(active_query)
    active_this_month = db.personnels.count_documents({
        **active_query,
        "created_at": {"$gte": first_day_this_month}
    })
    active_prev_month = db.personnels.count_documents({
        **active_query,
        "created_at": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}
    })
    active_pct = percentage_increase(active_this_month, active_prev_month)

    # --- INACTIVE PERSONNEL ---
    inactive_query = {**query_base, "status": "inactive"}
    total_inactive = db.personnels.count_documents(inactive_query)
    inactive_this_month = db.personnels.count_documents({
        **inactive_query,
        "created_at": {"$gte": first_day_this_month}
    })
    inactive_prev_month = db.personnels.count_documents({
        **inactive_query,
        "created_at": {"$gte": first_day_prev_month, "$lte": last_day_prev_month}
    })
    inactive_pct = percentage_increase(inactive_this_month, inactive_prev_month)

    return jsonify({
        "message": "Personnel analytics fetched successfully",
        "statusCode": 200,
        "data": {
            "total_personnel": {
                "total": total_personnel,
                "percentage_increase": total_pct
            },
            "total_active_personnel": {
                "total": total_active,
                "percentage_increase": active_pct
            },
            "total_inactive_personnel": {
                "total": total_inactive,
                "percentage_increase": inactive_pct
            }
        }
    }), 200
