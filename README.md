# NetLinkArena - Link Prediction Challenge

## 🎯 Challenge Overview
**Can you predict hidden connections in a scientific citation network?**

NetLinkArena is a link prediction competition where participants must infer missing citation links between research papers. Your score is determined by **AUC-ROC** - how well you rank true connections above false ones!

---

## 📊 Dataset Information

The dataset was processed using the `Planetoid` library with the following graph properties:

* **Undirected:** True
* **Self-loops:** False
* **Isolated Nodes:** False
* **Total Nodes:** 3,327
* **Total Node Features:** 2,742
* **Total Edges:** 9,104 (train + val + test)

---

## 🔥 What Makes This Hard?

- ✅ **Sparse Features** - 96.5% of feature values are zeros (bag-of-words representation)
- ✅ **Graph Structure Critical** - Node features alone are insufficient; GNN models required
- ✅ **Obfuscated Features** - Node features have been permuted and noise-injected to prevent information leakage
- ✅ **Large Graph** - 3,327 nodes with complex

**Expected Performance:**
- Random baseline: ~50% AUC-ROC
- Feature-only model: ~55-60% AUC-ROC
- Good GNN: ~70-75% AUC-ROC
- Excellent GNN: **>80% AUC-ROC** 🎯

---

## 📈 Dataset Distribution

| Split | Positive Edges | Negative Edges | Total | Label Ratio |
|:------|:--------------|:---------------|:------|:------------|
| **Training** | 2,730 | 2,730 | 5,460 | 1:1 (balanced) |
| **Validation** | 911 | 911 | 1,822 | 1:1 (balanced) |
| **Testing** | 911 | 911 | 1,822 | 1:1 (balanced) |

---

## 📋 Quick Links

