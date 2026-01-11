# seed_sales_with_customers.py
# ✅ SAFE SEEDER — WORKS WITH ALL AI MODELS

import random
from datetime import datetime, timedelta

from app import app
from db import db

from models.user import User
from models.item import Item
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem

# -----------------------------
# CONFIG
# -----------------------------
DAYS = 30
CUSTOMERS = 10
MIN_TX_PER_DAY = 5
MAX_TX_PER_DAY = 10
MIN_ITEMS_PER_TX = 1
MAX_ITEMS_PER_TX = 5
MIN_QTY = 1
MAX_QTY = 5


# -----------------------------
# USERS
# -----------------------------
def seed_customers():
    users = []
    for i in range(CUSTOMERS):
        username = f"customer{i+1}"

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                password="seeded",  # already hashed elsewhere in prod
                role="customer"
            )
            db.session.add(user)
            db.session.flush()

        users.append(user)

    return users


# -----------------------------
# SALES TRANSACTIONS
# -----------------------------
def seed_sales(users):
    items = Item.query.all()
    if len(items) < 5:
        raise Exception("❌ At least 5 items required for AI models")

    today = datetime.utcnow().date()

    for day_offset in range(DAYS):
        tx_date = today - timedelta(days=day_offset)
        transactions_today = random.randint(
            MIN_TX_PER_DAY,
            MAX_TX_PER_DAY
        )

        for _ in range(transactions_today):
            user = random.choice(users)

            tx = SalesTransaction(
                user_id=user.id,
                date=tx_date
            )
            db.session.add(tx)
            db.session.flush()

            picked_items = random.sample(
                items,
                random.randint(
                    MIN_ITEMS_PER_TX,
                    min(MAX_ITEMS_PER_TX, len(items))
                )
            )

            for item in picked_items:
                if item.quantity <= 0:
                    continue

                qty = random.randint(
                    MIN_QTY,
                    min(MAX_QTY, item.quantity)
                )

                item.quantity -= qty

                db.session.add(SalesTransactionItem(
                    transaction_id=tx.id,
                    item_id=item.id,
                    quantity=qty,
                    price_at_sale=item.price
                ))

    db.session.commit()


# -----------------------------
# RUN
# -----------------------------
def run(clear_existing=False):
    with app.app_context():

        if clear_existing:
            SalesTransactionItem.query.delete()
            SalesTransaction.query.delete()
            db.session.commit()

        users = seed_customers()
        seed_sales(users)

        print("✅ Customers + 30-day sales history seeded")
        print("🤖 AI models are SAFE to run")


if __name__ == "__main__":
    run(clear_existing=False)