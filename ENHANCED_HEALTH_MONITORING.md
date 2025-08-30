# Enhanced Health Monitoring System

## Overview

The Reality Checker WhatsApp Bot now includes comprehensive health monitoring for all external APIs and internal services. This system provides real-time status information and helps identify issues before they impact users.

## Monitored Services

### Critical Services

- **OpenAI API**: AI analysis functionality
- **Twilio API**: WhatsApp messaging
- **Database**: Data persistence and connection pool
- **Redis**: Caching and rate limiting

### Optional Services

- **ngrok**: Development tunneling (not required in production)

## Health Check Endpoints

### Basic Health Check

```http
GET /health
```
Simple endpoint for load balancers and basic monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-29T10:30:00Z",
  "service": "reality-checker-whatsapp-bot",
  "version": "1.0.0"
}
```

### Detailed Health Check

```http
GET /health/detailed
```
Comprehensive health check for all services with performance metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-29T10:30:00Z",
  "service": "reality-checker-whatsapp-bot",
  "version": "1.0.0",
  "health_check_duration_ms": 245.67,
  "services": {
    "openai": {
      "status": "healthy",
      "message": "OpenAI API accessible",
      "response_time_ms": 89.23,
      "model": "gpt-3.5-turbo",
      "circuit_breaker": "closed"
    },
    "twilio": {
      "status": "healthy",
      "message": "Twilio API accessible",
      "response_time_ms": 156.45,
      "account_status": "active",
      "phone_number": "+1234567890",
      "circuit_breaker": "closed"
    },
    "database": {
      "status": "healthy",
      "message": "Database is accessible and functioning",
      "response_time_ms": 12.34,
      "database_type": "sqlite",
      "connection_pool": {
        "active_connections": 5,
        "total_connections": 20
      }
    },
    "redis": {
      "status": "healthy",
      "message": "Redis is accessible and functioning",
      "response_time_ms": 8.91,
      "operations_tested": ["set", "get", "delete"]
    },
    "ngrok": {
      "status": "healthy",
      "message": "ngrok tunnel is active",
      "response_time_ms": 15.67,
      "public_url": "https://abc123.ngrok.io",
      "tunnel_name": "command_line"
    }
  },
  "metrics": {
    "requests": {...},
    "services": {...}
  },
  "configuration": {
    "openai_model": "gpt-3.5-turbo",
    "max_pdf_size_mb": 10,
    "log_level": "INFO",
    "webhook_validation": true
  }
}
```

### Individual Service Health Checks

#### OpenAI Health

```http
GET /health/openai
```

#### Twilio Health

```http
GET /health/twilio
```

#### Database Health

```http
GET /health/database
```

#### Redis Health

```http
GET /health/redis
```

#### ngrok Status

```http
GET /health/ngrok
```

### External Services Health

```http
GET /health/external
```
Combined health check for all external APIs (OpenAI, Twilio, ngrok).

**Note**: This endpoint is currently under development and may not be fully functional.

### Additional Endpoints

#### Metrics

```http
GET /health/metrics
```

Application performance metrics.

#### Readiness Check

```http
GET /health/readiness
```

Kubernetes-style readiness probe.

#### Liveness Check

```http
GET /health/liveness
```

Kubernetes-style liveness probe.

#### Circuit Breakers Status

```http
GET /health/circuit-breakers
```

Status of all circuit breakers.

#### Active Alerts

```http
GET /health/alerts
```

Current system alerts and warnings.

## Health Status Values

### Status Types

- **healthy**: Service is fully operational
- **degraded**: Service is working but with issues
- **unhealthy**: Service is not working
- **not_configured**: Service is not configured (expected for optional services)
- **not_available**: Service is not available (normal for development tools in production)
- **circuit_open**: Circuit breaker is open due to failures
- **error**: Health check itself failed

### HTTP Status Codes

- **200**: Healthy or degraded (with X-Health-Status header)
- **503**: Unhealthy or service unavailable

## Circuit Breaker Protection

All external API health checks are protected by circuit breakers to prevent cascading failures:

- **Failure Threshold**: 3 consecutive failures
- **Recovery Timeout**: 30 seconds
- **Request Timeout**: 10 seconds for OpenAI, 10 seconds for Twilio

## Monitoring Integration

### Dashboard Integration

The health check data is automatically integrated into the admin dashboard:

- Real-time service status display
- Historical health trends
- Alert notifications

### Alerting

The system automatically generates alerts for:

- Service failures
- Circuit breaker activations
- Performance degradation
- Configuration issues

## Testing the Health System

Use the provided test script to verify all health endpoints:

```bash
python3 test_enhanced_health_checks.py
```

This will test all endpoints and provide a comprehensive report.

## Production Deployment

### Load Balancer Configuration

Configure your load balancer to use the basic health check:

```text
Health Check URL: /health
Expected Status: 200
Timeout: 5 seconds
Interval: 30 seconds
```

### Kubernetes Configuration

```yaml
livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/readiness
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Monitoring Setup

Set up monitoring alerts for:

- `/health/detailed` returning non-200 status
- Individual service endpoints showing unhealthy status
- Circuit breakers in open state
- High response times (>5 seconds for detailed health check)

## Troubleshooting

### Common Issues

#### OpenAI Health Check Fails

- Verify `OPENAI_API_KEY` is set and valid
- Check API quota and billing status
- Review circuit breaker status

#### Twilio Health Check Fails

- Verify Twilio credentials are correct
- Check account status and balance
- Ensure phone number is properly configured

#### Database Health Check Fails

- Check database connection string
- Verify database server is running
- Review connection pool settings

#### Redis Health Check Fails

- Ensure Redis server is running
- Check Redis connection settings
- Verify Redis is accessible from the application

#### ngrok Shows Not Available

- This is normal in production environments
- For development, ensure ngrok is running: `ngrok http 8000`

### Performance Issues

If health checks are slow:

- Check network connectivity to external services
- Review circuit breaker configurations
- Monitor database connection pool utilization
- Check Redis performance metrics

## Security Considerations

- Health endpoints don't expose sensitive information
- API keys and tokens are not included in responses
- Circuit breaker status helps prevent information leakage during attacks
- Rate limiting applies to health endpoints to prevent abuse
- Phone numbers in responses are masked for security (showing configured number only)
- Detailed error messages are truncated to prevent information disclosure

## Future Enhancements

Planned improvements:

- Historical health data storage
- Predictive health analytics
- Custom health check plugins
- Integration with external monitoring systems (Prometheus, Grafana)
- Automated recovery actions