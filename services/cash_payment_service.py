# services/cash_payment_service.py
from db import db
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem
from models.item import Item
from models.pending_cash_payment import PendingCashPayment
from datetime import datetime, timedelta
import random
from sqlalchemy.exc import IntegrityError

class CashPaymentService:

    @staticmethod
    def create_pending_payment(user_id, cart):
        """
        Creates a pending payment for the user.
        If there's already a PENDING payment for the user, return it.
        Expired codes are automatically cancelled.
        """
        existing = PendingCashPayment.query.filter_by(user_id=user_id, status="PENDING").first()

        if existing:
            # Cancel expired code if present
            if existing.expires_at and existing.expires_at < datetime.utcnow():
                existing.status = "CANCELLED"
                db.session.commit()
            else:
                return existing

        # Create a new pending payment with a unique code
        pending = CashPaymentService._create_pending_payment_with_unique_code(user_id, cart, expires_minutes=10)
        return pending

    @staticmethod
    def generate_code(pending_id):
        """
        Generate a new 6-digit code for an existing pending payment.
        Cancels expired code automatically if needed.
        """
        pending = PendingCashPayment.query.filter_by(id=pending_id, status="PENDING").first()
        if not pending:
            raise Exception("Pending payment not found")

        # If existing code is expired, keep status as PENDING but update code
        CashPaymentService._update_pending_with_new_code(pending, expires_seconds=30)
        return pending

    @staticmethod
    def confirm_payment(code):
        pending = PendingCashPayment.query.filter_by(code=code, status="PENDING").first()
        if not pending:
            existing = PendingCashPayment.query.filter_by(code=code).first()
            if existing:
                if existing.status == "PAID":
                    raise Exception("This cash code has already been used.")
                elif existing.status == "CANCELLED":
                    raise Exception("This cash code was cancelled. Please request a new one.")
            raise Exception("Invalid or expired cash code")

        if pending.expires_at < datetime.utcnow():
            pending.status = "CANCELLED"
            db.session.commit()
            raise Exception("Cash code expired, please generate a new one")

        # Mark as PAID
        pending.status = "PAID"
        db.session.commit()

        # -----------------------------
        # Create Sales Transaction
        # -----------------------------
        cart_items = pending.cart or []  # [{'barcode': ..., 'quantity': ...}, ...]

        if not cart_items:
            raise Exception("Pending payment cart is empty")

        transaction = SalesTransaction(user_id=pending.user_id)
        db.session.add(transaction)
        db.session.flush()  # ensure transaction.id is available

        for entry in cart_items:
            barcode = entry.get("barcode")
            qty = entry.get("quantity")

            if not barcode or not qty:
                continue  # skip invalid entries

            item = Item.query.filter_by(barcode=barcode).first()
            if not item:
                raise Exception(f"Item not found: {barcode}")

            if item.quantity < qty:
                raise Exception(f"Not enough stock for {item.name}")

            # Deduct stock
            item.quantity -= qty

            # Create SalesTransactionItem
            transaction_item = SalesTransactionItem(
                transaction_id=transaction.id,
                item_id=item.id,
                quantity=qty,
                price_at_sale=item.price
            )
            db.session.add(transaction_item)

        db.session.commit()
        return transaction.id

    @staticmethod
    def cancel_payment(code):
        pending = PendingCashPayment.query.filter_by(code=code, status="PENDING").first()
        if pending:
            pending.status = "CANCELLED"
            db.session.commit()

    # ------------------------
    # Private helper methods
    # ------------------------
    @staticmethod
    def _create_pending_payment_with_unique_code(user_id, cart, expires_minutes=10):
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
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
                db.session.rollback()  # retry if code already exists

    @staticmethod
    def _update_pending_with_new_code(pending, expires_seconds=30):
        pending.expires_at = datetime.utcnow() + timedelta(seconds=expires_seconds)
        while True:
            try:
                # Assign a new unique 6-digit code
                pending.code = f"{random.randint(100000, 999999)}"
                db.session.commit()
                return pending
            except IntegrityError:
                db.session.rollback()  # retry if generated code already exists
