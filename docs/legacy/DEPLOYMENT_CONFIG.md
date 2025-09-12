# Deployment Configuration Guide

This document describes the enhanced deployment configuration for the Reality Checker WhatsApp Bot with Redis performance optimizations and monitoring capabilities.

## Overview

The deployment configuration has been optimized to address the following requirements:
- Redis connectivity reliability (Requirements 1.1, 1.4)
- Connection pool management (Requirements 5.1, 5.2)
- Performance monitoring and alerting
- Health checks and automated recovery

## Configuration Files

### Docker Compose Configuration

#### `docker-compose.yml`
- **Redis Service**: Optimized with custom configuration file and performance tuning
- **Application Service**: Enhanced with Redis connection pool settings and performance parameters
- **Environment Variables**: Added comprehensive performance tuning parameters

#### `docker-compose.override.yml`
- **Development Overrides**: Redis configuration optimized for development
- **Debug Settings**: Enhanced logging and monitoring for development

#### `redis.conf`
- **Memory Management**: Optimized for 256MB with LRU eviction policy
- **Connection Settings**: Tuned for high throughput and low latency
- **Performance Optimizations**: Hash tables, lists, and sets optimized for typical workloads

### Application Configuration

#### `app/config.py`
Enhanced with three new configuration classes:

1. **RedisConfig**: Connection pooling, circuit breaker, and retry settings
2. **PerformanceConfig**: Webhook timeouts, task queue settings, monitoring thresholds
3. **DatabaseConfig**: Connection pool optimization for database operations

#### `.env.example`
Added comprehensive environment variables for:
- Redis connection pool settings
- Performance tuning parameters
- Task queue configuration
- Monitoring and alerting thresholds

### Kubernetes Configuration

#### `k8s/performance-configmap.yaml`
New ConfigMap containing all performance-related environment variables for Kubernetes deployments.

#### `k8s/deployment.yaml`
- **Resource Limits**: Increased memory and CPU limits for better performance
- **ConfigMap References**: Added performance configuration

## Deployment Scripts

### `deploy.sh`
Comprehensive deployment script supporting multiple deployment modes:

#### Features:
- **Multi-mode Support**: Docker, Kubernetes, and production deployments
- **Health Checks**: Automated health verification with configurable timeouts
- **Environment Validation**: Checks for required environment variables
- **Resource Monitoring**: Displays resource usage after deployment
- **Cleanup Handling**: Graceful shutdown and cleanup on interruption

#### Usage:
```bash
# Docker deployment (development)
./deploy.sh docker development

# Kubernetes deployment (production)
./deploy.sh k8s production

# Direct production deployment
./deploy.sh production production
```

#### Environment Variables:
- `SKIP_HEALTH_CHECK`: Skip health checks (default: false)
- `TIMEOUT`: Deployment timeout in seconds (default: 300)

### `health-check.sh`
Standalone health check script for monitoring:

#### Features:
- **API Health**: Checks application health endpoint with response time measurement
- **Redis Health**: Verifies Redis connectivity
- **Webhook Performance**: Tests webhook response times against thresholds
- **Exit Codes**: Returns appropriate exit codes for monitoring systems

#### Usage:
```bash
# Single health check
./health-check.sh

# Configure custom settings
API_URL=http://localhost:8000 ALERT_THRESHOLD=2.0 ./health-check.sh
```

### `monitor.sh`
Continuous monitoring script with dashboard:

#### Features:
- **Real-time Dashboard**: Live monitoring display with system metrics
- **Alert System**: Configurable alerting via email or logging
- **Multi-service Monitoring**: API, Redis, and Docker container health
- **Performance Tracking**: Response time monitoring with threshold alerts

#### Usage:
```bash
# Start continuous monitoring
./monitor.sh

# Single check mode
./monitor.sh check

# Custom configuration
MONITOR_INTERVAL=30 ALERT_EMAIL=admin@example.com ./monitor.sh
```

### `prod.sh`
Enhanced production startup script:

#### Features:
- **Performance Optimizations**: All performance environment variables set
- **Gunicorn Support**: Uses Gunicorn when available for better production performance
- **Worker Configuration**: Optimized worker count and request handling
- **Resource Management**: Connection pooling and timeout configurations

## Environment Variables Reference

