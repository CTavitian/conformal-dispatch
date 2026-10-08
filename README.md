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

## Current results

On the 40 made-up assets in `fixtures/assets.json`, at alpha 0.1 (target coverage 0.9):

```text
coverage=0.775 target=0.9 n=40
decisions: hold 40, commit 0, escalate 0
```

Every asset is held, and the intervals are close to the full 0 to 1 range, so the tool is cautious but not yet useful. The test only asks for coverage of at least 0.7, which is why it passes. My guess, not yet tested, is that the scoring model is too simple and 40 assets is too few to calibrate on. Next step: a larger sample and a better model, then check whether coverage moves toward the target.

## Non-goals

- Not a full PdM platform or CMMS integration
- Does not claim production accuracy on real fleets

## Licence

MIT
