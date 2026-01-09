# utils/auth_restrict.py
from functools import wraps
from flask import request, jsonify, g
import jwt
from models.user import User

JWT_SECRET = "super-secret"

def require_auth(roles=()):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):

            # ✅ allow CORS preflight
            if request.method == "OPTIONS":
                return "", 200

            token = request.cookies.get("access_token")
            if not token:
                return jsonify({"error": "Authentication required"}), 401

            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

                if payload.get("type") != "access":
                    return jsonify({"error": "Invalid token type"}), 401

                user = User.query.get(payload["user_id"])
                if not user:
                    return jsonify({"error": "User not found"}), 401

                if roles and user.role not in roles:
                    return jsonify({"error": "Forbidden"}), 403

                g.current_user = user

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            return fn(*args, **kwargs)

        return wrapper
    return decorator
