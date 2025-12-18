import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("MONGO_URI is not set in the environment!")
    
    MONGO_DB = os.getenv("MONGO_DB", "office-payment-mgmt")
    JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
    ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("ACCESS_EXPIRES", 60)))


settings = Settings()