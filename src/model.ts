import type { AssetFeatures, BacktestSummary, Decision, ScoreResult } from "./types.js";

/** Simple logistic-style risk from ops features. Deterministic, no ML framework. */
export function rawRisk(a: AssetFeatures): number {
  const hours = a.runtime_hours / 10000;
  const alarms = a.alarm_rate_7d / 10;
  const pm = a.days_since_pm / 365;
  const crit = (a.criticality - 1) / 2;
  const z = -1.2 + 1.4 * hours + 1.1 * alarms + 0.9 * pm + 0.6 * crit;
  return 1 / (1 + Math.exp(-z));
}

/**
 * Split conformal: calibration residuals |y - s| where y in {0,1}, s = rawRisk.
 * For binary risk we use absolute residual and build an interval around the score.
 */
export function calibrateQuantile(
  calibration: AssetFeatures[],
  alpha: number,
): number {
  if (calibration.length === 0) throw new Error("calibration set empty");
  const scores = calibration
    .map((a) => {
      const s = rawRisk(a);
      const y = a.failed ? 1 : 0;
      return Math.abs(y - s);
    })
    .sort((x, y) => x - y);
  const qLevel = Math.ceil((1 - alpha) * (scores.length + 1)) / scores.length;
  const idx = Math.min(scores.length - 1, Math.max(0, Math.ceil(qLevel * scores.length) - 1));
  return scores[idx]!;
}

export function scoreAsset(
  a: AssetFeatures,
  qHat: number,
  alpha: number,
): ScoreResult {
  const s = rawRisk(a);
  const lo = Math.max(0, s - qHat);
  const hi = Math.min(1, s + qHat);
  const width = hi - lo;

  const prediction_set: ("low" | "high")[] = [];
  if (lo < 0.5) prediction_set.push("low");
  if (hi >= 0.5) prediction_set.push("high");
  if (prediction_set.length === 0) prediction_set.push("low");

  let decision: Decision;
  let rationale: string;

  if (prediction_set.length === 2 || width > 0.45) {
    decision = "hold";
    rationale =
      "Conformal set is ambiguous or interval is wide — do not auto-dispatch; gather more signal.";
  } else if (prediction_set[0] === "high" || s >= 0.55) {
    decision = "escalate";
    rationale =
      "Risk leans high inside the conformal interval — human review before commit.";
  } else {
    decision = "commit";
    rationale =
      "Risk leans low with a narrow enough interval for a careful automated commit under policy.";
  }

  // Criticality 3 never auto-commits
  if (a.criticality === 3 && decision === "commit") {
    decision = "escalate";
    rationale = "Criticality-3 assets never auto-commit even when risk looks low.";
  }

  return {
    id: a.id,
    risk_score: Math.round(s * 1000) / 1000,
    conformal_interval: [Math.round(lo * 1000) / 1000, Math.round(hi * 1000) / 1000],
    prediction_set,
    decision,
    rationale,
    alpha,
  };
}

export function backtest(
  calibration: AssetFeatures[],
  holdout: AssetFeatures[],
  alpha: number,
): { results: ScoreResult[]; summary: BacktestSummary } {
  const qHat = calibrateQuantile(calibration, alpha);
  const results = holdout.map((a) => scoreAsset(a, qHat, alpha));

  let covered = 0;
  for (let i = 0; i < holdout.length; i++) {
    const a = holdout[i]!;
    const r = results[i]!;
    const y = a.failed ? 1 : 0;
    if (y >= r.conformal_interval[0] && y <= r.conformal_interval[1]) covered++;
  }

  const decisions: Record<Decision, number> = { commit: 0, escalate: 0, hold: 0 };
  for (const r of results) decisions[r.decision]++;

  return {
    results,
    summary: {
      n: holdout.length,
      empirical_coverage: holdout.length ? covered / holdout.length : 0,
      target_coverage: 1 - alpha,
      decisions,
    },
  };
}
