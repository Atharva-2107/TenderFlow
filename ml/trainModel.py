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
    
    # Feature columns — must stay consistent with feature_columns.json & rag_api.py /predict-win
    feature_cols = [
        "prime_cost",
        "overhead_pct",
        "profit_pct",
        "estimated_budget",   # restored: was missing in old trainModel
        "complexity_score",
        "competitor_density"
    ]
    
    print("Fetching real bid history from bid_history_v2...")
    try:
        # Fetch only rows where 'won' is determined (not NULL)
        # NOTE: Using bid_history_v2 — this is where bidGeneration.py actually saves data
        response = supabase.table("bid_history_v2").select("*").not_.is_("won", "null").execute()
        real_data = response.data
    except Exception as e:
        print(f"Error fetching from bid_history_v2: {e}")
        try:
            # Fallback to old table
            response = supabase.table("bid_history").select("*").not_.is_("won", "null").execute()
            real_data = response.data
            print("Fell back to bid_history table")
        except Exception as e2:
            print(f"Error fetching from fallback table: {e2}")
            real_data = []

    print(f"Found {len(real_data)} real training records")

    # 2. PREPARE DATAFRAME FROM REAL DATA
    if real_data:
        df_real = pd.DataFrame(real_data)
        
        # bid_history_v2 stores prime_cost in lakhs and final_bid_amount in lakhs
        # We reconstruct estimated_budget if not present
        if "estimated_budget" not in df_real.columns and "final_bid_amount" in df_real.columns:
            df_real["estimated_budget"] = df_real["final_bid_amount"] * 1.15  # budget ~ 15% above bid
        
        # Ensure numeric
        for col in feature_cols:
            if col in df_real.columns:
                df_real[col] = pd.to_numeric(df_real[col], errors='coerce')
        
        # Target — 'won' column
        if "won" in df_real.columns:
            df_real["won"] = df_real["won"].astype(int)
        
        # Filter to relevant columns
        valid_cols = [c for c in feature_cols if c in df_real.columns] + ["won"]
        df_real = df_real[valid_cols].dropna()
        
        # Add any missing feature columns with 0
        for col in feature_cols:
            if col not in df_real.columns:
                df_real[col] = 0.0
    else:
        df_real = pd.DataFrame(columns=feature_cols + ["won"])

    # 3. GENERATE SYNTHETIC DATA (Fallback / Augmentation)
    # Always generate synthetic data for model stability when real data is sparse
    rows = []
    np.random.seed(42)
    
    # If we have lots of real data, use fewer synthetic samples
    n_synthetic = max(500, 1000 - len(df_real) * 2)
    
    for _ in range(n_synthetic):
        prime_cost = np.random.uniform(8, 40)          # in Lakhs
        overhead_pct = np.random.uniform(8, 20)
        profit_pct = np.random.uniform(5, 30)
        # estimated_budget: typically 10-70% above prime cost
        estimated_budget = prime_cost * np.random.uniform(1.1, 1.7)
        complexity_score = np.random.randint(3, 9)
        competitor_density = np.random.randint(2, 12)

        # Synthetic Win Logic:
        # Win when: reasonable profit, fewer competitors, bid within budget
        bid_value = prime_cost * (1 + overhead_pct/100) * (1 + profit_pct/100)
        price_ok = bid_value <= estimated_budget
        
        win = int(
            profit_pct < 18 and
            competitor_density < 8 and
            price_ok
        )

        rows.append({
            "prime_cost": prime_cost,
            "overhead_pct": overhead_pct,
            "profit_pct": profit_pct,
            "estimated_budget": estimated_budget,
            "complexity_score": complexity_score,
            "competitor_density": competitor_density,
            "won": win
        })
    
    df_synthetic = pd.DataFrame(rows)
    
    # Combine real + synthetic data
    df_final = pd.concat([df_synthetic, df_real], ignore_index=True)
    
    print(f"Training on {len(df_final)} records ({len(df_real)} real, {len(df_synthetic)} synthetic)")
    
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
        random_state=42,
        use_label_encoder=False
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # Evaluate
    from sklearn.metrics import accuracy_score
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Model accuracy on test set: {acc:.2%}")

    # 5. SAVE — use get_booster().save_model() so it works with both XGBClassifier and Booster loaders
    os.makedirs("ml", exist_ok=True)
    model.get_booster().save_model("ml/tenderflow_xgboost.json")
    
    # Also save the pkl for XGBClassifier loading (bidGeneration.py uses XGBClassifier.load_model)
    import pickle
    with open("ml/tenderflow_xgboost.pkl", "wb") as f:
        pickle.dump(model, f)
    
    with open("ml/feature_columns.json", "w") as f:
        json.dump(list(X.columns), f)
        
    print(f"✅ Model trained on {len(df_final)} records ({len(df_real)} real) and saved to ml/")
    print(f"   Features: {list(X.columns)}")
    return True

if __name__ == "__main__":
    train_model()
