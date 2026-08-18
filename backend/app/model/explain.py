import os
import sys
import pandas as pd
import numpy as np
import joblib
import json
import matplotlib.pyplot as plt
import shap

def generate_shap_reports():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'synthetic_accounts.csv')
    model_path = os.path.join(base_dir, 'model', 'best_model.joblib')
    reports_dir = os.path.join(base_dir, 'model', 'reports')

    os.makedirs(reports_dir, exist_ok=True)

    print("Loading data and model...")
    df = pd.read_csv(data_path)
    X = df.drop(columns=['is_mule'])
    y = df['is_mule']
    model = joblib.load(model_path)

    print("Predicting probabilities to find sample accounts...")
    probas = model.predict_proba(X)[:, 1]

    # Find specific accounts
    mule_idx = np.where((y == 1) & (probas > 0.9))[0]
    clear_mule_idx = mule_idx[0] if len(mule_idx) > 0 else np.where(y == 1)[0][0]

    clean_idx = np.where((y == 0) & (probas < 0.1))[0]
    clear_clean_idx = clean_idx[0] if len(clean_idx) > 0 else np.where(y == 0)[0][0]

    borderline_idx = np.argsort(np.abs(probas - 0.5))[0]

    samples = {
        "clear_mule": clear_mule_idx,
        "clean": clear_clean_idx,
        "borderline": borderline_idx
    }

    print("Generating SHAP Explainer...")
    explainer = shap.TreeExplainer(model)

    # 1. Summary Plot
    print("Generating summary plot...")
    X_sample = X.sample(500, random_state=42)
    shap_vals_sample = explainer.shap_values(X_sample)
    
    if isinstance(shap_vals_sample, list):
        sv_summary = shap_vals_sample[1]
    else:
        if len(shap_vals_sample.shape) == 3:
            sv_summary = shap_vals_sample[:, :, 1]
        else:
            sv_summary = shap_vals_sample

    plt.figure()
    shap.summary_plot(sv_summary, X_sample, show=False)
    plt.savefig(os.path.join(reports_dir, 'shap_summary.png'), bbox_inches='tight')
    plt.close()

    # 2. Force Plots
    print("Generating force plots...")
    base_value = explainer.expected_value
    if isinstance(base_value, list) or isinstance(base_value, np.ndarray):
        bv = base_value[1]
    else:
        bv = base_value

    for name, idx in samples.items():
        row_X = X.iloc[[idx]]
        row_shap = explainer.shap_values(row_X)
        
        if isinstance(row_shap, list):
            rs = row_shap[1][0]
        else:
            if len(row_shap.shape) == 3:
                rs = row_shap[0, :, 1]
            else:
                rs = row_shap[0]
                
        # Use matplotlib=True to render without JS
        fig = shap.force_plot(bv, rs, row_X.iloc[0], matplotlib=True, show=False)
        plt.savefig(os.path.join(reports_dir, f'shap_force_{name}.png'), bbox_inches='tight')
        plt.close(fig)

    print(f"Saved SHAP reports to {reports_dir}")


def get_explanation(account_id: int) -> dict:
    """
    Returns both the triggered rules and top 3 SHAP feature contributions 
    in plain-language sentences for a given account.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Ensure backend path is in sys.path to import rules engine
    backend_dir = os.path.dirname(base_dir)
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
        
    from app.rules.engine import run_all_rules

    data_path = os.path.join(base_dir, 'data', 'synthetic_accounts.csv')
    model_path = os.path.join(base_dir, 'model', 'best_model.joblib')
    config_path = os.path.join(base_dir, 'rules', 'default_config.json')

    df = pd.read_csv(data_path)
    if account_id < 0 or account_id >= len(df):
        raise ValueError(f"Invalid account_id: {account_id}")

    row = df.iloc[account_id]
    X = df.drop(columns=['is_mule'])
    row_features = X.iloc[[account_id]]

    # 1. Execute Rules Engine
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    triggered_rules = run_all_rules(row, config)
    rule_explanations = [r["explanation"] for r in triggered_rules]

    # 2. Extract SHAP Explanations
    model = joblib.load(model_path)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(row_features)

    if isinstance(shap_values, list):
        mule_shap = shap_values[1][0]
    else:
        if len(shap_values.shape) == 3:
            mule_shap = shap_values[0, :, 1]
        else:
            mule_shap = shap_values[0]

    contributions = []
    for feat, sv in zip(X.columns, mule_shap):
        if sv > 0:  # Only track features that *increased* risk
            val = row_features.iloc[0][feat]
            contributions.append((feat, sv, val))

    contributions.sort(key=lambda x: x[1], reverse=True)
    top_3 = contributions[:3]

    shap_sentences = []
    for feat, sv, val in top_3:
        # Convert log-odds or margin space to an arbitrary "points" metric for plain English
        pts = max(1, int(round(sv * 100))) 
        shap_sentences.append(f"{feat} ({val}) increased risk by {pts} points.")

    return {
        "account_id": account_id,
        "is_mule_label": int(row['is_mule']),
        "triggered_rules": rule_explanations,
        "top_shap_contributions": shap_sentences
    }

if __name__ == "__main__":
    generate_shap_reports()
    
    print("\nTesting get_explanation(0):")
    res = get_explanation(0)
    print(json.dumps(res, indent=2))
