from db import db
from models.pending_cash_payment import PendingCashPayment
import random

class AdminCashPaymentService:

    @staticmethod
    def generate_code(pending_id):
        pending = PendingCashPayment.query.filter_by(
            id=pending_id,
            status="PENDING"
        ).first()

        if not pending:
            raise Exception("Pending cash request not found")

        if pending.code:
            raise Exception("Cash code already generated for this request")

        # Generate unique 6-digit code
        while True:
            code = f"{random.randint(100000, 999999)}"
            exists = PendingCashPayment.query.filter_by(code=code).first()
            if not exists:
                break

        pending.code = code
        db.session.commit()

        return pending
