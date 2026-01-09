from db import db
from models.pending_cash_payment import PendingCashPayment
from models.item import Item
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem
from utils.cash_code import generate_unique_cash_code
from datetime import datetime, timedelta
# from ml.recommender.updater import on_successful_payment

class CashPaymentService:

    @staticmethod
    def create_pending_payment(user_id, cart):

    # Cancel any existing active code for this user
        PendingCashPayment.query.filter_by(
            user_id=user_id,
            status="PENDING"
        ).update({"status": "CANCELLED"})

        db.session.flush()

        # Validate cart
        for entry in cart:
            item = Item.query.filter_by(barcode=entry["barcode"]).first()
            if not item:
                raise Exception(f"Item not found: {entry['barcode']}")
            if item.quantity < entry["quantity"]:
                raise Exception(f"Insufficient stock for {item.name}")

        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Create UNIQUE code safely
        pending = generate_unique_cash_code(
            user_id=user_id,
            cart=cart,
            expires_at=expires_at
        )

        return pending

    @staticmethod
    def update_cart(code, new_cart):
        pending = PendingCashPayment.query.filter_by(code=code, status="PENDING").first()
        if not pending:
            raise Exception("Invalid or expired code")

        pending.cart = new_cart
        db.session.commit()
        return pending

    @staticmethod
    def cancel_payment(code):
        pending = PendingCashPayment.query.filter_by(code=code, status="PENDING").first()
        if not pending:
            raise Exception("Invalid or expired code")

        pending.status = "CANCELLED"
        db.session.commit()

    @staticmethod
    def confirm_payment(code):
        pending = PendingCashPayment.query.filter_by(code=code, status="PENDING").first()
        if not pending:
            raise Exception("Invalid or expired code")

        try:
            # create transaction
            transaction = SalesTransaction(user_id=pending.user_id)
            db.session.add(transaction)
            db.session.flush()

            for entry in pending.cart:
                item = Item.query.filter_by(barcode=entry["barcode"]).first()
                if item.quantity < entry["quantity"]:
                    raise Exception(f"Stock changed for {item.name}")

                item.quantity -= entry["quantity"]

                db.session.add(SalesTransactionItem(
                    transaction_id=transaction.id,
                    item_id=item.id,
                    quantity=entry["quantity"],
                    price_at_sale=item.price
                ))

            # mark as paid
            pending.status = "PAID"
            db.session.commit()  # commit all DB changes first

            # trigger recommender update, safely
            # try:
            #     on_successful_payment()
            # except Exception as e:
            #     print("WARNING: recommender update failed:", e)

            return transaction.id

        except Exception as e:
            db.session.rollback()  # revert any DB changes if something fails
            raise e

