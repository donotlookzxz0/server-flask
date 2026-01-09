from models.item import Item
from . import state
from .trainer import retrain_model


def recommend_for_user(user_id, top_n=5):
    # rebuild after restart
    if not state.score_matrix:
        retrain_model()

    if user_id not in state.score_matrix:
        return []

    ranked = sorted(
        state.score_matrix[user_id].items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    item_ids = [iid for iid, _ in ranked]
    return Item.query.filter(Item.id.in_(item_ids)).all()
