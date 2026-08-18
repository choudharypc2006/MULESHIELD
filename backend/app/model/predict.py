import os
import joblib
import pandas as pd

_model = None

def load_model():
    global _model
    if _model is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, 'model', 'best_model.joblib')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please run train_model.py first.")
        _model = joblib.load(model_path)
    return _model

def predict_proba(row: pd.Series) -> float:
    """
    Loads the saved model and returns a calibrated probability-of-mule score 
    for a single account row.
    """
    model = load_model()
    
    # Convert Series to DataFrame with 1 row
    df = row.to_frame().T
    
    # Predict probability of class 1 (mule)
    proba = model.predict_proba(df)[0][1]
    
    return float(proba)
