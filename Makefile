.PHONY: help start start-dashboard deploy deploy-dev deploy-k8s deploy-prod prod \
	health-check monitor redis-diagnostics db-init db-check db-migrate \
	db-backup db-list-backups db-restore db-cleanup db-stats validate-integration

# Tools
PY ?= python3
SHELL := /bin/bash

help:
	@echo "Reality Checker - Common Commands"
	@echo "=================================="
	@echo "make start                # Start backend (dev reload)"
	@echo "make start-dashboard      # Start backend with integrated dashboard"
	@echo "make deploy               # Deploy (docker by default)"
	@echo "make deploy-dev           # Deploy with docker to development"
	@echo "make deploy-k8s           # Deploy to Kubernetes"
	@echo "make deploy-prod          # Deploy in production mode"
	@echo "make prod                 # Start production server locally"
	@echo "make health-check         # Run health check script"
	@echo "make monitor              # Tail/monitor basic metrics"
	@echo "make redis-diagnostics    # Run Redis diagnostics"
	@echo "make db-init              # Initialize database"
	@echo "make db-check             # Check DB status/version"
	@echo "make db-migrate           # Run database migrations"
	@echo "make db-backup            # Create database backup"
	@echo "make db-list-backups      # List database backups"
	@echo "make db-restore name=...  # Restore database backup by name"
	@echo "make db-cleanup           # Run data retention cleanup"
	@echo "make db-stats             # Show database stats"
	@echo "make validate-integration # Validate dashboard integration docs/files"
	@echo ""
	@echo "See also: Makefile.load_testing (performance/load tests)"

# --- App start/deploy ---
start:
	@echo "🚀 Starting dev environment (auto-opens browser)…"
	bash start.sh

start-dashboard:
	bash start_unified_dashboard.sh

deploy:
	bash deploy.sh docker production

deploy-dev:
	bash deploy.sh docker development

deploy-k8s:
	bash deploy.sh k8s production

deploy-prod:
	bash deploy.sh production production

prod:
	bash prod.sh

# --- Monitoring / health ---
health-check:
	bash health-check.sh

monitor:
	bash monitor.sh

redis-diagnostics:
	$(PY) redis_diagnostics.py

# --- Database ---
db-init:
	$(PY) manage_db.py init

db-check:
	$(PY) manage_db.py check

db-migrate:
	$(PY) manage_db.py migrate

db-backup:
	$(PY) manage_db.py backup

db-list-backups:
	$(PY) manage_db.py list-backups

db-restore:
	@if [ -z "$(name)" ]; then \
		echo "Usage: make db-restore name=<backup_name>"; exit 1; \
	fi
	$(PY) manage_db.py restore $(name)

db-cleanup:
	$(PY) manage_db.py cleanup

db-stats:
	$(PY) manage_db.py stats

# --- Integration docs/tools ---
validate-integration:
	$(PY) validate_integration.py
