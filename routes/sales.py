from flask import Blueprint, jsonify, request, g
from db import db

from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem
from models.item import Item

from utils.auth_restrict import require_auth

sales_bp = Blueprint("sales", __name__)

# --------------------------------------------------
# 🔵 GET all transactions (ADMIN ONLY)
# --------------------------------------------------
@sales_bp.route("/", methods=["GET"])
@require_auth(roles=("admin",))
def get_all_transactions():
    transactions = (
        SalesTransaction.query
        .order_by(SalesTransaction.date.desc())  # ✅ FIX: newest first
        .all()
    )

    result = []

    for t in transactions:
        result.append({
            "transaction_id": t.id,
            "date": t.date.isoformat(),
            "user_id": t.user.id,
            "items": [
                {
                    "item_id": ti.item_id,
                    "item_name": ti.item.name,
                    "category": ti.item.category,
                    "quantity": ti.quantity,
                    "price_at_sale": float(ti.price_at_sale)
                }
                for ti in t.items
            ]
        })

    return jsonify(result), 200


# --------------------------------------------------
# 🔵 GET a single transaction by ID (ADMIN ONLY)
# --------------------------------------------------
@sales_bp.route("/<int:id>", methods=["GET"])
@require_auth(roles=("admin",))
def get_transaction(id):
    t = SalesTransaction.query.get(id)
    if not t:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({
        "transaction_id": t.id,
        "date": t.date.isoformat(),
        "user_id": t.user.id,
        "items": [
            {
                "item_id": ti.item_id,
                "item_name": ti.item.name,
                "category": ti.item.category,
                "quantity": ti.quantity,
                "price_at_sale": float(ti.price_at_sale)
            }
            for ti in t.items
        ]
    }), 200


# --------------------------------------------------
# 🟢 CREATE new transaction (EVERY LOGGED-IN USER)
# --------------------------------------------------
@sales_bp.route("/", methods=["POST"])
@require_auth(roles=None)
def create_transaction():
    data = request.get_json() or {}
    cart_items = data.get("items", [])

    if not cart_items:
        return jsonify({"error": "No items provided"}), 400

    transaction = SalesTransaction(
        user_id=g.current_user.id
    )
    db.session.add(transaction)

    for entry in cart_items:
        item_id = entry.get("item_id")
        qty = entry.get("quantity")

        if not item_id or not qty:
            return jsonify({"error": "item_id and quantity required"}), 400

        item = Item.query.get(item_id)
        if not item:
            return jsonify({"error": f"Item {item_id} not found"}), 400

        if item.quantity < qty:
            return jsonify({"error": f"Not enough stock for {item.name}"}), 400

        item.quantity -= qty

        db.session.add(SalesTransactionItem(
            transaction=transaction,
            item=item,
            quantity=qty,
            price_at_sale=item.price
        ))

    db.session.commit()

    return jsonify({
        "message": "Transaction recorded",
        "transaction_id": transaction.id
    }), 201


# --------------------------------------------------
# 🔵 UPDATE transaction (ADMIN ONLY)
# --------------------------------------------------
@sales_bp.route("/<int:id>", methods=["PUT"])
@require_auth(roles=("admin",))
def update_transaction(id):
    t = SalesTransaction.query.get(id)
    if not t:
        return jsonify({"error": "Transaction not found"}), 404

    data = request.get_json() or {}
    new_items = data.get("items", [])

    if not new_items:
        return jsonify({"error": "No items provided"}), 400

    for ti in t.items:
        ti.item.quantity += ti.quantity

    SalesTransactionItem.query.filter_by(transaction_id=t.id).delete()

    for entry in new_items:
        item_id = entry.get("item_id")
        qty = entry.get("quantity")

        if not item_id or not qty:
            return jsonify({"error": "item_id and quantity required"}), 400

        item = Item.query.get(item_id)
        if not item:
            return jsonify({"error": f"Item {item_id} not found"}), 400

        if item.quantity < qty:
            return jsonify({"error": f"Not enough stock for {item.name}"}), 400

        item.quantity -= qty

        db.session.add(SalesTransactionItem(
            transaction=t,
            item=item,
            quantity=qty,
            price_at_sale=item.price
        ))

    db.session.commit()

    return jsonify({
        "message": "Transaction updated",
        "transaction_id": t.id
    }), 200


# --------------------------------------------------
# 🔴 DELETE transaction (ADMIN ONLY)
# --------------------------------------------------
@sales_bp.route("/<int:id>", methods=["DELETE"])
@require_auth(roles=("admin",))
def delete_transaction(id):
    t = SalesTransaction.query.get(id)
    if not t:
        return jsonify({"error": "Transaction not found"}), 404

    for ti in t.items:
        ti.item.quantity += ti.quantity

    db.session.delete(t)
    db.session.commit()

    return jsonify({"message": "Transaction deleted"}), 200
