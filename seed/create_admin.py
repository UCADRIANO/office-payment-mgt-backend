from core.db import db
from core.security import hash_password
from models.schema import CreateAdminSchema, Role
from pydantic import ValidationError

def create_admin():
    # Check if admin already exists
    exists = db.users.find_one({"role": Role.admin.value})
    if exists:
        print("Admin already exists")
        return

    # Admin data
    admin_data = {
        "first_name": "Uchenna",
        "last_name": "Opara",
        "army_number": "N/17541",
        "role": Role.admin.value,
        "password_hash": hash_password("AdminPassSuper123"),
        "access_all_db": True
    }

    # Validate with Pydantic
    try:
        admin_schema = CreateAdminSchema(**admin_data)
    except ValidationError as e:
        print("Validation error:", e.errors())
        return

    # Insert into MongoDB
    result = db.users.insert_one(admin_schema.dict())
    print(f"Admin created: army_number={admin_data['army_number']} password=AdminPassSuper123, id={result.inserted_id}")


if __name__ == "__main__":
    create_admin()
