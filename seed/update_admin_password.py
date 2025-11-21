from core.db import db
from core.security import hash_password, verify_password
from models.schema import ChangePasswordSchema, Role
from pydantic import ValidationError

def change_admin_password():
    # Validate input with Pydantic

    data = {
        "old_password": "AdminPassSuper123",
        "new_password": "Admin123"
    }

    try:
        schema = ChangePasswordSchema(**data)
    except ValidationError as e:
        print("Validation error:", e.errors())
        return

    # Find the admin user
    admin = db.users.find_one({"role": Role.admin.value})
    if not admin:
        print("Admin not found")
        return

    # Verify old password
    if not verify_password(schema.old_password, admin.get("password_hash", "")):
        print("Old password does not match")
        return

    # Hash the new password
    hashed_password = hash_password(schema.new_password)

    # Update in MongoDB
    result = db.users.update_one(
        {"_id": admin["_id"]},
        {"$set": {"password_hash": hashed_password}}
    )

    if result.modified_count == 1:
        print("Password updated successfully")
    else:
        print("Password update failed")


if __name__ == "__main__":
    change_admin_password()
