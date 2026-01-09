# app.py
# FINAL SAFE VERSION — COOKIE AUTH + POSTGRES + CORS (PRODUCTION READY)

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from db import db
from urls import register_routes

app = Flask(__name__)

# --------------------------------------------------
# 🔐 SECURITY / COOKIE CONFIG (REQUIRED FOR VERCEL)
# --------------------------------------------------
app.config["SECRET_KEY"] = "super-secret"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"   # REQUIRED for cross-origin cookies
app.config["SESSION_COOKIE_SECURE"] = True       # ✅ MUST be TRUE (HTTPS)

# --------------------------------------------------
# 🌍 CORS (ALLOW CREDENTIALS + CRUD)
# --------------------------------------------------
CORS(
    app,
    supports_credentials=True,
    origins=[
        # 🧪 Local development
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",

        # 🚀 Vercel frontends
        "https://pi-mart-client-goaz.vercel.app",
        "https://test-deploy-t7yv.vercel.app",
    ],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# --------------------------------------------------
# 🚫 GLOBAL PREFLIGHT HANDLER (OPTIONS)
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
