from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

def hash_password(pwd: str) -> str:
    return bcrypt.generate_password_hash(pwd).decode()

def verify_password(pwd: str, hashed: str) -> bool:
    return bcrypt.check_password_hash(hashed, pwd)