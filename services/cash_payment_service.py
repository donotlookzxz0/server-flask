from db import db
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem
from models.item import Item
from models.pending_cash_payment import PendingCashPayment

class CashPaymentService:

    @staticmethod
    def create_pending_payment(user_id, cart):
        """
        Create a pending cash payment request.
        If user already has a PENDING request, return it.
        NO code is generated here.
        """
        existing = PendingCashPayment.query.filter_by(
            user_id=user_id,
            status="PENDING"
        ).first()

        if existing:
            return existing

        pending = PendingCashPayment(
            user_id=user_id,
            cart=cart
        )

        db.session.add(pending)
        db.session.commit()
        return pending

    @staticmethod
    def confirm_payment(code):
        """
        Confirm cash payment using ADMIN-GENERATED code.
        """
        pending = PendingCashPayment.query.filter_by(
            code=code,
            status="PENDING"
        ).first()

        if not pending:
            existing = PendingCashPayment.query.filter_by(code=code).first()
            if existing:
                if existing.status == "PAID":
                    raise Exception("This cash code has already been used.")
                if existing.status == "CANCELLED":
                    raise Exception("This cash payment was cancelled.")
            raise Exception("Invalid cash code.")

        # Mark payment as PAID
        pending.status = "PAID"
        db.session.commit()

        # -----------------------------
        # Create Sales Transaction
        # -----------------------------
        cart_items = pending.cart or []
        if not cart_items:
            raise Exception("Pending payment cart is empty")

        transaction = SalesTransaction(user_id=pending.user_id)
        db.session.add(transaction)
        db.session.flush()  # get transaction.id

        for entry in cart_items:
            barcode = entry.get("barcode")
            qty = entry.get("quantity")

            if not barcode or not qty:
                continue

            item = Item.query.filter_by(barcode=barcode).first()
            if not item:
                raise Exception(f"Item not found: {barcode}")

            if item.quantity < qty:
                raise Exception(f"Not enough stock for {item.name}")

            # Deduct stock
            item.quantity -= qty

            transaction_item = SalesTransactionItem(
                transaction_id=transaction.id,
                item_id=item.id,
                quantity=qty,
                price_at_sale=item.price
            )
            db.session.add(transaction_item)

        db.session.commit()
        return transaction.id
    