import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split

print("🤖 Generative AI Training Started...")

# 1. GENERATE SYNTHETIC DATA
# We create 1,000 fake past bids to teach the model the rules of the market.
np.random.seed(42)
n_samples = 1000

data = {
    # The inputs coming from your frontend
    'prime_cost': np.random.uniform(50000, 200000, n_samples),
    'overhead_pct': np.random.uniform(5, 25, n_samples),
    'profit_pct': np.random.uniform(5, 40, n_samples),
    
    # Hidden market factors (we assume these exist in the background)
    'competitor_count': np.random.randint(1, 15, n_samples),
    'market_benchmark': np.random.uniform(60000, 250000, n_samples)
}
df = pd.DataFrame(data)

# Calculate the Final Bid for these fake rows
df['final_bid'] = df['prime_cost'] * (1 + df['overhead_pct']/100) * (1 + df['profit_pct']/100)

# 2. DEFINE THE "WIN" LOGIC (The Ground Truth)
# We teach the AI: "If your bid is much higher than the benchmark, you lose."
def define_winner(row):
    # Ratio: Your Price / Market Average
    price_ratio = row['final_bid'] / row['market_benchmark']
    
    # Base probability starts at 50%
    prob = 0.5 
    
    # If you are expensive (ratio > 1.0), prob drops fast
    if price_ratio > 1.0: prob -= (price_ratio - 1.0) * 2
    # If you are cheap (ratio < 1.0), prob increases
    else: prob += (1.0 - price_ratio) * 1.5
    
    # Penalize high overheads (inefficiency)
    if row['overhead_pct'] > 15: prob -= 0.1
    
    # Add some randomness (luck)
    prob += np.random.normal(0, 0.05)
    
    return 1 if prob > 0.6 else 0 # 1 = Win, 0 = Loss

df['won'] = df.apply(define_winner, axis=1)

# 3. TRAIN XGBOOST
print("🧠 Training XGBoost Classifier...")

X = df[['final_bid', 'prime_cost', 'overhead_pct', 'profit_pct', 'competitor_count']]
y = df['won']

model = xgb.XGBClassifier(
    n_estimators=100, 
    learning_rate=0.1, 
    max_depth=4, 
    objective='binary:logistic'
)
model.fit(X, y)

# 4. SAVE THE BRAIN
joblib.dump(model, "ml/tenderflow_xgboost.pkl")
print("Model saved successfully")