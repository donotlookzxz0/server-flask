# seeds/seed_sales_transactions.py
# FINAL FIXED VERSION — user_id + price_at_sale handled correctly

import random
from datetime import date, timedelta

from app import app
from db import db
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem
from models.item import Item
from models.user import User


# ===============================
# CONFIG
# ===============================
DAYS = 120
MIN_TX_PER_DAY = 8
MAX_TX_PER_DAY = 25

CATEGORY_DEMAND = {
    "Frozen": 1.8,
    "Meat": 1.6,
    "Personal Care": 1.5,
    "Vegetables": 1.4,
    "Fruits": 1.4,
    "Snacks": 1.3,
    "Beverages": 1.3,
    "Pet Supplies": 1.2,
    "Dairy": 1.2,
    "Dry Goods": 1.1,
    "Spices & Seasonings": 1.1,
    "Grains & Pasta": 1.0,
    "Health & Wellness": 1.0,
    "Condiments": 1.0,
    "Bakery": 0.9,
    "Canned Goods": 0.9,
    "Breakfast & Cereal": 0.8,
    "Seafood": 0.7,
    "Baby Products": 0.6,
    "Household": 0.4,
    "Cleaning Supplies": 0.3,
}


def seed_sales(clear_existing=False):
    with app.app_context():

        if clear_existing:
            SalesTransactionItem.query.delete()
            SalesTransaction.query.delete()
            db.session.commit()

        items = Item.query.all()
        if not items:
            raise RuntimeError("❌ No items found. Run seed_items.py first.")

        users = User.query.all()
        if not users:
            raise RuntimeError("❌ No users found. Seed users first.")

        items_by_category = {}
        for item in items:
            items_by_category.setdefault(item.category, []).append(item)

        today = date.today()

        for day_offset in range(DAYS):
            current_date = today - timedelta(days=day_offset)

            tx_count = random.randint(MIN_TX_PER_DAY, MAX_TX_PER_DAY)

            for _ in range(tx_count):
                user = random.choice(users)   # ✅ valid user

                tx = SalesTransaction(
                    user_id=user.id,
                    date=current_date
                )
                db.session.add(tx)
                db.session.flush()

                for _ in range(random.randint(1, 5)):
                    category = random.choices(
                        list(CATEGORY_DEMAND.keys()),
                        weights=CATEGORY_DEMAND.values(),
                        k=1
                    )[0]

                    category_items = items_by_category.get(category)
                    if not category_items:
                        continue

                    item = random.choice(category_items)

                    base = CATEGORY_DEMAND.get(category, 1.0)
                    quantity = max(1, int(random.gauss(mu=3 * base, sigma=1)))

                    db.session.add(SalesTransactionItem(
                        transaction_id=tx.id,
                        item_id=item.id,
                        quantity=quantity,
                        price_at_sale=item.price  # 🔑 REQUIRED FIX
                    ))

        db.session.commit()
        print("✅ Sales transactions seeded successfully")


if __name__ == "__main__":
    seed_sales(clear_existing=False)
