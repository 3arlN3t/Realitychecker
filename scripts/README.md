Scripts overview and structure

Run common tasks via Make targets to keep commands short and consistent:
- List commands: `make help`
- Start backend (dev): `make start`
- Start with integrated dashboard: `make start-dashboard`
- Deploy (docker/dev/k8s/prod): `make deploy|deploy-dev|deploy-k8s|deploy-prod`
- Health and monitoring: `make health-check`, `make monitor`, `make redis-diagnostics`
- Database: `make db-init|db-check|db-migrate|db-backup|db-list-backups|db-restore name=<backup>|db-cleanup|db-stats`
- Validate dashboard integration docs: `make validate-integration`

Structure:
- scripts/dev: local dev helpers (start, dashboard, build)
- scripts/ops: deployment/ops (deploy, prod, restart_redis, whatsapp-setup)
- scripts/monitoring: health/monitoring utilities (health-check, monitor, redis/health python)
- scripts/db: database management (manage_db, simple_db_setup)
- scripts/tools: misc tools and debugging (validate_integration, debug_*, populate_sample_data, setup/verify whatsapp)

Backwards compatibility:
- Root-level files with the old names remain as thin wrappers that forward to the new locations, so existing commands keep working (e.g., `bash deploy.sh`, `python manage_db.py`).

Recommended usage via Makefile:
- List commands: `make help`
- Start backend (dev): `make start`
- Start with integrated dashboard: `make start-dashboard`
- Deploy (docker/dev/k8s/prod): `make deploy|deploy-dev|deploy-k8s|deploy-prod`
- Health and monitoring: `make health-check`, `make monitor`, `make redis-diagnostics`
- Database: `make db-init|db-check|db-migrate|db-backup|db-list-backups|db-restore name=<backup>|db-cleanup|db-stats`
- Validate dashboard integration docs: `make validate-integration`
