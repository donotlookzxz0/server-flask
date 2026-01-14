import torch.nn as nn

class MFModel(nn.Module):
    def __init__(self, n_users, n_items, n_factors=8):
        super().__init__()
        self.user_emb = nn.Embedding(n_users, n_factors)
        self.item_emb = nn.Embedding(n_items, n_factors)

    def forward(self, u, i):
        return (self.user_emb(u) * self.item_emb(i)).sum(dim=1)
