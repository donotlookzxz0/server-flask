import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from models.item import Item
from models.ai_recommendation import AIRecommendation
from db import db
from .model import MFModel
from .dataset import build_interactions
from . import state

# CONFIG
TOP_N = 10


class InteractionDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def retrain_model(epochs=2):
    """
    Full retraining from scratch
    Persists TOP-N item scores per user only
    """
    interactions = build_interactions()

    if not interactions:
        state.model = None
        state.user_map = {}
        state.item_map = {}
        state.score_matrix = {}
        return

    user_ids = list(interactions.keys())
    item_ids = [i.id for i in Item.query.all()]

    state.user_map = {uid: idx for idx, uid in enumerate(user_ids)}
    state.item_map = {iid: idx for idx, iid in enumerate(item_ids)}

    # Build training data
    data = []
    for uid, items_ in interactions.items():
        uidx = state.user_map[uid]
        for iid, qty in items_.items():
            if iid in state.item_map:
                data.append((uidx, state.item_map[iid], float(qty)))

    loader = DataLoader(
        InteractionDataset(data),
        batch_size=8,
        shuffle=True
    )

    model = MFModel(len(state.user_map), len(state.item_map))
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    model.train()
    for _ in range(epochs):
        for u, i, q in loader:
            opt.zero_grad()
            loss = loss_fn(model(u.long(), i.long()), q.float())
            loss.backward()
            opt.step()

    # =========================
    # UPDATE STATE (TOP-N ONLY)
    # =========================
    model.eval()
    state.model = model
    state.score_matrix = {}

    with torch.no_grad():
        for uid, uidx in state.user_map.items():
            scores = []

            for iid, iidx in state.item_map.items():
                score = (
                    model.user_emb.weight[uidx]
                    * model.item_emb.weight[iidx]
                ).sum().item()
                scores.append((iid, score))

            scores.sort(key=lambda x: x[1], reverse=True)
            state.score_matrix[uid] = dict(scores[:TOP_N])


# ======================================================
# INCREMENTAL UPDATE (NEW TRANSACTIONS ONLY)
# ======================================================
def update_model_with_transactions(new_transactions, epochs=5):
    """
    Incremental update using new transactions only.
    Recomputes TOP-N scores for affected users.
    """
    if state.model is None or not state.user_map or not state.item_map:
        retrain_model()
        return

    # -------------------------
    # Detect new users/items
    # -------------------------
    existing_user_ids = set(state.user_map.keys())
    existing_item_ids = set(state.item_map.keys())

    new_user_ids = {tx.user_id for tx in new_transactions} - existing_user_ids

    new_item_ids = set()
    for tx in new_transactions:
        new_item_ids.update(ti.item_id for ti in tx.items)
    new_item_ids -= existing_item_ids

    # Update user_map
    next_user_idx = len(state.user_map)
    for uid in new_user_ids:
        state.user_map[uid] = next_user_idx
        next_user_idx += 1

    # Update item_map
    next_item_idx = len(state.item_map)
    for iid in new_item_ids:
        state.item_map[iid] = next_item_idx
        next_item_idx += 1

    # -------------------------
    # Expand model
    # -------------------------
    old_model = state.model
    n_users = len(state.user_map)
    n_items = len(state.item_map)

    new_model = MFModel(n_users, n_items)

    # Copy old user embeddings
    new_model.user_emb.weight.data[:old_model.user_emb.num_embeddings] = \
        old_model.user_emb.weight.data

    # Copy old item embeddings
    new_model.item_emb.weight.data[:old_model.item_emb.num_embeddings] = \
        old_model.item_emb.weight.data

    state.model = new_model

    # -------------------------
    # Train on new data only
    # -------------------------
    data = []
    for tx in new_transactions:
        uidx = state.user_map[tx.user_id]
        for ti in tx.items:
            if ti.item_id in state.item_map:
                iidx = state.item_map[ti.item_id]
                data.append((uidx, iidx, float(ti.quantity)))

    if not data:
        return

    loader = DataLoader(
        InteractionDataset(data),
        batch_size=32,
        shuffle=True
    )

    opt = torch.optim.Adam(new_model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    new_model.train()
    for _ in range(epochs):
        for u, i, q in loader:
            opt.zero_grad()
            loss = loss_fn(new_model(u.long(), i.long()), q.float())
            loss.backward()
            opt.step()

    # -------------------------
    # Recompute TOP-N for affected users
    # -------------------------
    new_model.eval()
    affected_users = {tx.user_id for tx in new_transactions}

    with torch.no_grad():
        for uid in affected_users:
            uidx = state.user_map[uid]
            scores = []

            for iid, iidx in state.item_map.items():
                score = (
                    new_model.user_emb.weight[uidx]
                    * new_model.item_emb.weight[iidx]
                ).sum().item()
                scores.append((iid, score))

            scores.sort(key=lambda x: x[1], reverse=True)
            state.score_matrix[uid] = dict(scores[:TOP_N])
