@echo off
setlocal

echo ==============================================
echo  MULESHIELD Backend Setup Pipeline
echo ==============================================

:: Check for python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: python could not be found. Please ensure it is installed and in your PATH.
    exit /b 1
)

:: Check for required modules
python -c "import xgboost, shap, sklearn, pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Missing required Python packages.
    echo Please ensure you have run 'pip install -r requirements.txt' in your virtual environment.
    exit /b 1
)

echo Step 1/3: Generating synthetic dataset (app.data.generate_dataset)...
python -m app.data.generate_dataset
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo Step 2/3: Training ML models ^& evaluating (app.model.train_model)...
python -m app.model.train_model
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo Step 3/3: Generating SHAP explainability reports (app.model.explain)...
python -m app.model.explain
if %errorlevel% neq 0 exit /b %errorlevel%

echo ==============================================
echo  Setup complete! Data and models are ready.
echo ==============================================
