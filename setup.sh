#!/bin/bash
# Quick setup script for SHAP-SDD project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Test installation
python -c "from pysdd.sdd import SddManager, Vtree; print('PySDD works!')"
python -c "from src.shap.compute_shap import compute_shap_scores; print('SHAP module works!')"
echo "Setup complete! Your SHAP-SDD project is ready."
echo "To activate the environment in the future, run: source venv/bin/activate"