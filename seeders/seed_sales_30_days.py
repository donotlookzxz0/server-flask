# seed_sales_30_days.py
# ✅ FIXED — assigns user_id (ML-safe, no stock depletion)

import random
from datetime import datetime, timedelta, UTC

from app import app
from db import db
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem
from models.item import Item
from models.user import User

DAYS_BACK = 30
MIN_TRANSACTIONS_PER_DAY = 3
MAX_TRANSACTIONS_PER_DAY = 8

MIN_ITEMS_PER_TRANSACTION = 1
MAX_ITEMS_PER_TRANSACTION = 4

MIN_QTY = 1
MAX_QTY = 5

def seed_sales_30_days(clear_existing=False):
    with app.app_context():

        if clear_existing:
            SalesTransactionItem.query.delete()
            SalesTransaction.query.delete()
            db.session.commit()

        items = Item.query.all()
        users = User.query.all()

        if not items:
            raise Exception("Seed items first")
        if not users:
            raise Exception("Seed users first")

        now = datetime.now(UTC)
        total_transactions = 0

        for day_offset in range(DAYS_BACK):
            day_date = now - timedelta(days=day_offset)

            for _ in range(random.randint(
                MIN_TRANSACTIONS_PER_DAY,
                MAX_TRANSACTIONS_PER_DAY
            )):

                transaction = SalesTransaction(
                    user_id=random.choice(users).id,   # ✅ FIX
                    date=day_date.replace(
                        hour=random.randint(8, 21),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )
                )

                db.session.add(transaction)
                db.session.flush()

                cart_items = random.sample(
                    items,
                    random.randint(
                        MIN_ITEMS_PER_TRANSACTION,
                        MAX_ITEMS_PER_TRANSACTION
                    )
                )

                for item in cart_items:
                    db.session.add(SalesTransactionItem(
                        transaction_id=transaction.id,
                        item_id=item.id,
                        quantity=random.randint(MIN_QTY, MAX_QTY),
                        price_at_sale=item.price
                    ))

                total_transactions += 1

        db.session.commit()
        print(f"✅ Sales seeded for {DAYS_BACK} days")
        print(f"📊 Transactions: {total_transactions}")

if __name__ == "__main__":
    seed_sales_30_days(clear_existing=False)
