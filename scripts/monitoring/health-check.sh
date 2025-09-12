#!/bin/bash

# Reality Checker Health Check Script
# Monitors application health and performance metrics

set -euo pipefail

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"
ALERT_THRESHOLD="${ALERT_THRESHOLD:-3.0}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}[ERROR]${NC} $1"; }

# Check API health
check_api_health() {
    local start_time=$(date +%s.%N)
    local response
    local http_code
    
    response=$(curl -s -w "%{http_code}" "$API_URL/health" 2>/dev/null || echo "000")
    http_code="${response: -3}"
    local body="${response%???}"
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    if [ "$http_code" = "200" ]; then
        if echo "$body" | grep -q '"status":"healthy"'; then
            log_info "API Health: OK (${duration}s)"
            return 0
        else
            log_warn "API Health: Degraded - $body"
            return 1
        fi
    else
        log_error "API Health: Failed (HTTP $http_code)"
        return 1
    fi
}

# Check Redis connectivity
check_redis_health() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
            log_info "Redis Health: OK"
            return 0
        else
            log_error "Redis Health: Failed"
            return 1
        fi
    else
        log_warn "Redis Health: Cannot check (redis-cli not available)"
        return 0
    fi
}

# Check webhook performance
check_webhook_performance() {
    local start_time=$(date +%s.%N)
    local response
    
    response=$(curl -s -X POST "$API_URL/webhook/whatsapp" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "From=test&Body=health-check" 2>/dev/null || echo "")
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    if (( $(echo "$duration > $ALERT_THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
        log_warn "Webhook Performance: Slow (${duration}s > ${ALERT_THRESHOLD}s)"
        return 1
    else
        log_info "Webhook Performance: OK (${duration}s)"
        return 0
    fi
}

# Main health check
main() {
    log_info "Starting health check..."
    
    local api_ok=0
    local redis_ok=0
    local webhook_ok=0
    
    check_api_health && api_ok=1
    check_redis_health && redis_ok=1
    check_webhook_performance && webhook_ok=1
    
    local total_score=$((api_ok + redis_ok + webhook_ok))
    
    if [ $total_score -eq 3 ]; then
        log_info "Overall Health: HEALTHY"
        exit 0
    elif [ $total_score -eq 2 ]; then
        log_warn "Overall Health: DEGRADED"
        exit 1
    else
        log_error "Overall Health: UNHEALTHY"
        exit 2
    fi
}

main "$@"