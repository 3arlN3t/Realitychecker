#!/bin/bash

# Reality Checker WhatsApp Bot - Enhanced Deployment Script
# This script deploys the application with health checks and monitoring

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
DEPLOYMENT_MODE="${1:-docker}"  # docker, k8s, or production
ENVIRONMENT="${2:-production}"  # development, staging, production
SKIP_HEALTH_CHECK="${SKIP_HEALTH_CHECK:-false}"
TIMEOUT="${TIMEOUT:-300}"  # 5 minutes timeout

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Usage: $0 [DEPLOYMENT_MODE] [ENVIRONMENT]

DEPLOYMENT_MODE:
  docker      - Deploy using Docker Compose (default)
  k8s         - Deploy to Kubernetes cluster
  production  - Deploy in production mode with optimizations

ENVIRONMENT:
  development - Development environment
  staging     - Staging environment  
  production  - Production environment (default)

Environment Variables:
  SKIP_HEALTH_CHECK - Skip health checks (default: false)
  TIMEOUT          - Deployment timeout in seconds (default: 300)

Examples:
  $0 docker development
  $0 k8s production
  $0 production production

EOF
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    case "$DEPLOYMENT_MODE" in
        docker)
            if ! command -v docker &> /dev/null; then
                log_error "Docker is not installed"
                exit 1
            fi
            if ! command -v docker-compose &> /dev/null; then
                log_error "Docker Compose is not installed"
                exit 1
            fi
            ;;
        k8s)
            if ! command -v kubectl &> /dev/null; then
                log_error "kubectl is not installed"
                exit 1
            fi
            if ! kubectl cluster-info &> /dev/null; then
                log_error "Cannot connect to Kubernetes cluster"
                exit 1
            fi
            ;;
        production)
            if ! command -v python3 &> /dev/null; then
                log_error "Python 3 is not installed"
                exit 1
            fi
            ;;
    esac
    
    log_success "Prerequisites validated"
}

# Check environment configuration
check_environment() {
    log_info "Checking environment configuration..."
    
    if [ ! -f ".env" ] && [ "$ENVIRONMENT" != "development" ]; then
        log_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    # Load environment variables
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Check required variables for production
    if [ "$ENVIRONMENT" = "production" ]; then
        required_vars=(
            "OPENAI_API_KEY"
            "TWILIO_ACCOUNT_SID"
            "TWILIO_AUTH_TOKEN"
            "TWILIO_PHONE_NUMBER"
        )
        
        for var in "${required_vars[@]}"; do
            if [ -z "${!var:-}" ]; then
                log_error "Required environment variable $var is not set"
                exit 1
            fi
        done
    fi
    
    log_success "Environment configuration validated"
}

# Wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local health_url="$2"
    local timeout="$3"
    
    log_info "Waiting for $service_name to be ready..."
    
    local count=0
    local max_attempts=$((timeout / 5))
    
    while [ $count -lt $max_attempts ]; do
        if curl -sf "$health_url" > /dev/null 2>&1; then
            log_success "$service_name is ready"
            return 0
        fi
        
        sleep 5
        count=$((count + 1))
        
        if [ $((count % 6)) -eq 0 ]; then
            log_info "Still waiting for $service_name... ($((count * 5))s elapsed)"
        fi
    done
    
    log_error "$service_name failed to become ready within ${timeout}s"
    return 1
}

# Perform health checks
perform_health_checks() {
    if [ "$SKIP_HEALTH_CHECK" = "true" ]; then
        log_warning "Skipping health checks"
        return 0
    fi
    
    log_info "Performing health checks..."
    
    local base_url
    case "$DEPLOYMENT_MODE" in
        docker)
            base_url="http://localhost:8000"
            ;;
        k8s)
            # Get service URL from kubectl
            base_url=$(kubectl get service reality-checker-service -n reality-checker -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "http://localhost:8000")
            if [ "$base_url" = "http://localhost:8000" ]; then
                log_warning "Could not get LoadBalancer IP, using port-forward for health check"
                kubectl port-forward service/reality-checker-service 8000:80 -n reality-checker &
                local port_forward_pid=$!
                sleep 5
            fi
            ;;
        production)
            base_url="http://localhost:8000"
            ;;
    esac
    
    # Wait for main service
    if ! wait_for_service "Reality Checker API" "$base_url/health" "$TIMEOUT"; then
        return 1
    fi
    
    # Additional health checks
    local health_response
    health_response=$(curl -s "$base_url/health" || echo "")
    
    if echo "$health_response" | grep -q '"status":"healthy"'; then
        log_success "Health check passed - all services are healthy"
    else
        log_warning "Health check returned unexpected response: $health_response"
    fi
    
    # Clean up port-forward if used
    if [ -n "${port_forward_pid:-}" ]; then
        kill $port_forward_pid 2>/dev/null || true
    fi
    
    return 0
}

