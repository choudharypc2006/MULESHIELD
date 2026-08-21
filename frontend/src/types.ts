export type RiskBand = 'Low' | 'Medium' | 'High';

export interface AccountSummary {
  account_id: number;
  mcs_score: number;
  risk_band: RiskBand;
}

export interface TriggeredRule {
  rule_id: string;
  fired: boolean;
  severity: string;
  explanation: string;
}

export interface AccountDetail {
  account_id: number;
  mcs_score: number;
  risk_band: RiskBand;
  rule_signal: number;
  ml_signal: number;
  triggered_rules: TriggeredRule[];
  top_shap_contributions: string[];
  action?: 'mule' | 'clear' | 'escalate' | null;
}
