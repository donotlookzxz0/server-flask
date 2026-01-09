from collections import defaultdict
from models.sales_transaction import SalesTransaction

def build_interactions():
    user_item = defaultdict(lambda: defaultdict(int))

    transactions = SalesTransaction.query.all()
    for tx in transactions:
        for ti in tx.items:
            user_item[tx.user_id][ti.item_id] += ti.quantity

    return user_item
