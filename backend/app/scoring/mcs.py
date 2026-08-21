import os
import sys
import json
import joblib
import pandas as pd
from typing import Dict, Any, List

from app.rules.engine import run_all_rules

WEIGHTS = {
    "rule_signal": 0.5,
    "ml_signal": 0.5
}

_df = None
_model = None
_config = None

def load_data():
    """Loads synthetic_accounts.csv and the trained model once."""
    global _df, _model, _config
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'synthetic_accounts.csv')
    model_path = os.path.join(base_dir, 'model', 'best_model.joblib')
    config_path = os.path.join(base_dir, 'rules', 'default_config.json')

    if not os.path.exists(data_path) or not os.path.exists(model_path):
        sys.exit("ERROR: synthetic_accounts.csv or best_model.joblib don't exist. Please run ./setup.sh first.")

    _df = pd.read_csv(data_path)
    _model = joblib.load(model_path)
    
    with open(config_path, 'r') as f:
        _config = json.load(f)

def get_config() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'rules', 'default_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def update_config(updates: Dict[str, Any]):
    global _config
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'rules', 'default_config.json')
    
    current_config = get_config()
    
    # Merge partial update
    for rule_id, rule_conf in updates.items():
        if rule_id in current_config and isinstance(current_config[rule_id], dict) and isinstance(rule_conf, dict):
            current_config[rule_id].update(rule_conf)
        else:
            current_config[rule_id] = rule_conf
            
    with open(config_path, 'w') as f:
        json.dump(current_config, f, indent=4)
        
    _config = current_config

def compute_mcs(account_id: int) -> Dict[str, Any]:
    if _df is None or _model is None:
        load_data()
        
    if account_id < 0 or account_id >= len(_df):
        return None

    row = _df.iloc[account_id]
    
    # 1. Rule signal
    fired_rules = run_all_rules(row, _config)
    rule_signal = (len(fired_rules) / 5.0) * 100.0
    
    # 2. ML signal
    X = _df.drop(columns=['is_mule'])
    row_features = X.iloc[[account_id]]
    prob = _model.predict_proba(row_features)[0]
    ml_signal = prob[1] * 100.0
    
    # MCS Score
    mcs_score = (rule_signal * WEIGHTS["rule_signal"]) + (ml_signal * WEIGHTS["ml_signal"])
    mcs_score = round(mcs_score, 2)
    
    # Risk bands
    if mcs_score < 40:
        risk_band = "Low"
    elif mcs_score <= 70:
        risk_band = "Medium"
    else:
        risk_band = "High"
        
    return {
        "account_id": account_id,
        "mcs_score": mcs_score,
        "risk_band": risk_band,
        "rule_signal": round(rule_signal, 2),
        "ml_signal": round(ml_signal, 2),
        "triggered_rules": fired_rules
    }

def compute_all_scores() -> List[Dict[str, Any]]:
    if _df is None:
        load_data()
        
    scores = []
    for i in range(len(_df)):
        scores.append(compute_mcs(i))
    return scores
