import random
from sqlalchemy.exc import IntegrityError
from db import db
from models.pending_cash_payment import PendingCashPayment

def generate_unique_cash_code(user_id, cart, expires_at):

    while True:
        try:
            code = f"{random.randint(100000, 999999)}"

            pending = PendingCashPayment(
                user_id=user_id,
                code=code,
                cart=cart,
                expires_at=expires_at
            )

            db.session.add(pending)
            db.session.commit()
            return pending

        except IntegrityError:
            db.session.rollback()
           
