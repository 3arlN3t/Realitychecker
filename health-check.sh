#!/usr/bin/env bash
set -euo pipefail
exec bash scripts/monitoring/health-check.sh "$@"

