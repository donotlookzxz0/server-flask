from flask import Blueprint, jsonify
from ml.recommender.inference import recommend_for_user
# from utils.auth_restrict import require_auth
from models.user import User
from ml.recommender.trainer import retrain_model
from flask import current_app

recommendations_bp = Blueprint("recommendations_bp", __name__)

_training_in_progress = False

# GET recommendations for a SINGLE user
@recommendations_bp.route("/recommendations/<int:user_id>", methods=["GET"])
# @require_auth()
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
# @require_auth()
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

@recommendations_bp.route("/recommendations/train", methods=["POST"])
def train_recommender():
    global _training_in_progress

    if _training_in_progress:
        return jsonify({
            "success": False,
            "message": "Training already in progress"
        }), 409  # Conflict

    try:
        _training_in_progress = True

        # BLOCKING — this is intentional
        retrain_model()

        return jsonify({
            "success": True,
            "message": "Training completed successfully"
        }), 200

    except Exception as e:
        current_app.logger.exception("Training failed")
        return jsonify({
            "success": False,
            "message": "Training failed",
            "error": str(e)
        }), 500

    finally:
        _training_in_progress = False