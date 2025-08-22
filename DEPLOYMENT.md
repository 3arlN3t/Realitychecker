# Production Deployment Guide

This guide covers deploying the Reality Checker WhatsApp Bot to production environments with security best practices and performance optimizations.

## 🚀 Deployment Options

### 1. Docker Container Deployment

#### Single Container Deployment

```bash
# Build production image
docker build -t reality-checker:latest .

# Run with production configuration
docker run -d \
  --name reality-checker \
  --restart unless-stopped \
  --env-file .env.production \
  -p 8000:8000 \
  -v /opt/reality-checker/data:/app/data \
  -v /opt/reality-checker/logs:/app/logs \
  reality-checker:latest
```

#### Docker Compose Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: reality-checker:latest
    container_name: reality-checker-app
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/reality_checker
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    volumes:
      - /opt/reality-checker/data:/app/data
      - /opt/reality-checker/logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    container_name: reality-checker-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=reality_checker
      - POSTGRES_USER=reality_checker
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    container_name: reality-checker-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: reality-checker-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 2. Kubernetes Deployment

#### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: reality-checker

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: reality-checker-config
  namespace: reality-checker
data:
  OPENAI_MODEL: "gpt-4"
  MAX_PDF_SIZE_MB: "10"
  LOG_LEVEL: "INFO"
  WEBHOOK_VALIDATION: "true"
```

#### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: reality-checker-secrets
  namespace: reality-checker
type: Opaque
data:
  # Base64 encoded values
  openai-api-key: <base64-encoded-key>
  twilio-account-sid: <base64-encoded-sid>
  twilio-auth-token: <base64-encoded-token>
  jwt-secret-key: <base64-encoded-secret>
  admin-password: <base64-encoded-password>
```

#### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reality-checker
  namespace: reality-checker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: reality-checker
  template:
    metadata:
      labels:
        app: reality-checker
    spec:
      containers:
      - name: reality-checker
        image: reality-checker:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: reality-checker-secrets
              key: openai-api-key
        - name: TWILIO_ACCOUNT_SID
          valueFrom:
            secretKeyRef:
              name: reality-checker-secrets
              key: twilio-account-sid
        - name: TWILIO_AUTH_TOKEN
          valueFrom:
            secretKeyRef:
              name: reality-checker-secrets
              key: twilio-auth-token
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: reality-checker-secrets
              key: jwt-secret-key
        envFrom:
        - configMapRef:
            name: reality-checker-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service and Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: reality-checker-service
  namespace: reality-checker
spec:
  selector:
    app: reality-checker
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: reality-checker-ingress
  namespace: reality-checker
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.yourcompany.com
    secretName: reality-checker-tls
  rules:
  - host: api.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: reality-checker-service
            port:
              number: 80
