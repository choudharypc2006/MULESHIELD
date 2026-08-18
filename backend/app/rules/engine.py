import pandas as pd
from typing import Dict, Any, List

def rule_r001(row: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """R001 New Account Surge"""
    rule_id = "R001"
    conf = config.get(rule_id, {})
    age_max = conf.get("account_age_days_max", 30)
    tx_min = conf.get("tx_count_30d_min", 50)
    severity = conf.get("severity", "HIGH")

    age = row.get("account_age_days", float("inf"))
    tx_count = row.get("tx_count_30d", 0)

    fired = age < age_max and tx_count > tx_min
    explanation = f"Account age {age} < {age_max} days AND {tx_count} transactions in 30 days > {tx_min}" if fired else ""

    return {
        "rule_id": rule_id,
        "fired": bool(fired),
        "severity": severity,
        "explanation": explanation
    }

def rule_r002(row: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """R002 Smurfing Pattern"""
    rule_id = "R002"
    conf = config.get(rule_id, {})
    remitters_min = conf.get("unique_remitters_30d_min", 25)
    severity = conf.get("severity", "MEDIUM")

    remitters = row.get("unique_remitters_30d", 0)

    fired = remitters > remitters_min
    explanation = f"{remitters} unique remitters in 30 days exceeds threshold of {remitters_min}" if fired else ""

    return {
        "rule_id": rule_id,
        "fired": bool(fired),
        "severity": severity,
        "explanation": explanation
    }

def rule_r003(row: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """R003 Rapid In-Out"""
    rule_id = "R003"
    conf = config.get(rule_id, {})
    ratio_min = conf.get("rapid_inout_ratio_min", 0.6)
    severity = conf.get("severity", "HIGH")

    ratio = row.get("rapid_inout_ratio", 0.0)

    fired = ratio > ratio_min
    explanation = f"Rapid in-out ratio {ratio:.2f} exceeds threshold of {ratio_min}" if fired else ""

    return {
        "rule_id": rule_id,
        "fired": bool(fired),
        "severity": severity,
        "explanation": explanation
    }

def rule_r004(row: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """R004 Cash Concentration"""
    rule_id = "R004"
    conf = config.get(rule_id, {})
    ratio_min = conf.get("cash_deposit_ratio_min", 0.5)
    severity = conf.get("severity", "MEDIUM")

    ratio = row.get("cash_deposit_ratio", 0.0)

    fired = ratio > ratio_min
    explanation = f"Cash deposit ratio {ratio:.2f} exceeds threshold of {ratio_min}" if fired else ""

    return {
        "rule_id": rule_id,
        "fired": bool(fired),
        "severity": severity,
        "explanation": explanation
    }

def rule_r007(row: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """R007 Beneficiary Fanout"""
    rule_id = "R007"
    conf = config.get(rule_id, {})
    beneficiaries_min = conf.get("unique_beneficiaries_30d_min", 20)
    severity = conf.get("severity", "MEDIUM")

    beneficiaries = row.get("unique_beneficiaries_30d", 0)

    fired = beneficiaries > beneficiaries_min
    explanation = f"{beneficiaries} unique beneficiaries in 30 days exceeds threshold of {beneficiaries_min}" if fired else ""

    return {
        "rule_id": rule_id,
        "fired": bool(fired),
        "severity": severity,
        "explanation": explanation
    }

def run_all_rules(row: pd.Series, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Runs every rule and returns which fired."""
    rules = [
        rule_r001,
        rule_r002,
        rule_r003,
        rule_r004,
        rule_r007
    ]
    
    results = []
    for rule_func in rules:
        res = rule_func(row, config)
        if res["fired"]:
            results.append(res)
            
    return results
