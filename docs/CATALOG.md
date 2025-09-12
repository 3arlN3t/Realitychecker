# Catalog

## Active
- `app/api/webhook_original.py` (shim to legacy)
- `app/database/models_2_0.py` (shim to experimental)
- `app/main_improvements.py` (shim to examples)

## Legacy
- `app/api/legacy/webhook_original.py`

## Experimental
- `app/database/experimental/models_v2.py`

## Examples
- `app/_examples/main_structure.py`

## Notes
- Backward-compatible shims maintain old import paths.
- Moves used `git mv` to preserve history.

### Migration Map

| Old Path                          | New Path                                 | Status        |
|-----------------------------------|------------------------------------------|---------------|
| `app/api/webhook_original.py`     | `app/api/legacy/webhook_original.py`     | Shim in place |
| `app/database/models_2_0.py`      | `app/database/experimental/models_v2.py` | Shim in place |
| `app/main_improvements.py`        | `app/_examples/main_structure.py`        | Shim in place |

