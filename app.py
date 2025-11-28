from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from core.config import settings
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.personnel import personnel_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = settings.ACCESS_TOKEN_EXPIRES

CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(personnel_bp, url_prefix="/personnels")

@app.route("/")
def home():
    return "Hello World! The API is working 🎉"

if __name__ == "__main__":
    print("MongoDB connected!")
    app.run(host="0.0.0.0", port=8080, debug=True)