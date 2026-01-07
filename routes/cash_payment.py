from flask import Blueprint, request, jsonify, g
# from utils.auth_restrict import require_auth
from services.cash_payment_service import CashPaymentService

cash_payment_bp = Blueprint("cash_payment", __name__)

@cash_payment_bp.route("/start", methods=["POST"])
def start_cash_payment():
    data = request.get_json()
    cart = data.get("cart", [])
    print("DEBUG /start cart:", cart)  # <-- see what frontend sends

    user_id = g.current_user.id

    try:
        pending = CashPaymentService.create_pending_payment(
            user_id=user_id,
            cart=cart
        )
        return jsonify({
            "code": pending.code,
            "expires_at": pending.expires_at.isoformat()
        }), 201
    except Exception as e:
        print("DEBUG /start error:", e)  # <-- see exact exception
        return jsonify({"error": str(e)}), 400




@cash_payment_bp.route("/update-cart", methods=["PUT"])
# @require_auth(roles=None)
def update_cart():
    data = request.get_json()
    try:
        CashPaymentService.update_cart(data["code"], data["cart"])
        return jsonify({"message": "Cart updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@cash_payment_bp.route("/cancel", methods=["POST"])
# @require_auth(roles=None)
def cancel_cash():
    try:
        CashPaymentService.cancel_payment(request.json["code"])
        return jsonify({"message": "Cash payment cancelled"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@cash_payment_bp.route("/confirm", methods=["POST"])
# @require_auth(roles=None)
def confirm_cash():
    try:
        tx_id = CashPaymentService.confirm_payment(request.json["code"])
        return jsonify({
            "message": "Payment successful",
            "transaction_id": tx_id
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
