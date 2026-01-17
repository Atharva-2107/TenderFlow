import numpy as np
import pandas as pd
import xgboost as xgb
import json
import os
from sklearn.model_selection import train_test_split
from supabase import create_client
from dotenv import load_dotenv

def train_model():
    load_dotenv()
    
    # 1. SETUP & FETCH DATA
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Supabase credentials missing")
        return False
        
    supabase = create_client(url, key)
    
    print("Fetching real bid history...")
    try:
        # Fetch only rows where 'won' is determined (not NULL)
        response = supabase.table("bid_history").select("*").not_.is_("won", "null").execute()
        real_data = response.data
    except Exception as e:
        print(f"Error fetching data: {e}")
        real_data = []

    print(f"Found {len(real_data)} real training records")

    # 2. PREPARE DATAFRAME
    # Columns we can use from Supabase
    feature_cols = [
        "prime_cost", 
        "overhead_pct", 
        "profit_pct", 
        "complexity_score", 
        "competitor_density"
    ]
    
    # Map API keys to DF columns if needed, or assume they match
    # Supabase returns dicts, easy to DataFrame
    if real_data:
        df_real = pd.DataFrame(real_data)
        # Ensure numeric
        for col in feature_cols:
            if col in df_real.columns:
                df_real[col] = pd.to_numeric(df_real[col], errors='coerce')
        
        # Target
        if "won" in df_real.columns:
            df_real["won"] = df_real["won"].astype(int)
        
        # Filter to relevant columns
        valid_cols = [c for c in feature_cols if c in df_real.columns] + ["won"]
        df_real = df_real[valid_cols].dropna()
    else:
        df_real = pd.DataFrame(columns=feature_cols + ["won"])

    # 3. GENERATE SYNTHETIC DATA (Fallback / Augmentation)
    # We always generate some synthetic data to ensure model stability if real data is sparse
    rows = []
    np.random.seed(42)
    
    # If we have lots of real data, reduce synthetic, but for now keep it robust
    n_synthetic = 1000 
    
    for _ in range(n_synthetic):
        prime_cost = np.random.uniform(8, 40)
        overhead_pct = np.random.uniform(8, 20)
        profit_pct = np.random.uniform(5, 30)
        # estimated_budget proxy (not used in feature set directly but used for synthetic label logic)
        estimated_budget = prime_cost * np.random.uniform(1.1, 1.7)
        complexity_score = np.random.randint(3, 9)
        competitor_density = np.random.randint(2, 12)

        # Synthetic Win Logic
        win = int(
            profit_pct < 18 and
            competitor_density < 8 and
            (prime_cost / estimated_budget) < 0.85
        )

        rows.append({
            "prime_cost": prime_cost,
            "overhead_pct": overhead_pct,
            "profit_pct": profit_pct,
            "complexity_score": complexity_score,
            "competitor_density": competitor_density,
            "won": win
        })
    
    df_synthetic = pd.DataFrame(rows)
    
    # Combine
    df_final = pd.concat([df_synthetic, df_real], ignore_index=True)
    
    # 4. TRAIN MODEL
    X = df_final[feature_cols]
    y = df_final["won"]
    
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

    # 5. SAVE
    os.makedirs("ml", exist_ok=True)
    model.get_booster().save_model("ml/tenderflow_xgboost.json")
    
    with open("ml/feature_columns.json", "w") as f:
        json.dump(list(X.columns), f)
        
    print(f"✅ Model trained on {len(df_final)} records ({len(df_real)} real) and saved.")
    return True

if __name__ == "__main__":
    train_model()
