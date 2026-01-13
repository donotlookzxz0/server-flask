from models.item import Item
from models.ai_recommendation import AIRecommendation

def recommend_for_user(user_id, top_n=5):
    rows = (
        AIRecommendation.query
        .filter_by(user_id=user_id)
        .order_by(AIRecommendation.score.desc())
        .limit(top_n)
        .all()
    )

    if not rows:
        return []

    item_ids = [r.item_id for r in rows]
    return Item.query.filter(Item.id.in_(item_ids)).all()