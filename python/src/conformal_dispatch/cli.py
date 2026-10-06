"""CLI: conformal-dispatch score --fixtures <assets.json> [--alpha 0.1]."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import backtest, calibrate_quantile


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="conformal-dispatch")
    sub = parser.add_subparsers(dest="cmd", required=True)

    score_p = sub.add_parser("score", help="Score holdout assets with conformal intervals")
    score_p.add_argument("--fixtures", required=True, help="assets.json with calibration+holdout")
    score_p.add_argument("--alpha", type=float, default=0.1)
    score_p.add_argument("--out", default="reports/dispatch-latest.json")

    args = parser.parse_args(argv)
    if args.cmd != "score":
        parser.error("unknown command")

    data = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
    calibration = data["calibration"]
    holdout = data["holdout"]
    alpha = args.alpha

    results, summary = backtest(calibration, holdout, alpha)
    q_hat = calibrate_quantile(calibration, alpha)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "alpha": alpha,
        "q_hat": q_hat,
        "summary": summary,
        "results": [
            {**r, "conformal_interval": list(r["conformal_interval"])} for r in results
        ],
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("id\tdecision\trisk\tinterval\tset")
    for r in results:
        lo, hi = r["conformal_interval"]
        print(
            f"{r['id']}\t{r['decision']}\t{r['risk_score']}\t"
            f"[{lo},{hi}]\t{'|'.join(r['prediction_set'])}"
        )
    print(
        f"coverage={summary['empirical_coverage']:.3f} "
        f"target={summary['target_coverage']} n={summary['n']}"
    )
    print(f"Report: {out.resolve()}")


if __name__ == "__main__":
    main()
