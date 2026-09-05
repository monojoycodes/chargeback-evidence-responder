# Chargeback Evidence Responder

This project generates synthetic chargeback evidence data for experimentation and model evaluation.

## Requirements

- Python 3.11+
- uv

## Setup with uv

From the project root:

```bash
uv sync --python 3.11
source .venv/bin/activate
uv run python data/generate_Data.py
```

On Windows PowerShell:

```powershell
uv sync --python 3.11
.\.venv\Scripts\Activate.ps1
uv run python data/generate_Data.py
```

If you want to install only the declared deps without syncing the project metadata, this also works:

```bash
uv venv --python 3.11
uv pip install -r requirements.txt
```

## Launching the Interactive System

Run the unified dashboard server:

```bash
uv run python run_dashboard.py
```

Then navigate to `http://127.0.0.1:8000` to interact with:
- **Overview**: Executive summary and 3-step decision pipeline.
- **Dispute Dashboard**: Real-time filtering and risk scoring across 1,500 disputes.
- **Test System Flow**: Step-by-step evaluation wizard with dynamic held-out test scenarios, System A risk gating, and 3-page bank-ready PDF compilation.
- **About**: Architectural breakdown of financial gating and agentic document auditing.

## Project structure

- `data/generate_Data.py` — synthetic chargeback case and evidence generator
- `system_a/` — model training and evaluation area
- `system_b/` — additional responder logic (if used)
- `tests/` — validation or regression tests
- `outputs/` — generated artifacts and experiments

## Notes

- The repo currently uses a lightweight Python stack only: `numpy` and `pandas`.
- `pyproject.toml` and `requirements.txt` are both included so the project works with uv and standard Python installs.

