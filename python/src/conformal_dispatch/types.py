"""Feature and score types."""

from __future__ import annotations

from typing import Literal, TypedDict

Criticality = Literal[1, 2, 3]
Decision = Literal["commit", "escalate", "hold"]
RiskBand = Literal["low", "high"]


class AssetFeatures(TypedDict, total=False):
    id: str
    runtime_hours: float
    alarm_rate_7d: float
    days_since_pm: float
    criticality: Criticality
    failed: bool


class ScoreResult(TypedDict):
    id: str
    risk_score: float
    conformal_interval: tuple[float, float]
    prediction_set: list[RiskBand]
    decision: Decision
    rationale: str
    alpha: float


class BacktestSummary(TypedDict):
    n: int
    empirical_coverage: float
    target_coverage: float
    decisions: dict[Decision, int]