```

### 3. Cloud Platform Deployments

#### AWS ECS/Fargate

```json
{
  "family": "reality-checker",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "reality-checker",
      "image": "account.dkr.ecr.region.amazonaws.com/reality-checker:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:reality-checker/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/reality-checker",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy reality-checker \
  --image gcr.io/PROJECT-ID/reality-checker:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars LOG_LEVEL=INFO \
  --set-secrets OPENAI_API_KEY=openai-key:latest \
  --set-secrets TWILIO_ACCOUNT_SID=twilio-sid:latest
```

#### Azure Container Instances

```yaml
# azure-container-group.yaml
apiVersion: 2019-12-01
location: eastus
name: reality-checker
properties:
  containers:
  - name: reality-checker
    properties:
      image: yourregistry.azurecr.io/reality-checker:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 1
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: LOG_LEVEL
        value: INFO
      - name: OPENAI_API_KEY
        secureValue: your-openai-key
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 8000
```

## 🔒 Security Configuration

### 1. Environment Variables Security

**Production .env.production file:**

```bash
# ============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================================================

# OpenAI Configuration
OPENAI_API_KEY=sk-your-production-openai-key
OPENAI_MODEL=gpt-4

# Optional: OpenAI fine-tuning (use defaults if not specified)
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=1000
OPENAI_TIMEOUT=30.0

# Twilio Configuration
TWILIO_ACCOUNT_SID=ACyour-production-account-sid
TWILIO_AUTH_TOKEN=your-production-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Security Configuration
JWT_SECRET_KEY=your-very-secure-random-secret-key-256-bits
JWT_EXPIRY_HOURS=24
JWT_REFRESH_EXPIRY_DAYS=7

# Admin Credentials (CHANGE THESE!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# Application Configuration
MAX_PDF_SIZE_MB=10
LOG_LEVEL=INFO
WEBHOOK_VALIDATION=true

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/reality_checker

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# CORS Configuration
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### 2. Secrets Management

#### AWS Secrets Manager

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "reality-checker/openai-key" \
  --description "OpenAI API key for Reality Checker" \
  --secret-string "sk-your-openai-key"

aws secretsmanager create-secret \
  --name "reality-checker/twilio-credentials" \
  --description "Twilio credentials for Reality Checker" \
  --secret-string '{"account_sid":"ACxxx","auth_token":"xxx","phone_number":"+1234567890"}'
```

#### Kubernetes Secrets

```bash
# Create secrets from command line
kubectl create secret generic reality-checker-secrets \
  --from-literal=openai-api-key=sk-your-key \
  --from-literal=twilio-account-sid=ACyour-sid \
  --from-literal=twilio-auth-token=your-token \
  --from-literal=jwt-secret-key=your-secret \
  -n reality-checker
```

### 3. Network Security

#### Nginx Configuration

```nginx
# nginx.prod.conf
events {
    worker_connections 1024;
}

http {
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=webhook:10m rate=5r/s;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name api.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Webhook endpoint with stricter rate limiting
        location /webhook/ {
            limit_req zone=webhook burst=10 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 4. Application Security

#### Security Checklist

- [ ] **Change Default Credentials**: Update admin username/password
- [ ] **Strong JWT Secret**: Use cryptographically secure random key
- [ ] **HTTPS Only**: Enforce TLS/SSL in production
- [ ] **CORS Configuration**: Restrict origins to your domains
- [ ] **Rate Limiting**: Configure appropriate limits
- [ ] **Input Validation**: Enable all validation middleware
- [ ] **Webhook Validation**: Enable Twilio signature validation
- [ ] **Security Headers**: Configure CSP, HSTS, etc.
- [ ] **Database Security**: Use connection encryption
- [ ] **Log Sanitization**: Remove sensitive data from logs

## 📊 Monitoring and Observability

### 1. Application Monitoring

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'reality-checker'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Reality Checker Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 2. Log Management

#### ELK Stack Configuration

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### 3. Alerting

#### AlertManager Configuration

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourdomain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@yourdomain.com'
    subject: 'Reality Checker Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
```

## 🚀 Performance Optimization

### 1. Application Optimization

#### Async Configuration

```python
# app/config.py - Production optimizations
import asyncio
from functools import lru_cache

class ProductionConfig:
    # Connection pooling
    HTTP_POOL_CONNECTIONS = 20
    HTTP_POOL_MAXSIZE = 20
    HTTP_MAX_RETRIES = 3
    
    # Async settings
    ASYNC_POOL_SIZE = 10
    ASYNC_MAX_OVERFLOW = 20
    
    # Caching
    CACHE_TTL = 300  # 5 minutes
    CACHE_MAX_SIZE = 1000
    
    # Rate limiting
    RATE_LIMIT_STORAGE = "redis://redis:6379/1"
```

#### Database Optimization

```python
# Database connection pooling
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 2. Infrastructure Optimization

#### Load Balancing

```yaml
# HAProxy configuration
global:
    daemon

defaults:
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend reality_checker_frontend
    bind *:80
    default_backend reality_checker_backend

backend reality_checker_backend
    balance roundrobin
    option httpchk GET /health
    server app1 app1:8000 check
    server app2 app2:8000 check
    server app3 app3:8000 check
```

#### CDN Configuration

```javascript
// CloudFlare configuration
const cdnConfig = {
  caching: {
    browser_ttl: 3600,
    edge_ttl: 86400,
    cache_level: "aggressive"
  },
  security: {
    security_level: "medium",
    challenge_ttl: 1800
  },
  performance: {
    minify: {
      css: true,
      js: true,
      html: true
    },
    compression: "gzip"
  }
};
```

## 🔄 Backup and Recovery

### 1. Database Backup

```bash
#!/bin/bash
# backup.sh - Database backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/reality-checker"
DB_NAME="reality_checker"

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -h postgres -U reality_checker $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://your-backup-bucket/reality-checker/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

### 2. Application Data Backup

```bash
#!/bin/bash
# app-backup.sh - Application data backup

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/reality-checker"

# Backup application data
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz /opt/reality-checker/data

# Backup logs
tar -czf $BACKUP_DIR/app_logs_$DATE.tar.gz /opt/reality-checker/logs

# Upload to cloud storage
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/reality-checker/
```

### 3. Disaster Recovery

```yaml
# disaster-recovery.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: disaster-recovery-plan
data:
  recovery-steps: |
    1. Assess the scope of the outage
    2. Activate backup infrastructure
    3. Restore database from latest backup
    4. Deploy application to backup environment
    5. Update DNS to point to backup
    6. Verify all services are operational
    7. Communicate status to stakeholders
```

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] **Environment Configuration**
  - [ ] Production .env file configured
  - [ ] Secrets properly stored and referenced
  - [ ] Database connection tested
  - [ ] External API access verified

- [ ] **Security Review**
  - [ ] Default credentials changed
  - [ ] JWT secret key updated
  - [ ] HTTPS/TLS configured
  - [ ] CORS origins restricted
  - [ ] Rate limiting configured

- [ ] **Infrastructure Setup**
  - [ ] Production servers provisioned
  - [ ] Load balancer configured
  - [ ] Database server ready
  - [ ] Monitoring systems deployed
  - [ ] Backup systems configured

### Deployment

- [ ] **Application Deployment**
  - [ ] Docker image built and tested
  - [ ] Database migrations applied
  - [ ] Application deployed to production
  - [ ] Health checks passing
  - [ ] Smoke tests completed

- [ ] **Post-Deployment Verification**
  - [ ] All endpoints responding correctly
  - [ ] WhatsApp webhook functioning
  - [ ] Dashboard accessible
  - [ ] Monitoring data flowing
  - [ ] Alerts configured and tested

### Post-Deployment

- [ ] **Documentation Updates**
  - [ ] Deployment notes documented
  - [ ] Runbook updated
  - [ ] Team notified of deployment
  - [ ] Monitoring dashboards shared

- [ ] **Ongoing Maintenance**
  - [ ] Backup verification scheduled
  - [ ] Security updates planned
  - [ ] Performance monitoring active
  - [ ] Log retention configured

## 🆘 Troubleshooting Production Issues

### Common Production Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats reality-checker-app

# Check for memory leaks
docker exec reality-checker-app python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

#### Database Connection Issues

```bash
# Test database connectivity
docker exec reality-checker-app python -c "
from app.database.database import get_database
import asyncio
async def test():
    db = get_database()
    await db.execute('SELECT 1')
    print('Database connection OK')
asyncio.run(test())
"
```

#### External API Failures

```bash
# Test OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test Twilio API
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json" \
     -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN
```

### Emergency Procedures

#### Service Restart

```bash
# Docker restart
docker restart reality-checker-app

# Kubernetes restart
kubectl rollout restart deployment/reality-checker -n reality-checker

# Check service status
kubectl get pods -n reality-checker
```

#### Rollback Deployment

```bash
# Docker rollback
docker stop reality-checker-app
docker run -d --name reality-checker-app-rollback \
  --env-file .env.production \
  reality-checker:previous-version

# Kubernetes rollback
kubectl rollout undo deployment/reality-checker -n reality-checker
```

---

This deployment guide provides comprehensive instructions for deploying the Reality Checker WhatsApp Bot to production environments with proper security, monitoring, and maintenance procedures.