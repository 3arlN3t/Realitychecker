#!/bin/bash

# Reality Checker Continuous Monitoring Script
# Provides real-time monitoring of application performance

set -euo pipefail

# Configuration
MONITOR_INTERVAL="${MONITOR_INTERVAL:-10}"
API_URL="${API_URL:-http://localhost:8000}"
LOG_FILE="${LOG_FILE:-monitor.log}"
ALERT_EMAIL="${ALERT_EMAIL:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        INFO) echo -e "${BLUE}[$timestamp] [INFO]${NC} $message" | tee -a "$LOG_FILE" ;;
        WARN) echo -e "${YELLOW}[$timestamp] [WARN]${NC} $message" | tee -a "$LOG_FILE" ;;
        ERROR) echo -e "${RED}[$timestamp] [ERROR]${NC} $message" | tee -a "$LOG_FILE" ;;
        SUCCESS) echo -e "${GREEN}[$timestamp] [SUCCESS]${NC} $message" | tee -a "$LOG_FILE" ;;
    esac
}

# Send alert (placeholder for email/slack integration)
send_alert() {
    local message="$1"
    log ERROR "ALERT: $message"
    
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "Reality Checker Alert" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

# Get system metrics
get_system_metrics() {
    local cpu_usage memory_usage disk_usage
    
    if command -v top &> /dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 2>/dev/null || echo "0")
    else
        cpu_usage="N/A"
    fi
    
    if command -v free &> /dev/null; then
        memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' 2>/dev/null || echo "0")
    else
        memory_usage="N/A"
    fi
    
    if command -v df &> /dev/null; then
        disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1 2>/dev/null || echo "0")
    else
        disk_usage="N/A"
    fi
    
    echo "CPU: ${cpu_usage}% | Memory: ${memory_usage}% | Disk: ${disk_usage}%"
}

# Monitor API performance
monitor_api() {
    local start_time end_time duration response http_code
    
    start_time=$(date +%s.%N)
    response=$(curl -s -w "%{http_code}" "$API_URL/health" 2>/dev/null || echo "000")
    end_time=$(date +%s.%N)
    
    http_code="${response: -3}"
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    if [ "$http_code" = "200" ]; then
        if (( $(echo "$duration > 3.0" | bc -l 2>/dev/null || echo 0) )); then
            log WARN "API response slow: ${duration}s"
            send_alert "API response time exceeded 3 seconds: ${duration}s"
        else
            log INFO "API healthy: ${duration}s"
        fi
    else
        log ERROR "API unhealthy: HTTP $http_code"
        send_alert "API health check failed with HTTP $http_code"
    fi
    
    echo "$duration"
}

# Monitor Redis
monitor_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping > /dev/null 2>&1; then
            log INFO "Redis healthy"
            return 0
        else
            log ERROR "Redis connection failed"
            send_alert "Redis connection failed"
            return 1
        fi
    else
        log WARN "Redis monitoring unavailable (redis-cli not found)"
        return 0
    fi
}

# Monitor Docker containers (if applicable)
monitor_docker() {
    if command -v docker &> /dev/null && docker ps > /dev/null 2>&1; then
        local unhealthy_containers
        unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null || echo "")
        
        if [ -n "$unhealthy_containers" ]; then
            log ERROR "Unhealthy containers: $unhealthy_containers"
            send_alert "Unhealthy Docker containers detected: $unhealthy_containers"
        else
            log INFO "All Docker containers healthy"
        fi
    fi
}

# Display dashboard
display_dashboard() {
    clear
    echo "======================================"
    echo "  Reality Checker Monitoring Dashboard"
    echo "======================================"
    echo "Time: $(date)"
    echo "System: $(get_system_metrics)"
    echo "API URL: $API_URL"
    echo "Monitor Interval: ${MONITOR_INTERVAL}s"
    echo "======================================"
    echo ""
    echo "Recent Activity:"
    tail -10 "$LOG_FILE" 2>/dev/null || echo "No log entries yet"
    echo ""
    echo "Press Ctrl+C to stop monitoring"
    echo "======================================"
}

# Cleanup function
cleanup() {
    log INFO "Monitoring stopped"
    exit 0
}

# Main monitoring loop
main() {
    log INFO "Starting continuous monitoring (interval: ${MONITOR_INTERVAL}s)"
    
    trap cleanup SIGINT SIGTERM
    
    while true; do
        display_dashboard
        
        # Perform checks
        monitor_api > /dev/null
        monitor_redis > /dev/null
        monitor_docker > /dev/null
        
        sleep "$MONITOR_INTERVAL"
    done
}

# Handle command line arguments
case "${1:-monitor}" in
    monitor)
        main
        ;;
    check)
        log INFO "Performing single health check..."
        monitor_api > /dev/null
        monitor_redis > /dev/null
        monitor_docker > /dev/null
        log SUCCESS "Health check completed"
        ;;
    --help|-h)
        echo "Usage: $0 [monitor|check]"
        echo "  monitor  - Start continuous monitoring (default)"
        echo "  check    - Perform single health check"
        echo ""
        echo "Environment Variables:"
        echo "  MONITOR_INTERVAL - Check interval in seconds (default: 10)"
        echo "  API_URL         - API base URL (default: http://localhost:8000)"
        echo "  LOG_FILE        - Log file path (default: monitor.log)"
        echo "  ALERT_EMAIL     - Email for alerts (optional)"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac