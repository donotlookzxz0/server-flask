# ml/time_series_forecast.py
# STABLE + REPRODUCIBLE TIME-SERIES DEMAND FORECAST
# Fixes: randomness, shuffle, leakage, instability

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import random

from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset, DataLoader

from db import db
from models.sales_transaction import SalesTransaction
from models.sales_transaction_item import SalesTransactionItem
from models.item import Item


# ===============================
# 0️⃣ FIX RANDOMNESS (NEW)
# ===============================
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


def run_time_series_forecast():
    print("\n[ML] Stable demand prediction started")

    # ===============================
    # 1️⃣ LOAD DATA
    # ===============================
    rows = (
        db.session.query(
            SalesTransaction.date.label("date"),
            Item.category.label("category"),
            SalesTransactionItem.quantity.label("quantity"),
        )
        .select_from(SalesTransaction)
        .join(
            SalesTransactionItem,
            SalesTransaction.id == SalesTransactionItem.transaction_id
        )
        .join(
            Item,
            Item.id == SalesTransactionItem.item_id
        )
        .all()
    )

    if not rows:
        print("[ML] No sales data found")
        return None

    df = pd.DataFrame(rows, columns=["date", "category", "quantity"])
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # ===============================
    # 2️⃣ DAILY CATEGORY SERIES
    # ===============================
    daily = (
        df.groupby(["date", "category"])["quantity"]
        .sum()
        .unstack(fill_value=0)
        .sort_index()
    )

    if len(daily) < 14:
        print("[ML] Not enough data")
        return None

    # ===============================
    # 3️⃣ LOG TRANSFORM
    # ===============================
    values = np.log1p(daily.values)

    # ===============================
    # 4️⃣ TRAIN / TEST SPLIT (NEW)
    # ===============================
    split = int(len(values) * 0.8)
    train_data = values[:split]
    test_data = values[split:]

    scaler = MinMaxScaler()
    train_scaled = scaler.fit_transform(train_data)
    test_scaled = scaler.transform(test_data)

    SEQ_LEN = min(30, len(train_scaled) - 1)

    # ===============================
    # 5️⃣ DATASET (NO SHUFFLE)
    # ===============================
    class TSDataset(Dataset):
        def __init__(self, data):
            self.X, self.y = [], []
            for i in range(len(data) - SEQ_LEN):
                self.X.append(data[i:i + SEQ_LEN])
                self.y.append(data[i + SEQ_LEN])

        def __len__(self):
            return len(self.X)

        def __getitem__(self, idx):
            return (
                torch.tensor(self.X[idx], dtype=torch.float32),
                torch.tensor(self.y[idx], dtype=torch.float32),
            )

    train_ds = TSDataset(train_scaled)
    train_loader = DataLoader(
        train_ds,
        batch_size=16,
        shuffle=False  # ❌ DO NOT SHUFFLE TIME SERIES
    )

    # ===============================
    # 6️⃣ MODEL (SIMPLIFIED, STABLE)
    # ===============================
    class LSTM(nn.Module):
        def __init__(self, features):
            super().__init__()
            self.lstm = nn.LSTM(features, 64, batch_first=True)
            self.fc = nn.Linear(64, features)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1])

    model = LSTM(daily.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.MSELoss()

    # ===============================
    # 7️⃣ TRAIN (MORE EPOCHS)
    # ===============================
    print("[ML] Training...")
    for epoch in range(60):
        total_loss = 0.0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/60 | Loss: {total_loss:.4f}")

    # ===============================
    # 8️⃣ PREDICTION (STABLE)
    # ===============================
    def predict(days):
        model.eval()

        seq = torch.tensor(
            train_scaled[-SEQ_LEN:], dtype=torch.float32
        ).unsqueeze(0)

        preds = []

        for _ in range(days):
            with torch.no_grad():
                next_step = model(seq)

            preds.append(next_step.numpy()[0])
            seq = torch.cat(
                [seq[:, 1:, :], next_step.unsqueeze(1)],
                dim=1
            )

        preds = scaler.inverse_transform(np.array(preds))
        preds = np.expm1(preds)
        return np.clip(preds, 0, None)

    # ===============================
    # 9️⃣ OUTPUT
    # ===============================
    pred_1 = predict(1)[0]
    pred_7 = predict(7)
    pred_30 = predict(30)

    return {
        "tomorrow": dict(zip(daily.columns, pred_1.round().astype(int))),
        "next_7_days": {
            cat: int(pred_7[:, i].sum())
            for i, cat in enumerate(daily.columns)
        },
        "next_30_days": {
            cat: int(pred_30[:, i].sum())
            for i, cat in enumerate(daily.columns)
        }
    }
