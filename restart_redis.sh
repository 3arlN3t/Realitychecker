#!/usr/bin/env bash
set -euo pipefail
exec bash scripts/ops/restart_redis.sh "$@"

