Here’s a clear **README section** for running your admin seed script using your current synchronous PyMongo + Pydantic setup. I’ll make it concise and step-by-step so it’s easy for anyone to follow.

---

# Seeding Admin User

This script creates a default admin user in your MongoDB database. It is **synchronous**, uses **Pydantic for validation**, and works with your current Flask + PyMongo setup.

## Default Admin Credentials

- **Army Number:** `ADMIN001`
- **Password:** `AdminPass123`

> The password is hashed before saving. You will use the plain text password to log in the first time.

---

## Steps to Run the Seed

### 1. Ensure your virtual environment is activated

```bash
# On Linux/macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

---

### 2. Ensure your project structure supports module imports

Your project root should contain the folders:

```
project_root/
│
├─ core/
│  ├─ __init__.py
│  ├─ db.py
│  └─ ...
├─ seed/
│  ├─ __init__.py
│  └─ create_admin.py
├─ models/
│  └─ schema.py
└─ ...
```

- Make sure both `core/` and `seed/` have **`__init__.py`** files to enable Python package imports.

---

### 3. Run the seed script

From the **project root**, run:

```bash
python -m seed.create_admin
```

**OR** (if your `PYTHONPATH` includes the project root):

```bash
python seed/create_admin.py
```

---

### 4. Expected Output

- If the admin already exists:

```
Admin already exists
```

- If the admin is created:

```
Admin created: army_number=ADMIN001 password=AdminPass123, id=...
```

---

### 5. Verify in MongoDB (Optional)

Open MongoDB shell or Compass and run:

```javascript
use <your_database_name>;
db.users.find({ role: "admin" }).pretty();
```

You should see the newly created admin user.

---

### 6. Notes

- The script is **idempotent** — running it multiple times will not create duplicate admin users.
- Passwords are hashed automatically using the project’s `hash_password` function.
- This script uses the **login-style approach**, so it is fully compatible with your login route and `CreateUserSchema`.

---

If you want, I can also add a **section for creating additional users via Flask `/users` route** to make the README a full admin/user setup guide.

Do you want me to add that?
