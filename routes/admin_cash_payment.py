from flask import Blueprint, jsonify, request
from services.admin_cash_payment_service import AdminCashPaymentService
from utils.auth_restrict import require_auth
from models.pending_cash_payment import PendingCashPayment
from db import db

admin_cash_bp = Blueprint("admin_cash", __name__)

@admin_cash_bp.route("/pending", methods=["GET"])
@require_auth(roles=("admin",))
def get_pending():
    pendings = PendingCashPayment.query.filter_by(status="PENDING").order_by(
        PendingCashPayment.created_at.desc()
    ).all()

    return jsonify([{
        "id": p.id,
        "user_id": p.user_id,
        "cart": p.cart,
        "code": p.code,
        "created_at": p.created_at.isoformat()
    } for p in pendings]), 200


@admin_cash_bp.route("/generate-code/<int:pending_id>", methods=["POST"])
@require_auth(roles=("admin",))
def generate_code(pending_id):
    try:
        pending = AdminCashPaymentService.generate_code(pending_id)
        return jsonify({
            "code": pending.code,
            "expires_at": pending.expires_at.isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@admin_cash_bp.route("/cancel/<int:pending_id>", methods=["POST"])
@require_auth(roles=("admin",))
def cancel_request(pending_id):
    pending = PendingCashPayment.query.filter_by(id=pending_id, status="PENDING").first()
    if not pending:
        return jsonify({"error": "Not found"}), 404

    pending.status = "CANCELLED"
    db.session.commit()
    return jsonify({"message": "Pending cash request cancelled"}), 200