# Deploy with Docker Compose
deploy_docker() {
    log_info "Deploying with Docker Compose..."
    
    # Build and start services
    if [ "$ENVIRONMENT" = "development" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build -d
    else
        docker-compose up --build -d
    fi
    
    # Wait for services to be ready
    sleep 10
    
    log_success "Docker deployment completed"
}

# Deploy to Kubernetes
deploy_k8s() {
    log_info "Deploying to Kubernetes..."
    
    # Apply configurations
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/performance-configmap.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/reality-checker -n reality-checker --timeout=${TIMEOUT}s
    
    log_success "Kubernetes deployment completed"
}

# Deploy in production mode
deploy_production() {
    log_info "Deploying in production mode..."
    
    # Install/update dependencies
    pip install -r requirements.txt
    
    # Run database migrations if needed
    if [ -f "alembic.ini" ]; then
        log_info "Running database migrations..."
        alembic upgrade head
    fi
    
    # Start the application with optimized settings
    export DEVELOPMENT_MODE=false
    export USE_MOCK_TWILIO=false
    export WEBHOOK_VALIDATION=true
    
    # Use gunicorn for production deployment
    if command -v gunicorn &> /dev/null; then
        log_info "Starting with Gunicorn..."
        gunicorn app.main:app \
            --bind 0.0.0.0:8000 \
            --workers 4 \
            --worker-class uvicorn.workers.UvicornWorker \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --timeout 30 \
            --keep-alive 2 \
            --access-logfile - \
            --error-logfile - \
            --log-level info &
    else
        log_info "Starting with Uvicorn..."
        python3 -m uvicorn app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 4 &
    fi
    
    local app_pid=$!
    echo $app_pid > app.pid
    
    log_success "Production deployment completed (PID: $app_pid)"
}

# Monitor deployment
monitor_deployment() {
    log_info "Monitoring deployment..."
    
    # Check resource usage
    case "$DEPLOYMENT_MODE" in
        docker)
            docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10
            ;;
        k8s)
            kubectl top pods -n reality-checker 2>/dev/null || log_warning "Metrics server not available"
            ;;
        production)
            if command -v ps &> /dev/null; then
                ps aux | grep -E "(python|uvicorn|gunicorn)" | grep -v grep | head -5
            fi
            ;;
    esac
    
    # Show service URLs
    log_info "Service URLs:"
    case "$DEPLOYMENT_MODE" in
        docker)
            echo "  • API Server: http://localhost:8000"
            echo "  • Dashboard: http://localhost:3000"
            echo "  • Health Check: http://localhost:8000/health"
            ;;
        k8s)
            local ingress_ip
            ingress_ip=$(kubectl get ingress reality-checker-ingress -n reality-checker -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
            echo "  • API Server: http://$ingress_ip"
            echo "  • Health Check: http://$ingress_ip/health"
            ;;
        production)
            echo "  • API Server: http://localhost:8000"
            echo "  • Health Check: http://localhost:8000/health"
            ;;
    esac
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    
    case "$DEPLOYMENT_MODE" in
        docker)
            docker-compose down 2>/dev/null || true
            ;;
        k8s)
            # Don't automatically cleanup k8s resources
            ;;
        production)
            if [ -f "app.pid" ]; then
                local pid=$(cat app.pid)
                kill $pid 2>/dev/null || true
                rm app.pid
            fi
            ;;
    esac
}

# Main deployment function
main() {
    # Handle help
    if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
        show_help
        exit 0
    fi
    
    log_info "Starting deployment - Mode: $DEPLOYMENT_MODE, Environment: $ENVIRONMENT"
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Validate and prepare
    validate_prerequisites
    check_environment
    
    # Deploy based on mode
    case "$DEPLOYMENT_MODE" in
        docker)
            deploy_docker
            ;;
        k8s)
            deploy_k8s
            ;;
        production)
            deploy_production
            ;;
        *)
            log_error "Unknown deployment mode: $DEPLOYMENT_MODE"
            show_help
            exit 1
            ;;
    esac
    
    # Health checks and monitoring
    if perform_health_checks; then
        monitor_deployment
        log_success "Deployment completed successfully!"
    else
        log_error "Deployment failed health checks"
        exit 1
    fi
}

# Run main function
main "$@"