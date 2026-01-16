import numpy as np
import pandas as pd
import xgboost as xgb
import json
from sklearn.model_selection import train_test_split

# 1. GENERATE REALISTIC SYNTHETIC DATA
rows = []

np.random.seed(42)

for _ in range(1500):
    prime_cost = np.random.uniform(8, 40)  # lakhs
    overhead_pct = np.random.uniform(8, 20)
    profit_pct = np.random.uniform(5, 30)
    estimated_budget = prime_cost * np.random.uniform(1.1, 1.7)
    complexity_score = np.random.randint(3, 9)
    competitor_density = np.random.randint(2, 12)

    # Win logic (IMPORTANT)
    win = int(
        profit_pct < 18 and
        competitor_density < 8 and
        (prime_cost / estimated_budget) < 0.85
    )

    rows.append([
        prime_cost,
        overhead_pct,
        profit_pct,
        estimated_budget,
        complexity_score,
        competitor_density,
        win
    ])

df = pd.DataFrame(rows, columns=[
    "prime_cost",
    "overhead_pct",
    "profit_pct",
    "estimated_budget",
    "complexity_score",
    "competitor_density",
    "won"
])

# ----------------------------
# 2. TRAIN MODEL
# ----------------------------
X = df.drop(columns=["won"])
y = df["won"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    eval_metric="logloss",
    random_state=42
)

model.fit(X_train, y_train)

# ----------------------------
# 3. SAVE MODEL + FEATURES
# ----------------------------
model.get_booster().save_model("ml/tenderflow_xgboost.json")

with open("ml/feature_columns.json", "w") as f:
    json.dump(list(X.columns), f)

print("✅ Model retrained and saved successfully")
