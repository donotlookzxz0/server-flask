from flask import Blueprint, jsonify
from ml.recommender.inference import recommend_for_user
from utils.auth_restrict import require_auth
from models.user import User

recommendations_bp = Blueprint("recommendations_bp", __name__)

# GET recommendations for a SINGLE user
@recommendations_bp.route("/recommendations/<int:user_id>", methods=["GET"])
@require_auth()
def get_recommendations(user_id):
    items = recommend_for_user(user_id)

    return jsonify({
        "user_id": user_id,
        "recommendations": [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "price": float(i.price)
            }
            for i in items
        ]
    }), 200

# GET recommendations for ALL users
@recommendations_bp.route("/recommendations", methods=["GET"])
@require_auth()
def get_all_recommendations():
    users = User.query.all()
    if not users:
        return jsonify({"message": "No users found"}), 200

    all_recommendations = []

    for user in users:
        items = recommend_for_user(user.id)

        all_recommendations.append({
            "user_id": user.id,
            "recommendations": [
                {
                    "id": i.id,
                    "name": i.name,
                    "category": i.category,
                    "price": float(i.price)
                }
                for i in items
            ]
        })

    return jsonify(all_recommendations), 200
