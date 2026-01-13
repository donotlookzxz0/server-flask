# models/ai_recommendation.py
from db import db
from datetime import datetime

class AIRecommendation(db.Model):
    __tablename__ = "ai_recommendations"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False
    )

    score = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
