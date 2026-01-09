from db import db
from datetime import datetime
import pytz

# 🇵🇭 Philippines Timezone
PH_TZ = pytz.timezone("Asia/Manila")

def ph_now():
    # return PH time as naive datetime (no postgres changes needed)
    return datetime.now(PH_TZ).replace(tzinfo=None)

class SalesTransaction(db.Model):
    __tablename__ = "sales_transactions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # ✅ PHILIPPINES TIME (FLASK-ONLY)
    date = db.Column(
        db.DateTime,
        nullable=False,
        default=ph_now
    )

    # One transaction → many items
    items = db.relationship(
        "SalesTransactionItem",
        back_populates="transaction",
        lazy=True,
        cascade="all, delete-orphan"
    )

    user = db.relationship(
        "User",
        backref="sales_transactions"
    )

    def __repr__(self):
        return f"<SalesTransaction {self.id}>"
