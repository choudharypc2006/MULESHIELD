#!/usr/bin/env bash
set -e

echo "=============================================="
echo " MULESHIELD Backend Setup Pipeline"
echo "=============================================="

# Check if python is available
if ! command -v python &> /dev/null; then
    echo "ERROR: python could not be found. Please ensure it is installed and in your PATH."
    exit 1
fi

# Check for required modules to verify requirements.txt was run
if ! python -c "import xgboost, shap, sklearn, pandas" &> /dev/null; then
    echo "ERROR: Missing required Python packages."
    echo "Please ensure you have run 'pip install -r requirements.txt' in your virtual environment."
    exit 1
fi

echo "Step 1/3: Generating synthetic dataset (app.data.generate_dataset)..."
python -m app.data.generate_dataset

echo ""
echo "Step 2/3: Training ML models & evaluating (app.model.train_model)..."
python -m app.model.train_model

echo ""
echo "Step 3/3: Generating SHAP explainability reports (app.model.explain)..."
python -m app.model.explain

echo "=============================================="
echo " Setup complete! Data and models are ready."
echo "=============================================="
