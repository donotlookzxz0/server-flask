import threading
from .trainer import update_model_with_transactions
from models.sales_transaction import SalesTransaction

def on_successful_payment():
    """
    Called AFTER DB commit.
    Updates recommender asynchronously using only new transactions.
    """
    # get last transaction(s)
    latest_tx = SalesTransaction.query.order_by(SalesTransaction.date.desc()).limit(1).all()

    def background_update():
        try:
            update_model_with_transactions(latest_tx)
        except Exception as e:
            print("WARNING: incremental recommender update failed:", e)

    threading.Thread(target=background_update, daemon=True).start()
