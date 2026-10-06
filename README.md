# conformal-dispatch

Score field-asset failure risk from simple telemetry features, wrap the score with split conformal prediction, and emit a dispatch decision: `commit`, `escalate`, or `hold`.

## Why

A point estimate of risk is not enough for regulated dispatch. Conformal intervals make uncertainty explicit. When the prediction set is ambiguous, the system abstains instead of bluffing.

## Honest limits

- Fixtures are synthetic (documented Weibull-ish wear features). Not a trained plant model.
- Empirical coverage on a small holdout will wobble. Tests use a loose band, not a fake 98% claim.
- Criticality-3 assets never auto-commit, even when the score looks calm.

## TypeScript demo

```bash
npm install
npm test
npm run score -- --fixtures fixtures/assets.json
```

## Python core

```bash
cd python
uv sync --extra dev   # or: pip install -e ".[dev]"
uv run pytest
uv run conformal-dispatch score --fixtures ../fixtures/assets.json --alpha 0.1
```

## Decision rule (summary)

| Signal | Decision |
| --- | --- |
| Narrow interval, low risk, criticality &lt; 3 | commit |
| High risk lean | escalate |
| Ambiguous set or wide interval | hold |

## Non-goals

- Not a full PdM platform or CMMS integration
- Does not claim production accuracy on real fleets

## Licence

MIT
