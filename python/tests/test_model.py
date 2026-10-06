"""Decision rules, criticality gate, and honest coverage band on fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from conformal_dispatch import backtest, calibrate_quantile, raw_risk, score_asset
from conformal_dispatch.types import AssetFeatures

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "assets.json"


def _load():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def test_raw_risk_bounds_and_monotone():
    low: AssetFeatures = {
        "id": "a",
        "runtime_hours": 800,
        "alarm_rate_7d": 0.2,
        "days_since_pm": 20,
        "criticality": 1,
    }
    high: AssetFeatures = {
        "id": "b",
        "runtime_hours": 11000,
        "alarm_rate_7d": 7,
        "days_since_pm": 350,
        "criticality": 3,
    }
    assert 0 < raw_risk(low) < 1
    assert raw_risk(high) > raw_risk(low)


def test_holdout_coverage_honest_band():
    data = _load()
    alpha = 0.1
    _, summary = backtest(data["calibration"], data["holdout"], alpha)
    # Finite-sample conformal on synthetic fixtures — loose band, not a fake 98%
    assert summary["empirical_coverage"] >= 0.7
    assert abs(summary["target_coverage"] - 0.9) < 1e-9


def test_criticality_3_never_commits():
    a: AssetFeatures = {
        "id": "c3",
        "runtime_hours": 500,
        "alarm_rate_7d": 0.1,
        "days_since_pm": 10,
        "criticality": 3,
        "failed": False,
    }
    r = score_asset(a, q_hat=0.05, alpha=0.1)
    assert r["decision"] != "commit"


def test_wide_interval_holds():
    a: AssetFeatures = {
        "id": "w",
        "runtime_hours": 5000,
        "alarm_rate_7d": 3,
        "days_since_pm": 180,
        "criticality": 2,
    }
    r = score_asset(a, q_hat=0.6, alpha=0.1)
    assert r["decision"] == "hold"
    assert len(r["prediction_set"]) >= 1


def test_ambiguous_set_holds():
    # Mid-range score + modest q so both low and high land in the set
    a: AssetFeatures = {
        "id": "amb",
        "runtime_hours": 5000,
        "alarm_rate_7d": 3,
        "days_since_pm": 180,
        "criticality": 2,
    }
    s = raw_risk(a)
    # Force interval that straddles 0.5 with width <= 0.45 still possible;
    # q_hat large enough that lo < 0.5 <= hi
    q = max(0.3, abs(s - 0.5) + 0.05)
    r = score_asset(a, q_hat=q, alpha=0.1)
    if len(r["prediction_set"]) == 2 or (r["conformal_interval"][1] - r["conformal_interval"][0]) > 0.45:
        assert r["decision"] == "hold"


def test_calibrate_quantile_positive():
    data = _load()
    assert calibrate_quantile(data["calibration"], 0.1) > 0
