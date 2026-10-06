"""Logistic risk + split conformal intervals + commit/escalate/hold policy."""

from __future__ import annotations

import math

from .types import AssetFeatures, BacktestSummary, Decision, RiskBand, ScoreResult


def raw_risk(a: AssetFeatures) -> float:
    hours = a["runtime_hours"] / 10000
    alarms = a["alarm_rate_7d"] / 10
    pm = a["days_since_pm"] / 365
    crit = (a["criticality"] - 1) / 2
    z = -1.2 + 1.4 * hours + 1.1 * alarms + 0.9 * pm + 0.6 * crit
    return 1.0 / (1.0 + math.exp(-z))


def calibrate_quantile(calibration: list[AssetFeatures], alpha: float) -> float:
    """Absolute residual |y - s| quantile for split conformal."""
    if not calibration:
        raise ValueError("calibration set empty")
    scores = sorted(
        abs((1 if a.get("failed") else 0) - raw_risk(a)) for a in calibration
    )
    # Finite-sample (1-alpha) quantile index used by the TypeScript twin
    q_level = math.ceil((1 - alpha) * (len(scores) + 1)) / len(scores)
    idx = min(len(scores) - 1, max(0, math.ceil(q_level * len(scores)) - 1))
    return scores[idx]


def _round3(x: float) -> float:
    return round(x * 1000) / 1000


def score_asset(a: AssetFeatures, q_hat: float, alpha: float) -> ScoreResult:
    s = raw_risk(a)
    lo = max(0.0, s - q_hat)
    hi = min(1.0, s + q_hat)
    width = hi - lo

    prediction_set: list[RiskBand] = []
    if lo < 0.5:
        prediction_set.append("low")
    if hi >= 0.5:
        prediction_set.append("high")
    if not prediction_set:
        prediction_set.append("low")

    decision: Decision
    rationale: str

    if len(prediction_set) == 2 or width > 0.45:
        decision = "hold"
        rationale = (
            "Conformal set is ambiguous or interval is wide — do not auto-dispatch; "
            "gather more signal."
        )
    elif prediction_set[0] == "high" or s >= 0.55:
        decision = "escalate"
        rationale = (
            "Risk leans high inside the conformal interval — human review before commit."
        )
    else:
        decision = "commit"
        rationale = (
            "Risk leans low with a narrow enough interval for a careful automated "
            "commit under policy."
        )

    # Criticality-3 never auto-commits, even with a calm score
    if a["criticality"] == 3 and decision == "commit":
        decision = "escalate"
        rationale = (
            "Criticality-3 assets never auto-commit even when risk looks low."
        )

    return {
        "id": a["id"],
        "risk_score": _round3(s),
        "conformal_interval": (_round3(lo), _round3(hi)),
        "prediction_set": prediction_set,
        "decision": decision,
        "rationale": rationale,
        "alpha": alpha,
    }


def backtest(
    calibration: list[AssetFeatures],
    holdout: list[AssetFeatures],
    alpha: float,
) -> tuple[list[ScoreResult], BacktestSummary]:
    q_hat = calibrate_quantile(calibration, alpha)
    results = [score_asset(a, q_hat, alpha) for a in holdout]

    covered = 0
    for a, r in zip(holdout, results):
        y = 1 if a.get("failed") else 0
        lo, hi = r["conformal_interval"]
        if lo <= y <= hi:
            covered += 1

    decisions: dict[Decision, int] = {"commit": 0, "escalate": 0, "hold": 0}
    for r in results:
        decisions[r["decision"]] += 1

    summary: BacktestSummary = {
        "n": len(holdout),
        "empirical_coverage": (covered / len(holdout)) if holdout else 0.0,
        "target_coverage": 1 - alpha,
        "decisions": decisions,
    }
    return results, summary
