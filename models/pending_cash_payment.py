from db import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class PendingCashPayment(db.Model):
    __tablename__ = "pending_cash_payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    # Admin-generated only
    code = db.Column(db.String(6), unique=True, nullable=True)

    cart = db.Column(JSON, nullable=False)

    status = db.Column(
        db.Enum("PENDING", "CANCELLED", "PAID", name="cash_status"),
        default="PENDING",
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
