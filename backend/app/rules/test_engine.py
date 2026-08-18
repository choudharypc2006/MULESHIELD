import pytest
import pandas as pd
import json
import os
from engine import (
    rule_r001, rule_r002, rule_r003, rule_r004, rule_r007, run_all_rules
)

# Load default config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'default_config.json')
with open(CONFIG_PATH, 'r') as f:
    DEFAULT_CONFIG = json.load(f)

def test_r001_fires():
    row = pd.Series({
        "account_age_days": 10,
        "tx_count_30d": 60
    })
    result = rule_r001(row, DEFAULT_CONFIG)
    assert result["fired"] is True
    assert result["rule_id"] == "R001"
    assert "Account age" in result["explanation"]
    assert "days AND" in result["explanation"]

def test_r002_fires():
    row = pd.Series({
        "unique_remitters_30d": 30
    })
    result = rule_r002(row, DEFAULT_CONFIG)
    assert result["fired"] is True
    assert result["rule_id"] == "R002"
    assert "unique remitters" in result["explanation"]

def test_r003_fires():
    row = pd.Series({
        "rapid_inout_ratio": 0.8
    })
    result = rule_r003(row, DEFAULT_CONFIG)
    assert result["fired"] is True
    assert result["rule_id"] == "R003"
    assert "ratio 0.80 exceeds threshold" in result["explanation"]

def test_r004_fires():
    row = pd.Series({
        "cash_deposit_ratio": 0.6
    })
    result = rule_r004(row, DEFAULT_CONFIG)
    assert result["fired"] is True
    assert result["rule_id"] == "R004"
    assert "ratio 0.60 exceeds threshold" in result["explanation"]

def test_r007_fires():
    row = pd.Series({
        "unique_beneficiaries_30d": 25
    })
    result = rule_r007(row, DEFAULT_CONFIG)
    assert result["fired"] is True
    assert result["rule_id"] == "R007"
    assert "unique beneficiaries" in result["explanation"]

def test_run_all_rules_clean_row():
    # A clean row that shouldn't trigger any rules
    row = pd.Series({
        "account_age_days": 100,
        "tx_count_30d": 10,
        "unique_remitters_30d": 5,
        "rapid_inout_ratio": 0.1,
        "cash_deposit_ratio": 0.1,
        "unique_beneficiaries_30d": 5
    })
    
    results = run_all_rules(row, DEFAULT_CONFIG)
    assert len(results) == 0

def test_run_all_rules_multiple_fires():
    # A risky row that triggers R001 and R003
    row = pd.Series({
        "account_age_days": 5,
        "tx_count_30d": 100,
        "unique_remitters_30d": 5,
        "rapid_inout_ratio": 0.9,
        "cash_deposit_ratio": 0.1,
        "unique_beneficiaries_30d": 5
    })
    
    results = run_all_rules(row, DEFAULT_CONFIG)
    assert len(results) == 2
    rule_ids = [res["rule_id"] for res in results]
    assert "R001" in rule_ids
    assert "R003" in rule_ids
