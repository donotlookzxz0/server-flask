# routes/ml.py
# DEMAND FORECAST + ITEM MOVEMENT FORECAST + STOCKOUT RISK (SAFE)

from flask import Blueprint, jsonify, request
from sqlalchemy import case

from db import db

from ml.time_series_forecast import run_time_series_forecast
from ml.item_movement_forecast import run_item_movement_forecast
from ml.stockout_risk_forecast import run_stockout_risk_forecast

from models.ai_forecast import AIForecast
from models.ai_item_movement import AIItemMovement
from models.ai_stockout_risk import AIStockoutRisk

# from utils.auth_restrict import require_auth


ml_bp = Blueprint("ml_bp", __name__)

# =================================================
# DEMAND FORECAST
# =================================================

@ml_bp.route("/forecast", methods=["POST"])
# @require_auth()
def create_forecast():
    try:
        result = run_time_series_forecast()
        if result is None:
            return jsonify({"success": False, "message": "Not enough data"}), 400

        AIForecast.query.delete()

        for cat, qty in result["tomorrow"].items():
            db.session.add(AIForecast(
                horizon="tomorrow",
                category=cat,
                predicted_quantity=int(round(qty))
            ))

        for cat, qty in result["next_7_days"].items():
            db.session.add(AIForecast(
                horizon="7_days",
                category=cat,
                predicted_quantity=qty
            ))

        for cat, qty in result["next_30_days"].items():
            db.session.add(AIForecast(
                horizon="30_days",
                category=cat,
                predicted_quantity=qty
            ))

        db.session.commit()
        return jsonify({"success": True}), 201

    except Exception as e:
        db.session.rollback()
        print("🔥 DEMAND FORECAST ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500


@ml_bp.route("/forecast", methods=["GET"])
# @require_auth()
def get_forecasts_grouped():
    forecasts = AIForecast.query.order_by(AIForecast.category).all()

    grouped = {
        "tomorrow": [],
        "next_7_days": [],
        "next_30_days": []
    }

    for f in forecasts:
        data = {
            "id": f.id,
            "category": f.category,
            "predicted_quantity": f.predicted_quantity,
            "created_at": f.created_at.isoformat()
        }

        if f.horizon == "tomorrow":
            grouped["tomorrow"].append(data)
        elif f.horizon == "7_days":
            grouped["next_7_days"].append(data)
        elif f.horizon == "30_days":
            grouped["next_30_days"].append(data)

    return jsonify(grouped), 200


@ml_bp.route("/forecast/<int:id>", methods=["PUT"])
# @require_auth()
def update_forecast(id):
    forecast = AIForecast.query.get(id)
    if not forecast:
        return jsonify({"error": "Forecast not found"}), 404

    data = request.get_json() or {}
    if "predicted_quantity" in data:
        forecast.predicted_quantity = int(data["predicted_quantity"])

    db.session.commit()
    return jsonify({"success": True}), 200


@ml_bp.route("/forecast/<int:id>", methods=["DELETE"])
# @require_auth()
def delete_forecast(id):
    forecast = AIForecast.query.get(id)
    if not forecast:
        return jsonify({"error": "Forecast not found"}), 404

    db.session.delete(forecast)
    db.session.commit()
    return jsonify({"success": True}), 200


# =================================================
# ITEM MOVEMENT FORECAST (NEURAL NETWORK SAFE)
# =================================================

@ml_bp.route("/item-movement-forecast", methods=["POST"])
# @require_auth()
def create_item_movement_forecast():
    try:
        ok = run_item_movement_forecast()
        if not ok:
            return jsonify({"success": False, "message": "Not enough data"}), 400
        return jsonify({"success": True}), 201

    except Exception as e:
        db.session.rollback()
        print("🔥 ITEM MOVEMENT ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500


@ml_bp.route("/item-movement-forecast", methods=["GET"])
# @require_auth()
def get_item_movement_forecast():
    records = AIItemMovement.query.order_by(AIItemMovement.category).all()
    return jsonify([
        {
            "item_id": r.item_id,
            "item_name": r.item_name,
            "category": r.category,
            "avg_daily_sales": r.avg_daily_sales,
            "days_since_last_sale": r.days_since_last_sale,
            "movement_class": r.movement_class,
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]), 200


# =================================================
# STOCK-OUT RISK FORECAST (NEURAL NETWORK SAFE)
# =================================================

@ml_bp.route("/stockout-risk", methods=["POST"])
# @require_auth()
def create_stockout_risk():
    try:
        ok = run_stockout_risk_forecast()
        if not ok:
            return jsonify({"success": False, "message": "Not enough data"}), 400
        return jsonify({"success": True}), 201

    except Exception as e:
        db.session.rollback()
        print("🔥 STOCKOUT RISK ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500


@ml_bp.route("/stockout-risk", methods=["GET"])
# @require_auth()
def get_stockout_risk():
    priority_order = case(
        (AIStockoutRisk.risk_level == "High", 1),
        (AIStockoutRisk.risk_level == "Medium", 2),
        (AIStockoutRisk.risk_level == "Low", 3),
        else_=4
    )

    records = (
        AIStockoutRisk.query
        .order_by(priority_order, AIStockoutRisk.category)
        .all()
    )

    return jsonify([
        {
            "item_id": r.item_id,
            "item_name": r.item_name,
            "category": r.category,
            "current_stock": r.current_stock,
            "avg_daily_sales": r.avg_daily_sales,
            "days_of_stock_left": r.days_of_stock_left,
            "risk_level": r.risk_level,
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]), 200
