import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from models.item import Item
from .model import MFModel
from .dataset import build_interactions
from . import state


class InteractionDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def retrain_model(epochs=30):
    """
    Full retraining from scratch (existing function)
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

    data = []
    for uid, items_ in interactions.items():
        uidx = state.user_map[uid]
        for iid, qty in items_.items():
            if iid in state.item_map:
                data.append((uidx, state.item_map[iid], float(qty)))

    loader = DataLoader(InteractionDataset(data), batch_size=32, shuffle=True)

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

    # update state
    model.eval()
    state.model = model
    state.score_matrix = {}

    with torch.no_grad():
        for uid, uidx in state.user_map.items():
            state.score_matrix[uid] = {}
            for iid, iidx in state.item_map.items():
                score = (model.user_emb.weight[uidx] * model.item_emb.weight[iidx]).sum().item()
                state.score_matrix[uid][iid] = score



# NEW FUNCTION: Incremental Update
def update_model_with_transactions(new_transactions, epochs=5):
    """
    Update model incrementally with new transactions only.
    Adds new users/items to embedding matrices.
    """
    if state.model is None or not state.user_map or not state.item_map:
        # no model exists, fall back to full retrain
        retrain_model()
        return

    # new users/items
    existing_user_ids = set(state.user_map.keys())
    existing_item_ids = set(state.item_map.keys())

    new_user_ids = {tx.user_id for tx in new_transactions} - existing_user_ids
    new_item_ids = set()
    for tx in new_transactions:
        new_item_ids.update({ti.item_id for ti in tx.items})
    new_item_ids -= existing_item_ids

    # Update user_map and item_map
    next_user_idx = len(state.user_map)
    for uid in new_user_ids:
        state.user_map[uid] = next_user_idx
        next_user_idx += 1

    next_item_idx = len(state.item_map)
    for iid in new_item_ids:
        state.item_map[iid] = next_item_idx
        next_item_idx += 1

    n_users = len(state.user_map)
    n_items = len(state.item_map)

    # Expand embedding matrices for new users/items
    old_model = state.model
    new_model = MFModel(n_users, n_items)
    new_model.load_state_dict(old_model.state_dict(), strict=False)  # keep old weights

    state.model = new_model

    # Build dataset for new transactions only
    data = []
    for tx in new_transactions:
        uidx = state.user_map[tx.user_id]
        for ti in tx.items:
            if ti.item_id in state.item_map:
                iidx = state.item_map[ti.item_id]
                data.append((uidx, iidx, float(ti.quantity)))

    if not data:
        return

    loader = DataLoader(InteractionDataset(data), batch_size=32, shuffle=True)
    opt = torch.optim.Adam(new_model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    new_model.train()
    for _ in range(epochs):
        for u, i, q in loader:
            opt.zero_grad()
            loss = loss_fn(new_model(u.long(), i.long()), q.float())
            loss.backward()
            opt.step()

    # Update score matrix for affected users/items
    new_model.eval()
    with torch.no_grad():
        for tx in new_transactions:
            uid = tx.user_id
            uidx = state.user_map[uid]
            state.score_matrix.setdefault(uid, {})
            for ti in tx.items:
                iid = ti.item_id
                iidx = state.item_map[iid]
                state.score_matrix[uid][iid] = (new_model.user_emb.weight[uidx] * new_model.item_emb.weight[iidx]).sum().item()
