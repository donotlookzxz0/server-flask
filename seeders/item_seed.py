# seed_items.py
# ✅ CORRECT — NO CHANGES NEEDED (KEPT FOR COMPLETENESS)

import random
import uuid

from app import app
from db import db
from models.item import Item

ITEMS_PER_CATEGORY = 8
MIN_PRICE = 10.00
MAX_PRICE = 500.00
MIN_STOCK = 100
MAX_STOCK = 500

CATEGORIES = {
    "Fruits": ["Apple", "Banana", "Orange", "Mango", "Grapes", "Pineapple"],
    "Vegetables": ["Carrot", "Broccoli", "Spinach", "Potato", "Tomato"],
    "Meat": ["Chicken Breast", "Pork Chop", "Beef Steak", "Ground Beef"],
    "Seafood": ["Salmon", "Tuna", "Shrimp", "Tilapia"],
    "Dairy": ["Milk", "Cheese", "Butter", "Yogurt"],
    "Beverages": ["Cola", "Orange Juice", "Water", "Coffee", "Tea"],
    "Snacks": ["Chips", "Cookies", "Popcorn", "Chocolate Bar"],
    "Bakery": ["Bread", "Croissant", "Muffin", "Donut"],
    "Frozen": ["Frozen Pizza", "Ice Cream", "Frozen Nuggets"],
    "Canned Goods": ["Canned Tuna", "Canned Corn", "Canned Beans"],
    "Condiments": ["Ketchup", "Mayonnaise", "Soy Sauce"],
    "Dry Goods": ["Sugar", "Salt", "Flour"],
    "Grains & Pasta": ["Rice", "Spaghetti", "Macaroni"],
    "Spices & Seasonings": ["Pepper", "Paprika", "Cumin"],
    "Breakfast & Cereal": ["Cornflakes", "Oatmeal", "Granola"],
    "Personal Care": ["Shampoo", "Soap", "Toothpaste"],
    "Household": ["Trash Bags", "Light Bulbs", "Paper Towels"],
    "Baby Products": ["Baby Diapers", "Baby Wipes"],
    "Pet Supplies": ["Dog Food", "Cat Litter"],
    "Health & Wellness": ["Vitamins", "Pain Reliever"],
    "Cleaning Supplies": ["Laundry Detergent", "Dish Soap"]
}

def generate_barcode():
    return str(uuid.uuid4().int)[:13]

def seed_items(clear_existing=False):
    with app.app_context():

        if clear_existing:
            Item.query.delete()
            db.session.commit()

        existing_barcodes = {
            b for (b,) in Item.query.with_entities(Item.barcode).all()
        }

        for category, names in CATEGORIES.items():
            for i in range(ITEMS_PER_CATEGORY):
                barcode = generate_barcode()
                while barcode in existing_barcodes:
                    barcode = generate_barcode()

                existing_barcodes.add(barcode)

                db.session.add(Item(
                    name=f"{random.choice(names)} {i+1}",
                    category=category,
                    price=round(random.uniform(MIN_PRICE, MAX_PRICE), 2),
                    quantity=random.randint(MIN_STOCK, MAX_STOCK),
                    barcode=barcode
                ))

        db.session.commit()
        print("✅ Items seeded")

if __name__ == "__main__":
    seed_items(clear_existing=False)
