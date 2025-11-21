from core.config import settings
from pymongo import MongoClient


client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

db.users.create_index("army_number", unique=True)