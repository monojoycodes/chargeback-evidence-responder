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

## Running the generator

Generate the synthetic dataset:

```bash
uv run python data/generate_Data.py
```

This writes CSV outputs into the project workspace, including the generated case/evidence datasets used by the responder systems.

## Project structure

- `data/generate_Data.py` — synthetic chargeback case and evidence generator
- `system_a/` — model training and evaluation area
- `system_b/` — additional responder logic (if used)
- `tests/` — validation or regression tests
- `outputs/` — generated artifacts and experiments

## Notes

- The repo currently uses a lightweight Python stack only: `numpy` and `pandas`.
- `pyproject.toml` and `requirements.txt` are both included so the project works with uv and standard Python installs.

