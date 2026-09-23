from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

from config import settings
from db import init_db
from routes import bp as api_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key
app.register_blueprint(api_bp)
init_db()

@app.get("/")
def index():
    return jsonify({
        "app": "LayoAI",
        "status": "development-scaffold",
        "api": "/api/health"
    })

@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "not_found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=settings.app_env == "development")
