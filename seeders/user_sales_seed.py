import random
from datetime import datetime, timedelta

from app import app
from db import db
from models.user import User
from models.item import Item
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem

DAYS_BACK = 30
MIN_TRANSACTIONS = 10
MAX_TRANSACTIONS = 30

def seed_user_sales(clear_existing=False):
    with app.app_context():

        if clear_existing:
            SalesTransactionItem.query.delete()
            SalesTransaction.query.delete()
            db.session.commit()

        users = User.query.all()
        items = Item.query.all()

        if not users or not items:
            raise Exception("Seed users and items first")

        for user in users:
            for _ in range(random.randint(MIN_TRANSACTIONS, MAX_TRANSACTIONS)):

                transaction = SalesTransaction(
                    user_id=user.id,
                    date=datetime.utcnow() - timedelta(days=random.randint(0, DAYS_BACK))
                )

                db.session.add(transaction)
                db.session.flush()

                cart_items = random.sample(items, random.randint(1, 4))

                for item in cart_items:
                    db.session.add(SalesTransactionItem(
                        transaction_id=transaction.id,
                        item_id=item.id,
                        quantity=random.randint(1, 5),
                        price_at_sale=item.price
                    ))

        db.session.commit()
        print("User sales seeded")

if __name__ == "__main__":
    seed_user_sales(clear_existing=False)
