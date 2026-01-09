# routes/users.py
# FULL FILE — COOKIE AUTH + ACCESS + REFRESH TOKENS (PRODUCTION READY)

from flask import Blueprint, request, jsonify, make_response, g
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from datetime import datetime, timedelta
from models.user import User
import jwt

# ✅ IMPORT THE SHARED AUTH DECORATOR
from utils.auth_restrict import require_auth

user_routes = Blueprint("user_routes", __name__)

# --------------------------------------------------
# 🔐 JWT CONFIG
# --------------------------------------------------
JWT_SECRET = "super-secret"
ACCESS_EXPIRES = timedelta(minutes=15)
REFRESH_EXPIRES = timedelta(days=7)

# ✅ REQUIRED FOR VERCEL / SAFARI / IOS
COOKIE_KWARGS = dict(
    httponly=True,
    samesite="None",   # 🔥 CRITICAL
    secure=True,       # 🔥 CRITICAL
    path="/"           # 🔥 IMPORTANT
)

# --------------------------------------------------
# TOKEN CREATOR
# --------------------------------------------------
def create_token(user_id, token_type="access"):
    payload = {
        "user_id": user_id,
        "type": token_type,
        "exp": datetime.utcnow()
        + (ACCESS_EXPIRES if token_type == "access" else REFRESH_EXPIRES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# --------------------------------------------------
# CURRENT USER
# --------------------------------------------------
@user_routes.route("/me", methods=["GET"])
@require_auth(roles=("admin",))
def me_admin():
    user = g.current_user
    return jsonify({
        "authenticated": True,
        "id": user.id,
        "username": user.username,
        "role": user.role
    }), 200


@user_routes.route("/me/customer", methods=["GET"])
@require_auth(roles=("customer",))
def me_customer():
    user = g.current_user
    return jsonify({
        "authenticated": True,
        "id": user.id,
        "username": user.username,
        "role": user.role
    }), 200

# --------------------------------------------------
# USERS CRUD
# --------------------------------------------------
@user_routes.route("", methods=["GET"])
@user_routes.route("/", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "created_at": u.created_at,
            "updated_at": u.updated_at,
        }
        for u in users
    ]), 200


@user_routes.route("/<int:id>", methods=["GET"])
def get_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }), 200


@user_routes.route("", methods=["POST"])
@user_routes.route("/", methods=["POST"])
def create_user():
    data = request.json or {}

    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "username and password required"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "username exists"}), 400

    user = User(
        username=data["username"],
        password=generate_password_hash(data["password"]),
        role=data.get("role", "customer"),
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "user created", "id": user.id}), 201

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
@user_routes.route("/login", methods=["POST"])
def login():
    data = request.json or {}

    user = User.query.filter_by(username=data.get("username")).first()
    if not user or not check_password_hash(user.password, data.get("password")):
        return jsonify({"error": "invalid credentials"}), 401

    access_token = create_token(user.id, "access")
    refresh_token = create_token(user.id, "refresh")

    user.refresh_token = refresh_token
    db.session.commit()

    resp = make_response(jsonify({
        "message": "login success",
        "role": user.role
    }))

    resp.set_cookie("access_token", access_token, **COOKIE_KWARGS)
    resp.set_cookie("refresh_token", refresh_token, **COOKIE_KWARGS)

    return resp, 200

# --------------------------------------------------
# REGISTER
# --------------------------------------------------
@user_routes.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 409

    user = User(
        username=data["username"],
        password=generate_password_hash(data["password"]),
        role="customer"
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Account created"}), 201

# --------------------------------------------------
# REFRESH TOKEN
# --------------------------------------------------
@user_routes.route("/refresh", methods=["POST"])
def refresh():
    token = request.cookies.get("refresh_token")
    if not token:
        return jsonify({"error": "no refresh token"}), 401

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        if payload["type"] != "refresh":
            return jsonify({"error": "invalid token type"}), 401

        user = User.query.get(payload["user_id"])
        if not user or user.refresh_token != token:
            return jsonify({"error": "invalid refresh"}), 401

        new_access = create_token(user.id, "access")

        resp = make_response(jsonify({"message": "token refreshed"}))
        resp.set_cookie("access_token", new_access, **COOKIE_KWARGS)
        return resp, 200

    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid refresh token"}), 401

# --------------------------------------------------
# LOGOUT
# --------------------------------------------------
@user_routes.route("/logout", methods=["POST"])
def logout():
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=["HS256"])
            user = User.query.get(payload.get("user_id"))
            if user and user.refresh_token == refresh_token:
                user.refresh_token = None
                db.session.commit()
        except jwt.InvalidTokenError:
            pass

    resp = make_response(jsonify({"message": "logged out"}))
    resp.delete_cookie("access_token", **COOKIE_KWARGS)
    resp.delete_cookie("refresh_token", **COOKIE_KWARGS)
    return resp, 200
