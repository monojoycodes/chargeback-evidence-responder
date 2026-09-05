"""
LAUNCH SCRIPT FOR AI CHARGEBACK EVIDENCE RESPONDER DASHBOARD

Starts the unified FastAPI server on http://127.0.0.1:8000 serving:
  - The React frontend dashboard UI
  - REST API (/api/*) for System A scoring & System B 4-page PDF compiler
"""

import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    url = "http://127.0.0.1:8000"
    print("=" * 65)
    print("  AI CHARGEBACK EVIDENCE RESPONDER — DASHBOARD & DEMO ENGINE")
    print("=" * 65)
    print(f"\n  Serving on: {url}")
    print("  Press CTRL+C to stop the server.\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run("dashboard.api.main:app", host="127.0.0.1", port=8000, reload=False)
