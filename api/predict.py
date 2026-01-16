from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import json
import xgboost as xgb

app = FastAPI()

model = None
FEATURES = None

def load_model():
    global model, FEATURES
    if model is None:
        model = xgb.XGBClassifier()
        model.load_model("ml/tenderflow_xgboost.json")
        with open("ml/feature_columns.json") as f:
            FEATURES = json.load(f)

class BidInput(BaseModel):
    prime_cost_lakh: float
    overhead_pct: float
    profit_pct: float
    estimated_budget_lakh: float
    complexity_score: int
    competitor_density: int

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict-win")
def predict_win(data: BidInput):
    load_model()

    X = pd.DataFrame([[
        data.prime_cost_lakh,
        data.overhead_pct,
        data.profit_pct,
        data.estimated_budget_lakh,
        data.complexity_score,
        data.competitor_density
    ]], columns=FEATURES)

    prob = model.predict_proba(X)[0][1]
    return {"win_probability": round(float(prob), 4)}
