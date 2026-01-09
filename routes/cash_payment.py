from flask import Blueprint, request, jsonify, g
from services.cash_payment_service import CashPaymentService
from models.pending_cash_payment import PendingCashPayment
from utils.auth_restrict import require_auth

cash_payment_bp = Blueprint("cash_payment", __name__)

# -----------------------
# STEP 1: CUSTOMER REQUESTS CASH PAYMENT (NO CODE)
# -----------------------
@cash_payment_bp.route("/start", methods=["POST"])
@require_auth(roles=("customer",))
def start_cash_payment():
    data = request.get_json()
    cart = data.get("cart", [])

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    user_id = g.current_user.id

    try:
        pending = CashPaymentService.create_pending_payment(
            user_id=user_id,
            cart=cart
        )
        return jsonify({
            "pending_id": pending.id,
            "message": "Cash payment requested. Waiting for admin approval."
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -----------------------
# STEP 2: CUSTOMER POLLS STATUS (ADMIN GENERATES CODE)
# -----------------------
@cash_payment_bp.route("/status/<int:pending_id>", methods=["GET"])
@require_auth(roles=("customer",))
def cash_status(pending_id):
    pending = PendingCashPayment.query.filter_by(
        id=pending_id,
        user_id=g.current_user.id
    ).first()

    if not pending:
        return jsonify({"error": "Pending cash request not found"}), 404

    return jsonify({
        "status": pending.status,
        "code": pending.code
    }), 200


# -----------------------
# STEP 3: CUSTOMER CONFIRMS PAYMENT
# -----------------------
@cash_payment_bp.route("/confirm", methods=["POST"])
@require_auth(roles=("customer",))
def confirm_cash():
    code = request.json.get("code")
    if not code:
        return jsonify({"error": "Cash code required"}), 400

    try:
        tx_id = CashPaymentService.confirm_payment(code)
        return jsonify({
            "message": "Payment successful",
            "transaction_id": tx_id,
            "redirect_url": "/success"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -----------------------
# STEP 4: CUSTOMER CANCELS REQUEST (OPTIONAL)
# -----------------------
@cash_payment_bp.route("/cancel/<int:pending_id>", methods=["POST"])
@require_auth(roles=("customer",))
def cancel_cash(pending_id):
    pending = PendingCashPayment.query.filter_by(
        id=pending_id,
        user_id=g.current_user.id,
        status="PENDING"
    ).first()

    if not pending:
        return jsonify({"error": "Pending cash request not found"}), 404

    pending.status = "CANCELLED"
    from db import db
    db.session.commit()

    return jsonify({"message": "Cash payment cancelled"}), 200
