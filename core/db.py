from core.config import settings
from pymongo import MongoClient


client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

db.users.create_index("army_number", unique=True)
db.users.create_index("first_name")
db.users.create_index("last_name")
db.dbs.create_index("name")
db.dbs.create_index("short_code")
db.personnels.create_index("army_number", unique=True)
db.personnels.create_index("first_name")
db.personnels.create_index("last_name")
db.personnels.create_index("middle_name")