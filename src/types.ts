export interface AssetFeatures {
  id: string;
  runtime_hours: number;
  alarm_rate_7d: number;
  days_since_pm: number;
  criticality: 1 | 2 | 3;
  /** Ground-truth failure within horizon (fixtures only) */
  failed?: boolean;
}

export type Decision = "commit" | "escalate" | "hold";

export interface ScoreResult {
  id: string;
  risk_score: number;
  conformal_interval: [number, number];
  prediction_set: ("low" | "high")[];
  decision: Decision;
  rationale: string;
  alpha: number;
}

export interface BacktestSummary {
  n: number;
  empirical_coverage: number;
  target_coverage: number;
  decisions: Record<Decision, number>;
}
