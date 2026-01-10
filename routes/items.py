from flask import Blueprint, request, jsonify
from models.item import Item
from models.sales_transaction_item import SalesTransactionItem

# from utils.auth_restrict import require_auth

from db import db

items_bp = Blueprint('items', __name__)

def valid_categories():
    return [choice for choice in Item.__table__.columns.category.type.enums]


# 🟢 GET all items
@items_bp.route('/', methods=['GET'])
# @require_auth(roles=("admin"),)
def get_items():
    try:
        items = Item.query.all()
        return jsonify([
            {
                'id': i.id,
                'name': i.name,
                'quantity': i.quantity,
                'category': i.category,
                'price': float(i.price),
                'barcode': i.barcode
            } for i in items
        ]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 GET item by ID
@items_bp.route('/<int:id>', methods=['GET'])
# @require_auth()
def get_item_by_id(id):
    try:
        item = Item.query.get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        return jsonify({
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'category': item.category,
            'price': float(item.price),
            'barcode': item.barcode
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 GET item by barcode
@items_bp.route('/barcode/<string:barcode>', methods=['GET'])
# @require_auth()
def get_item_by_barcode(barcode):
    try:
        item = Item.query.filter_by(barcode=barcode).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        return jsonify({
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'category': item.category,
            'price': float(item.price),
            'barcode': item.barcode
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 CREATE item
@items_bp.route('/', methods=['POST'])
# @require_auth(roles=("admin",))
def create_item():
    try:
        data = request.get_json() or {}

        name = data.get('name')
        quantity = data.get('quantity', 0)
        category = data.get('category')
        price = data.get('price')
        barcode = data.get('barcode')

        # Validate required
        if not name or not barcode or category is None or price is None:
            return jsonify({'error': 'name, barcode, category, and price are required'}), 400

        # Validate numeric fields
        if quantity < 0:
            return jsonify({'error': 'quantity must be 0 or greater'}), 400
        if float(price) < 0:
            return jsonify({'error': 'price must be 0 or greater'}), 400

        # Validate category
        if category not in valid_categories():
            return jsonify({'error': f"Invalid category. Allowed: {', '.join(valid_categories())}"}), 400

        # Unique barcode
        existing = Item.query.filter_by(barcode=barcode).first()
        if existing:
            return jsonify({'error': 'barcode already exists'}), 400

        new_item = Item(
            name=name,
            quantity=quantity,
            category=category,
            price=price,
            barcode=barcode
        )

        db.session.add(new_item)
        db.session.commit()

        return jsonify({
            'id': new_item.id,
            'name': new_item.name,
            'quantity': new_item.quantity,
            'category': new_item.category,
            'price': float(new_item.price),
            'barcode': new_item.barcode
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# 🟡 UPDATE item
@items_bp.route('/<int:id>', methods=['PUT'])
# @require_auth()
def update_item(id):
    try:
        data = request.get_json() or {}

        item = Item.query.get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Validate category if provided
        category = data.get('category')
        if category and category not in valid_categories():
            return jsonify({'error': f"Invalid category. Allowed: {', '.join(valid_categories())}"}), 400

        # Validate quantity & price
        if 'quantity' in data and data['quantity'] < 0:
            return jsonify({'error': 'quantity must be 0 or greater'}), 400
        if 'price' in data and float(data['price']) < 0:
            return jsonify({'error': 'price must be 0 or greater'}), 400

        # Barcode uniqueness
        if 'barcode' in data and data['barcode'] != item.barcode:
            existing = Item.query.filter_by(barcode=data['barcode']).first()
            if existing:
                return jsonify({'error': 'barcode already exists'}), 400
            item.barcode = data['barcode']

        # Update fields
        if 'name' in data:
            item.name = data['name']
        if category:
            item.category = category
        if 'price' in data:
            item.price = data['price']
        if 'quantity' in data:
            item.quantity = data['quantity']

        db.session.commit()

        return jsonify({
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'category': item.category,
            'price': float(item.price),
            'barcode': item.barcode
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# 🔴 DELETE item
@items_bp.route('/<int:id>', methods=['DELETE'])
# @require_auth()
def delete_item(id):
    try:
        item = Item.query.get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Check if item exists in ANY transaction
        has_sales = SalesTransactionItem.query.filter_by(item_id=id).first()
        if has_sales:
            return jsonify({'error': 'Item was sold and cannot be deleted'}), 400

        db.session.delete(item)
        db.session.commit()

        return jsonify({'message': 'Item deleted'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
