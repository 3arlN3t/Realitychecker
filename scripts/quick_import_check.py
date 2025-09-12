import importlib
import sys
import traceback
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

modules = [
    "app.api.webhook_original",
    "app.api.legacy.webhook_original",
    "app.database.models_2_0",
    "app.database.experimental.models_v2",
    "app.main_improvements",
    "app._examples.main_structure",
    "app.services.mock_twilio_response",
]

failures = []
for m in modules:
    try:
        importlib.import_module(m)
    except Exception as e:
        failures.append((m, e, traceback.format_exc()))

if failures:
    sys.stderr.write("Import check failed for the following modules:\n")
    for m, e, tb in failures:
        sys.stderr.write(f"- {m}: {e}\n")
        sys.stderr.write(tb + "\n")
    sys.exit(1)

sys.exit(0)
