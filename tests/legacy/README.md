This directory catalogs legacy or ad-hoc tests and artifacts that are not part of the primary test suite.

What moved here:
- Root-level Python test scripts (now under `root_tests/`).
- HTML templates used only for manual test scenarios (under `templates/`).
- Sample PDF fixtures not needed by automated tests (under `artifacts/`).
- Historical `scripts_backup/` helpers and experimental tests.

Notes:
- `pytest` is configured to ignore `tests/legacy` via `--ignore=tests/legacy` in `pytest.ini`.
- Keep for reference; migrate back into `tests/` with proper fixtures/markers if needed.