- 📤 **[Submit Predictions](https://forms.gle/wh5gZXWGg2qnWNCFA)** ← Start here!
- 🏆 **[View Leaderboard](https://ignatiusbalayo.github.io/NetLinkArena/leaderboard.html)**
- 📥 **[Download Dataset](https://github.com/ignatiusbalayo/NetLinkArena/releases/download/v1.0/NetLinkArena_Dataset.zip)**
- 📖 **[Detailed Submission Guide](submissions/README.md)**

---

## 1. Repository Structure
```
.
├── data/
│   ├── public/
│   │   ├── node_features.csv      # Features for ALL nodes
│   │   ├── train_edges.csv        # Training edges WITH labels
│   │   ├── val_edges.csv          # Validation edges WITH labels
│   │   ├── test_nodes.csv         # Test edges WITHOUT labels
│   │   └── sample_submission.csv  # Example submission format
│   └── private/
│       └── test_labels.csv        # Hidden (used for evaluation)
├── competition/
│   ├── config.yaml                # Competition settings
│   ├── validate_submission.py     # Validation script
│   ├── evaluate.py                # Scoring script
│   ├── metrics.py                 # AUC-ROC calculation
│   ├── render_leaderboard.py      # Markdown generator
│   ├── generate_html_leaderboard.py  # HTML generator
│   └── process_google_form_submissions.py  # Auto-processing
├── leaderboard/
│   ├── leaderboard.csv            # Scores database
│   └── leaderboard.md             # GitHub-friendly view
├── docs/
│   ├── index.html                 # Landing page redirect
│   ├── leaderboard.html           # Live leaderboard
│   └── leaderboard.css            # Leaderboard styling
└── scripts/
    └── baseline.py                # Simple baseline model
```

---

## 2. Dataset Files

### node_features.csv
Features for **ALL** papers in the network.
```csv
node_id,0,1,2,...,2741
0,0.0,1.0,0.0,...,0.0
1,1.0,0.0,0.0,...,1.0
...
3326,...
```

- **3,327 rows** (one per paper)
- **2,742 features** + node_id column
- **Sparse bag-of-words** (mostly 0/1)

### train_edges.csv & val_edges.csv
Edge examples **WITH** labels.
```csv
source,target,label
15,234,1     ← Citation exists
42,891,0     ← No citation
...
```

### test_nodes.csv
Test edges **WITHOUT** labels - **you must predict!**
```csv
id,source,target
0,456,789
1,123,456
...
```

**See `data/public/sample_submission.csv` for the required output format.**

---

## 3. 📥 Download & Setup
```bash
# Clone repository
git clone https://github.com/ignatiusbalayo/NetLinkArena.git
cd NetLinkArena

# Download dataset
wget https://github.com/ignatiusbalayo/NetLinkArena/releases/download/v1.0/NetLinkArena_Dataset.zip
unzip NetLinkArena_Dataset.zip

# Install dependencies
pip install torch torch-geometric pandas scikit-learn

# Run baseline
python scripts/baseline.py
```

---

## 4. 📤 How to Submit

### **Submit via Google Form:**
**🔗 [https://forms.gle/wh5gZXWGg2qnWNCFA](https://forms.gle/wh5gZXWGg2qnWNCFA)**

### What you need:
1. **Team Name** - Unique identifier (one submission per team)
2. **Model Name** - e.g., GAT, GCN, GraphSAGE
3. **predictions.csv** - Your predictions file

### Required format:
```csv
id,y_pred
0,0.85
1,0.23
...
1821,0.67
```

**Requirements:**
- ✅ Exactly 1,822 rows (excluding header)
- ✅ `id` matches `test_nodes.csv` (0 to 1821)
- ✅ `y_pred` is probability [0, 1]

### Validate before submitting:
```bash
python competition/validate_submission.py predictions.csv
```

### After submission:
- ⏱️ **Automatic processing** in 5-15 minutes
- 🏆 **Check leaderboard:** [Live Leaderboard](https://ignatiusbalayo.github.io/NetLinkArena/leaderboard.html)

---

## 5. 🏆 Leaderboard

**Live Leaderboard:** [https://ignatiusbalayo.github.io/NetLinkArena/leaderboard.html](https://ignatiusbalayo.github.io/NetLinkArena/leaderboard.html)

Features:
- 🎯 Ranked by AUC-ROC score
- 🏅 Kaggle-style ranking (ties share rank)
- 🔍 Search by team name
- 🎨 Filter by model type
- ⏱️ Auto-updates every 15 minutes

---

## 6. Getting Started

### Explore the Data
```python
import pandas as pd

# Load data
features = pd.read_csv('data/public/node_features.csv')
train = pd.read_csv('data/public/train_edges.csv')
test = pd.read_csv('data/public/test_nodes.csv')

print(f"Nodes: {len(features):,}")
print(f"Features: {features.shape[1]-1:,}")
print(f"Training edges: {len(train):,}")
print(f"Test edges: {len(test):,}")
```

### Build a Simple GNN
```python
from torch_geometric.nn import GCNConv
import torch.nn as nn

class LinkPredictor(nn.Module):
    def __init__(self, num_features, hidden_dim):
        super().__init__()
        self.conv1 = GCNConv(num_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        
    def encode(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)
    
    def decode(self, z, edge_index):
        return (z[edge_index[0]] * z[edge_index[1]]).sum(dim=-1)
```

### Generate Predictions
```python
# Get node embeddings
z = model.encode(x, train_edge_index)

# Predict on test edges
test_edge_index = torch.tensor([test['source'].values, test['target'].values])
pred = torch.sigmoid(model.decode(z, test_edge_index))

# Save submission
pd.DataFrame({
    'id': test['id'],
    'y_pred': pred.detach().numpy()
}).to_csv('predictions.csv', index=False)

# Validate before submitting!
# python competition/validate_submission.py predictions.csv
```

---

## 7. Rules

### ✅ Allowed
- Any GNN architecture (GCN, GAT, GraphSAGE, GIN, etc.)
- Feature engineering on node features
- Ensemble models
- Unlimited offline training

### ❌ Not Allowed
- External datasets
- Manual labeling of test edges
- Test set peeking
- **ONE submission per team** (strictly enforced)

---

## 8. Baseline Performance

**Simple 2-layer GCN:**
- Hidden dim: 128 → 64
- Training time: ~20 minutes (CPU)
- Expected AUC-ROC: **0.65-0.75**

**Your goal: Beat the baseline!** 🎯

---

## 9. Tips for Success

- 📊 **Use graph structure** - Features alone won't beat baseline
- 🎯 **Handle sparsity** - 96.5% of features are zeros
- 🔗 **Try different architectures** - GAT, GraphSAGE, GIN
- 💡 **Negative sampling** - Important for link prediction
- ⚖️ **No class imbalance** - Data is perfectly balanced

---

## 10. Resources

- [PyTorch Geometric Tutorial](https://pytorch-geometric.readthedocs.io/)
- [GCN Paper](https://arxiv.org/abs/1609.02907)
- [GAT Paper](https://arxiv.org/abs/1710.10903)
- [Link Prediction Survey](https://arxiv.org/abs/2010.16103)

---

## 11. References

- **Dataset:** Planetoid-CiteSeer
- **Task:** Link Prediction on Citation Networks
- **Framework:** PyTorch Geometric

---

## 12. License

MIT License.

---

**Good luck!** 🚀
