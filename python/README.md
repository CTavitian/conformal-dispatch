# conformal-dispatch (Python)

Split conformal wrapper around a logistic risk score. Same fixtures as the TypeScript demo.

```bash
cd python
uv sync --extra dev
uv run pytest
uv run conformal-dispatch score --fixtures ../fixtures/assets.json --alpha 0.1
```
