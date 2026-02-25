# Office Payment Management — Backend

A REST API backend for managing office personnel records, databases, user accounts, and analytics. Built with **Python**, **Flask**, **MongoDB**, and **JWT authentication**.

---

## Tech Stack

| Layer          | Technology                       |
| -------------- | -------------------------------- |
| Framework      | Flask 3.x                        |
| Database       | MongoDB (via PyMongo)            |
| Authentication | JWT (flask-jwt-extended)         |
| Validation     | Pydantic v2                      |
| Password Hash  | Bcrypt (flask-bcrypt)            |
| CORS           | flask-cors                       |
| Package Mgr    | [uv](https://docs.astral.sh/uv/) |
| Python         | ≥ 3.9                            |

---

## Features

- **User & Admin Management** — Create, update, delete users with role-based access control (admin / user).
- **Database (DB) Management** — Create and manage logical databases; assign users to specific DBs via `allowed_dbs`.
- **Personnel Management** — Full CRUD for personnel records, bulk upload, soft-delete, and status tracking.
- **Personnel Status** — Track personnel with multiple statuses: `active`, `inactive`, `awol`, `death`, `rtu`, `posted`, `cse`.
- **Search & Filtering** — Search by name/army number; filter personnel by status.
- **Pagination** — All list endpoints support paginated responses with metadata.
- **Analytics Dashboard** — Aggregated stats with month-over-month percentage changes.

---

## API Endpoints

All protected endpoints require a `Bearer` token in the `Authorization` header.

### Authentication — `/auth`

| Method | Endpoint                | Auth | Description                       |
| ------ | ----------------------- | ---- | --------------------------------- |
| POST   | `/auth/login`           | ✗    | Login with army_number & password |
| POST   | `/auth/change-password` | ✓    | Change own password               |

### Admin — `/admin` _(Admin only)_

#### User Management

| Method | Endpoint                | Description                            |
| ------ | ----------------------- | -------------------------------------- |
| POST   | `/admin/users`          | Create a new user                      |
| GET    | `/admin/users`          | List all users (paginated, searchable) |
| PATCH  | `/admin/users/:userId`  | Update a user                          |
| DELETE | `/admin/users/:userId`  | Delete a user                          |
| POST   | `/admin/reset-password` | Reset a user's password                |

**Query params** for `GET /admin/users`:

| Param    | Default | Description                   |
| -------- | ------- | ----------------------------- |
| `page`   | 1       | Page number                   |
| `limit`  | 10      | Items per page                |
| `search` | —       | Search by name or army number |

#### Database Management

| Method | Endpoint           | Description                            |
| ------ | ------------------ | -------------------------------------- |
| POST   | `/admin/dbs`       | Create a new database                  |
| GET    | `/admin/dbs`       | List databases (paginated, searchable) |
| PATCH  | `/admin/dbs/:dbId` | Update a database                      |
| DELETE | `/admin/dbs/:dbId` | Delete a database & its personnel      |

**Query params** for `GET /admin/dbs`:

| Param    | Default | Description                  |
| -------- | ------- | ---------------------------- |
| `page`   | 1       | Page number                  |
| `limit`  | 10      | Items per page               |
| `search` | —       | Search by name or short code |

### Personnel — `/personnels`

| Method | Endpoint                   | Auth | Description                             |
| ------ | -------------------------- | ---- | --------------------------------------- |
| POST   | `/personnels/`             | ✓    | Create a single personnel               |
| GET    | `/personnels/`             | ✓    | Get all personnel (optionally by db_id) |
| GET    | `/personnels/:personnelId` | ✓    | Get a single personnel by ID            |
| PATCH  | `/personnels/:personnelId` | ✓    | Update a personnel                      |
| DELETE | `/personnels/:personnelId` | ✓    | Soft-delete a personnel                 |
| GET    | `/personnels/db/:db_id`    | ✓    | Get personnel by database (paginated)   |
| POST   | `/personnels/upload`       | ✓    | Bulk upload personnel                   |
| DELETE | `/personnels/bulk-delete`  | ✓    | Bulk soft-delete personnel              |

**Query params** for `GET /personnels/db/:db_id`:

| Param    | Default | Description                                                                            |
| -------- | ------- | -------------------------------------------------------------------------------------- |
| `page`   | 1       | Page number                                                                            |
| `limit`  | 10      | Items per page                                                                         |
| `search` | —       | Search by first name, last name, middle name, or army number                           |
| `filter` | `all`   | Filter by status: `all`, `active`, `inactive`, `awol`, `death`, `rtu`, `posted`, `cse` |

### Analytics — `/analytics`

| Method | Endpoint                          | Auth | Description                                    |
| ------ | --------------------------------- | ---- | ---------------------------------------------- |
| GET    | `/analytics/dashboard`            | ✓    | Global dashboard stats (users, personnel, DBs) |
| GET    | `/analytics/personnels/db/:db_id` | ✓    | Personnel analytics for a specific DB          |

---

## Getting Started

### Prerequisites

- **Python 3.9+**
- **MongoDB** instance (local or cloud e.g. MongoDB Atlas)
- **[uv](https://docs.astral.sh/uv/)** package manager

### 1. Clone the Repository

```bash
git clone <repository-url>
cd office-payment-mgt-backend
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
MONGO_URI=mongodb://localhost:27017        # Your MongoDB connection string
MONGO_DB=office-payment-mgmt              # Database name (default: office-payment-mgmt)
JWT_SECRET=your-secret-key                # JWT signing secret
ACCESS_EXPIRES=60                         # Token expiry in minutes (default: 60)
```

### 3. Install Dependencies

```bash
uv sync
```

This will create a `.venv` virtual environment and install all dependencies from `pyproject.toml`.

### 4. Run the Server

```bash
uv run python app.py
```

The server will start at **`http://localhost:8080`** with debug mode enabled.

---

## Project Structure

```
office-payment-mgt-backend/
├── app.py                  # Flask app setup, blueprint registration
├── main.py                 # Entrypoint placeholder
├── pyproject.toml           # Project metadata & dependencies
├── uv.lock                 # Lockfile for reproducible installs
├── .env                    # Environment variables (not committed)
├── .python-version         # Python version (3.9)
│
├── core/
│   ├── config.py           # Settings loaded from env vars
│   ├── db.py               # MongoDB connection & indexes
│   └── security.py         # Password hashing & verification
│
├── models/
│   ├── schema.py           # Pydantic models (User, Admin, Login, etc.)
│   ├── personnel.py        # Personnel & DB Pydantic models, PersonnelStatus enum
│   └── user.py             # Additional user model
│
├── routes/
│   ├── auth.py             # Login & change password
│   ├── admin.py            # User & DB management (admin only)
│   ├── personnel.py        # Personnel CRUD, bulk ops, filtering
│   └── analytics.py        # Dashboard & per-DB analytics
│
├── seed/                   # Database seeding utilities
└── utils/                  # Shared utilities
```

---

## Response Format

All endpoints return a consistent JSON structure:

```json
{
  "message": "Description of the result",
  "statusCode": 200,
  "data": {}
}
```

Paginated endpoints include a `meta` object:

```json
{
  "data": {
    "data": [],
    "meta": {
      "total": 100,
      "page": 1,
      "limit": 10,
      "pageCount": 10,
      "hasNextPage": true,
      "hasPrevPage": false
    }
  }
}
```