### Redis Configuration
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20                    # Connection pool size
REDIS_MAX_CONNECTIONS=50              # Maximum connections
REDIS_CONNECTION_TIMEOUT=5.0          # Connection timeout (seconds)
REDIS_SOCKET_TIMEOUT=5.0              # Socket timeout (seconds)
REDIS_RETRY_ATTEMPTS=3                # Retry attempts for failed operations
REDIS_RETRY_BACKOFF=1.0               # Backoff multiplier for retries
REDIS_HEALTH_CHECK_INTERVAL=30        # Health check interval (seconds)
REDIS_CIRCUIT_BREAKER_THRESHOLD=5     # Circuit breaker failure threshold
REDIS_CIRCUIT_BREAKER_TIMEOUT=60      # Circuit breaker timeout (seconds)
```

### Performance Tuning
```bash
WEBHOOK_TIMEOUT=2.0                   # Maximum webhook processing time
WEBHOOK_ACKNOWLEDGMENT_TIMEOUT=0.5    # Webhook acknowledgment timeout
TASK_QUEUE_MAX_SIZE=1000              # Maximum task queue size
TASK_QUEUE_WORKER_COUNT=5             # Number of background workers
TASK_QUEUE_BATCH_SIZE=10              # Tasks processed per batch
TASK_PROCESSING_TIMEOUT=30            # Task processing timeout
TASK_RETRY_ATTEMPTS=3                 # Task retry attempts
TASK_RETRY_BACKOFF=2.0                # Task retry backoff multiplier
```

### Monitoring and Alerting
```bash
PERFORMANCE_MONITORING_ENABLED=true   # Enable performance monitoring
PERFORMANCE_ALERT_THRESHOLD_WEBHOOK=1.0  # Webhook warning threshold (seconds)
PERFORMANCE_ALERT_THRESHOLD_CRITICAL=3.0 # Critical alert threshold (seconds)
```

### Database Configuration
```bash
DB_POOL_SIZE=20                       # Database connection pool size
DB_MAX_OVERFLOW=30                    # Maximum overflow connections
DB_POOL_TIMEOUT=30                    # Pool checkout timeout
DB_POOL_RECYCLE=3600                  # Connection recycle time (seconds)
```

## Deployment Modes

### Development Mode
```bash
# Using Docker Compose with development overrides
./deploy.sh docker development

# Features:
# - Hot reload enabled
# - Debug logging
# - Development tools (pgAdmin, Redis Commander)
# - Reduced resource limits
```

### Staging Mode
```bash
# Using Docker Compose with production settings
./deploy.sh docker staging

# Features:
# - Production-like configuration
# - Performance monitoring enabled
# - Health checks enabled
# - Resource monitoring
```

### Production Mode
```bash
# Direct production deployment
./deploy.sh production production

# Or Kubernetes deployment
./deploy.sh k8s production

# Features:
# - Optimized resource allocation
# - Gunicorn with multiple workers
# - Comprehensive health checks
# - Performance monitoring and alerting
```

## Health Check Endpoints

### Application Health
- **URL**: `/health`
- **Method**: GET
- **Response**: JSON with service status and metrics
- **Timeout**: 5 seconds

### Performance Metrics
- **URL**: `/metrics` (if implemented)
- **Method**: GET
- **Response**: Prometheus-compatible metrics
- **Includes**: Response times, error rates, queue depths

## Monitoring Integration

### Prometheus Integration
The configuration supports Prometheus monitoring through:
- Custom metrics in application code
- Redis metrics via redis_exporter
- System metrics via node_exporter

### Grafana Dashboards
Recommended dashboard panels:
- API response times (p50, p95, p99)
- Redis connection pool utilization
- Task queue depth and processing times
- Error rates and types
- System resource utilization

### Alerting Rules
Suggested alert conditions:
- Webhook response time > 1 second (warning)
- Webhook response time > 3 seconds (critical)
- Redis connection failures > 5%
- Task queue depth > 500 items
- Error rate > 5%

## Troubleshooting

### Common Issues

#### Redis Connection Failures
1. Check Redis service status: `docker-compose ps redis`
2. Verify Redis configuration: `docker-compose logs redis`
3. Test connection: `redis-cli -u $REDIS_URL ping`

#### Slow Webhook Response Times
1. Check performance metrics: `curl http://localhost:8000/health`
2. Monitor task queue: Check application logs for queue depth
3. Verify resource usage: `docker stats` or `kubectl top pods`

#### Health Check Failures
1. Run manual health check: `./health-check.sh`
2. Check application logs: `docker-compose logs app`
3. Verify environment variables: Check `.env` file

### Log Files
- **Application**: `docker-compose logs app`
- **Redis**: `docker-compose logs redis`
- **Health Checks**: `monitor.log`
- **Deployment**: Console output from `deploy.sh`

## Security Considerations

### Production Deployment
- Change default passwords in `.env`
- Use secrets management for sensitive data
- Enable TLS/SSL for external connections
- Implement proper firewall rules
- Regular security updates for base images

### Network Security
- Use internal networks for service communication
- Implement proper ingress controls
- Enable Redis AUTH if exposed externally
- Use encrypted connections where possible

## Performance Optimization

### Redis Optimization
- Memory allocation based on usage patterns
- Connection pooling to reduce overhead
- Circuit breaker to prevent cascade failures
- Health monitoring for proactive maintenance

### Application Optimization
- Asynchronous processing for webhook handling
- Connection pool management for database
- Task queue for background processing
- Performance monitoring and alerting

### Infrastructure Optimization
- Resource limits based on actual usage
- Horizontal scaling for high load
- Load balancing for multiple instances
- Caching strategies for frequently accessed data