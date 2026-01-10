# app.py
# FINAL SAFE VERSION — COOKIE AUTH + POSTGRES + CORS (PRODUCTION READY)

import os
from flask import Flask, request
from flask_cors import CORS

from db import db
from urls import register_routes

app = Flask(__name__)

# --------------------------------------------------
# 🔐 SECURITY / COOKIE CONFIG
# --------------------------------------------------
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"   # REQUIRED for cross-origin cookies
app.config["SESSION_COOKIE_SECURE"] = True       # MUST be TRUE for HTTPS

# --------------------------------------------------
# 🌍 CORS (🔥 FIXED FOR COOKIES)
# --------------------------------------------------
CORS(
    app,
    supports_credentials=True,
    origins=[
        "https://test-customer-react.vercel.app",   # 📱 Mobile
        "https://admin-vue-iota.vercel.app",      # 🖥 PC
    ],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Set-Cookie"],  # 🔥 CRITICAL
)

# --------------------------------------------------
# 🔥 GLOBAL PREFLIGHT HANDLER
# --------------------------------------------------
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        return "", 200

# --------------------------------------------------
# 🗄 DATABASE (POSTGRESQL — RENDER)
# --------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

db.init_app(app)

@app.route("/__db_check")
def db_check():
    return {"DATABASE_URL": os.environ.get("DATABASE_URL")}

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
        use_reloader=False,
    )
