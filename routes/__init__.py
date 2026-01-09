from routes.items import items_bp
from routes.sales import sales_bp
from routes.users import user_routes
from routes.payment import payment_bp
from routes.ml import ml_bp
from routes.recommendation import recommendations_bp
from routes.cash_payment import cash_payment_bp
from routes.admin_cash_payment import admin_cash_bp

__all__ = [
    "items_bp",
    "sales_bp",
    "user_routes",
    "payment_bp",
    "ml_bp",
    "recommendations_bp",
    "cash_payment_bp",
    "admin_cash_bp",
]
