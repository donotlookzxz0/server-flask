from db import db
from models.pending_cash_payment import PendingCashPayment
from utils.cash_code import generate_unique_cash_code
from datetime import datetime, timedelta

class AdminCashPaymentService:

    @staticmethod
    def generate_code(pending_id):
        pending = PendingCashPayment.query.filter_by(
            id=pending_id,
            status="PENDING"
        ).first()

        if not pending:
            raise Exception("Pending cash request not found")

        # Generate unique 6-digit code
        updated_pending = generate_unique_cash_code(
            user_id=pending.user_id,
            cart=pending.cart,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )

        # Save generated code
        pending.code = updated_pending.code
        pending.expires_at = updated_pending.expires_at
        db.session.commit()

        return pending
