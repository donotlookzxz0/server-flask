# app.py
# FINAL SAFE VERSION — COOKIE AUTH + POSTGRES + CORS (ACTUALLY WORKING)

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from db import db
from urls import register_routes

# from ml.recommender.trainer import retrain_model

app = Flask(__name__)

# --------------------------------------------------
# 🔐 SECURITY / COOKIE CONFIG
# --------------------------------------------------
app.config["SECRET_KEY"] = "super-secret"

# JWT stored in cookies
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"   # REQUIRED for cross-origin
app.config["SESSION_COOKIE_SECURE"] = False      # Set True when using HTTPS

# --------------------------------------------------
# 🌍 CORS (ALLOW CREDENTIALS)
# --------------------------------------------------
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
)

# --------------------------------------------------
# 🚫 GLOBAL PREFLIGHT HANDLER
# --------------------------------------------------
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.status_code = 200
        return response

# --------------------------------------------------
# 🗄 DATABASE (POSTGRESQL — RENDER)
# --------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://thesis_nt63_user:XgdoCNcLQ1Du441DQY8Nf64A8Ecpuy1H@"
    "dpg-d5glstf5r7bs73egb930-a.singapore-postgres.render.com/thesis_nt63"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

db.init_app(app)

# --------------------------------------------------
# 🔗 ROUTES
# --------------------------------------------------
register_routes(app)

# --------------------------------------------------
# 🧪 ROOT CHECK
# --------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return {"message": "Flask API running successfully"}

# --------------------------------------------------
# 🚀 START SERVER
# --------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
        threaded=True,
        use_reloader=False
    )
