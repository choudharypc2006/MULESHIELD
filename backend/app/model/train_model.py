import pandas as pd
import numpy as np
import json
import os
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, average_precision_score,
    PrecisionRecallDisplay, ConfusionMatrixDisplay
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

def train():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'synthetic_accounts.csv')
    model_path = os.path.join(base_dir, 'model', 'best_model.joblib')
    importances_path = os.path.join(base_dir, 'model', 'feature_importances.json')
    reports_dir = os.path.join(base_dir, 'model', 'reports')

    os.makedirs(reports_dir, exist_ok=True)

    print(f"Loading data from {data_path}...")
    if not os.path.exists(data_path):
        print("Data not found! Please run generate_dataset.py first.")
        return

    df = pd.read_csv(data_path)

    X = df.drop(columns=['is_mule'])
    y = df['is_mule']

    # Compute scale_pos_weight for XGBoost
    num_neg = (y == 0).sum()
    num_pos = (y == 1).sum()
    scale_pos_weight = num_neg / num_pos if num_pos > 0 else 1.0

    models = {
        "Random Forest": RandomForestClassifier(
            class_weight='balanced', n_estimators=200, random_state=42
        ),
        "XGBoost": XGBClassifier(
            scale_pos_weight=scale_pos_weight, random_state=42, eval_metric='logloss'
        ),
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight='balanced', max_iter=2000, random_state=42)
        )
    }

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results = {}

    print("\nRunning 5-fold cross-validation...")
    for name, model in models.items():
        print(f"Evaluating {name}...")
        f1_scores, pr_aucs, roc_aucs = [], [], []

        for train_idx, test_idx in skf.split(X, y):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            f1_scores.append(f1_score(y_test, y_pred, zero_division=0))
            pr_aucs.append(average_precision_score(y_test, y_proba))
            roc_aucs.append(roc_auc_score(y_test, y_proba))

        results[name] = {
            "F1": (np.mean(f1_scores), np.std(f1_scores)),
            "PR-AUC": (np.mean(pr_aucs), np.std(pr_aucs)),
            "ROC-AUC": (np.mean(roc_aucs), np.std(roc_aucs)),
            "model_obj": model
        }

    # Print comparison table
    print("\n" + "="*85)
    print(f"{'Model':<22} | {'F1 Score':<18} | {'PR-AUC':<18} | {'ROC-AUC':<18}")
    print("-" * 85)
    for name, res in results.items():
        f1_str = f"{res['F1'][0]:.4f} ± {res['F1'][1]:.4f}"
        pr_str = f"{res['PR-AUC'][0]:.4f} ± {res['PR-AUC'][1]:.4f}"
        roc_str = f"{res['ROC-AUC'][0]:.4f} ± {res['ROC-AUC'][1]:.4f}"
        print(f"{name:<22} | {f1_str:<18} | {pr_str:<18} | {roc_str:<18}")
    print("="*85 + "\n")

    # Determine best model by mean PR-AUC (often the best metric for highly imbalanced data)
    best_model_name = max(results.keys(), key=lambda k: results[k]['PR-AUC'][0])
    best_model = results[best_model_name]['model_obj']
    print(f"Best model selected: {best_model_name}")

    # Retrain best model on standard 80/20 split to generate clean plots and save
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)
    print(f"\nRetraining {best_model_name} on 80% data for final export...")
    best_model.fit(X_train, y_train)

    y_pred = best_model.predict(X_test)
    y_proba = best_model.predict_proba(X_test)[:, 1]

    # Save PR curve
    pr_fig, ax = plt.subplots(figsize=(8, 6))
    PrecisionRecallDisplay.from_predictions(y_test, y_proba, ax=ax, name=best_model_name)
    ax.set_title(f'Precision-Recall Curve ({best_model_name})')
    pr_curve_path = os.path.join(reports_dir, 'pr_curve.png')
    pr_fig.savefig(pr_curve_path)
    plt.close(pr_fig)

    # Save Confusion Matrix
    cm_fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=ax, cmap='Blues')
    ax.set_title(f'Confusion Matrix ({best_model_name})')
    cm_path = os.path.join(reports_dir, 'confusion_matrix.png')
    cm_fig.savefig(cm_path)
    plt.close(cm_fig)

    print(f"Saved PR curve to {pr_curve_path}")
    print(f"Saved Confusion Matrix to {cm_path}")

    # Save the model
    joblib.dump(best_model, model_path)
    print(f"Saved best model to {model_path}")

    # Extract feature importances if the model supports it
    model_for_importances = best_model
    # If the model is in a pipeline (e.g. LogisticRegression), get the underlying estimator
    if hasattr(best_model, 'named_steps'):
        model_for_importances = best_model.named_steps[list(best_model.named_steps.keys())[-1]]

    if hasattr(model_for_importances, 'feature_importances_'):
        print(f"Extracting top 10 global feature importances...")
        importances = model_for_importances.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        top_10 = []
        for i in range(10):
            feature_name = X.columns[indices[i]]
            importance_value = importances[indices[i]]
            top_10.append({
                "feature": feature_name,
                "importance": float(importance_value)
            })
            
        with open(importances_path, 'w') as f:
            json.dump(top_10, f, indent=4)
        print(f"Saved feature importances to {importances_path}")
    elif hasattr(model_for_importances, 'coef_'):
        print(f"Extracting top 10 absolute coefficients for feature importance...")
        importances = np.abs(model_for_importances.coef_[0])
        indices = np.argsort(importances)[::-1]
        
        top_10 = []
        for i in range(10):
            feature_name = X.columns[indices[i]]
            importance_value = importances[indices[i]]
            top_10.append({
                "feature": feature_name,
                "importance": float(importance_value)
            })
            
        with open(importances_path, 'w') as f:
            json.dump(top_10, f, indent=4)
        print(f"Saved feature importances to {importances_path}")

    print("Done.")

if __name__ == "__main__":
    train()
