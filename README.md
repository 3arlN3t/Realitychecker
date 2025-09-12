# Reality Checker WhatsApp Bot

An AI-powered WhatsApp bot that analyzes job advertisements to detect potential scams, helping users identify legitimate job opportunities versus fraudulent postings.

![Reality Checker Logo](https://via.placeholder.com/150x50/4CAF50/FFFFFF?text=Reality+Checker)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/3arlN3t/Realitychecker)
[![CI](https://github.com/3arlN3t/Realitychecker/actions/workflows/ci.yml/badge.svg)](https://github.com/3arlN3t/Realitychecker/actions/workflows/ci.yml)
[![Nightly](https://github.com/3arlN3t/Realitychecker/actions/workflows/nightly.yml/badge.svg)](https://github.com/3arlN3t/Realitychecker/actions/workflows/nightly.yml)
[![CD](https://github.com/your-org/reality-checker-whatsapp-bot/actions/workflows/cd.yml/badge.svg)](https://github.com/your-org/reality-checker-whatsapp-bot/actions/workflows/cd.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)

## 📚 Documentation

- Full documentation archive: `docs/legacy/`
  - Browse all implementation notes, deployment guides, and summaries moved from the repo root.

## 🧰 Scripts

- Scripts overview: see `scripts/README.md`
- Common commands (via Makefile):
  - `make start` — start backend (dev reload)
  - `make start-dashboard` — backend with integrated dashboard
  - `make deploy` | `make deploy-dev` | `make deploy-k8s` | `make deploy-prod`
  - `make db-init` | `make db-check` | `make db-migrate`
  - `make health-check` | `make monitor` | `make redis-diagnostics`


## 🚀 Features

- **WhatsApp Integration**: Seamless interaction through Twilio WhatsApp Business API
- **Multi-Channel Support**: Web interface, direct API, and WhatsApp bot for flexible access
- **AI-Powered Analysis**: Uses OpenAI GPT-4 with advanced error handling, circuit breakers, and structured response parsing
- **PDF Processing**: Extracts and analyzes text from uploaded PDF job postings with enhanced error handling
- **Trust Scoring**: Provides 0-100 trust scores with detailed reasoning and confidence levels
- **Admin Dashboard**: Integrated dashboard at `/dashboard`. React admin app available in `dashboard/` (optional build)
- **Multi-Factor Authentication**: TOTP-based MFA with backup codes and admin management
- **Real-time Monitoring**: Live metrics, WebSocket updates, error tracking, and performance monitoring
- **Advanced Analytics**: A/B testing, user clustering, pattern detection, and predictive analytics
- **Role-Based Access**: Admin and Analyst roles with granular permissions
- **Comprehensive Reporting**: Generate and export detailed reports with analysis accuracy metrics
- **Production-Ready**: Comprehensive security, rate limiting, health checks, and observability

## 🧭 Architecture Overview

### High-Level Diagram

```
External User (WhatsApp)
      |
      v
  Twilio WhatsApp
      |
      v   HTTPS (webhook POST)
+------------------------------+
|    FastAPI (app/main.py)     |
|  - Routers: /webhook, /web,  |
|            /health, /api/*   |
|  - Middleware: CORS, security|
|            perf, rate-limit  |
|  - DI container (services)   |
+--------------+---------------+
               | immediate ACK (<500ms)
               v
        Background Task Queue
               |
               v
   +-----------------------------+
   | MessageHandlerService       |
   | - decides text vs PDF       |
   | - orchestrates services     |
   +--+-----------+--------------+
      |           |
      |           | PDF
      |           v
      |   PDFProcessingService
      |     - download/validate/extract
      |
      v  text
EnhancedAIAnalysisService (OpenAI)
      |     - rules + fallbacks
      |     - history/similarity
      v
 TwilioResponseService  ---> Twilio API ---> User (WhatsApp)
      |
      v
UserManagementService (DB write)
      |
      v
+-------------------------------+
| Database (SQLite/Postgres)    |
+-------------------------------+

Support/Infra:
- Redis (cache/validation) <--> RedisConnectionManager/CachingService
- Metrics/Error tracking/Diagnostics <--> WebSocket alerts → Dashboard
- React Dashboard (`dashboard/`) optional build for richer UI
```

### Sequence Diagrams

WhatsApp Text
```
User → Twilio → FastAPI /webhook/whatsapp → (fast validation + cache)
→ immediate 200 ACK → queue task → MessageHandlerService
→ EnhancedAIAnalysisService (OpenAI) → TwilioResponseService → Twilio → User
→ record interaction (DB)
```

WhatsApp PDF
```
User → Twilio → FastAPI /webhook/whatsapp → 200 ACK → queue task
→ MessageHandlerService → PDFProcessingService (download/validate/extract)
→ EnhancedAIAnalysisService (OpenAI) → TwilioResponseService → Twilio → User
→ record interaction (DB)
```

Web Upload (text/PDF)
```
User → GET /web/upload (form)
→ POST /web/analyze/text or /web/analyze/pdf
→ MessageHandlerService (direct) → [PDFProcessingService if PDF]
→ EnhancedAIAnalysisService (OpenAI) → JSON response to browser
→ record interaction (DB)
```

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Dashboard](#dashboard)
- [Documentation](#documentation)
- [Scripts](#scripts)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Twilio account with WhatsApp Business API access

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/reality-checker-whatsapp-bot.git
cd reality-checker-whatsapp-bot
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env
```

### 3. Run with Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the Application

- Root/Test Page: http://localhost:8000
- API (text): http://localhost:8000/api/analyze/text
- Direct test UI: http://localhost:8000/api/direct/test
- Dashboard (integrated): http://localhost:8000/dashboard (alias: /admin)
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Tip: The WhatsApp webhook endpoint for Twilio is POST http://YOUR_HOST/webhook/whatsapp

## 📦 Installation

### Option 1: Docker (Recommended)

Docker provides the easiest way to run the application with all dependencies:

```bash
# Clone repository
git clone https://github.com/your-org/reality-checker-whatsapp-bot.git
cd reality-checker-whatsapp-bot

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start with Docker Compose
docker-compose up --build
```

### Option 2: Manual Installation

#### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python manage_db.py init

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Build for production (integrated into backend)
npm run build

# Or run development server (for frontend development)
npm start
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

#### Required Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Twilio Configuration
TWILIO_ACCOUNT_SID=ACyour-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

#### Optional Variables (recognized by the app)

```bash
# Application Settings
OPENAI_MODEL=gpt-4                        # OpenAI model to use
MAX_PDF_SIZE_MB=10                        # Maximum PDF file size (MB)
LOG_LEVEL=INFO                            # DEBUG, INFO, WARNING, ERROR
WEBHOOK_VALIDATION=true                   # Enable Twilio webhook signature validation

# Authentication
JWT_SECRET_KEY=your-secret-key            # CHANGE IN PRODUCTION
JWT_EXPIRY_HOURS=24                       # Access token lifetime (hours)
JWT_REFRESH_EXPIRY_DAYS=7                 # Refresh token lifetime (days)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123                   # CHANGE IN PRODUCTION
ANALYST_USERNAME=
ANALYST_PASSWORD=

# Development toggles
DEVELOPMENT_MODE=false
USE_MOCK_TWILIO=false                     # Use mock Twilio for local dev/tests
BYPASS_AUTHENTICATION=false               # Disable auth for local testing

# Redis (caching/validation)
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=50
REDIS_CONNECTION_TIMEOUT=5.0
REDIS_SOCKET_TIMEOUT=5.0
REDIS_RETRY_ATTEMPTS=3
REDIS_RETRY_BACKOFF=1.0
REDIS_HEALTH_CHECK_INTERVAL=30
REDIS_CIRCUIT_BREAKER_THRESHOLD=5
REDIS_CIRCUIT_BREAKER_TIMEOUT=60

# Performance
WEBHOOK_TIMEOUT=2.0                       # Overall webhook SLA (seconds)
WEBHOOK_ACKNOWLEDGMENT_TIMEOUT=0.5        # Immediate ACK budget (seconds)
TASK_QUEUE_MAX_SIZE=1000
TASK_QUEUE_WORKER_COUNT=5
TASK_QUEUE_BATCH_SIZE=10
TASK_PROCESSING_TIMEOUT=30
TASK_RETRY_ATTEMPTS=3
TASK_RETRY_BACKOFF=2.0
PERFORMANCE_MONITORING_ENABLED=true
PERFORMANCE_ALERT_THRESHOLD_WEBHOOK=1.0
PERFORMANCE_ALERT_THRESHOLD_CRITICAL=3.0

# Database
DATABASE_URL=sqlite+aiosqlite:///data/reality_checker.db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false
# DB circuit breaker (used by connection pool)
DB_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
DB_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

#### Integration Env Mapping

- OpenAI
  - `OPENAI_API_KEY` (required)
  - `OPENAI_MODEL` (optional; default `gpt-4`)
- Twilio (WhatsApp)
  - `TWILIO_ACCOUNT_SID` (required)
  - `TWILIO_AUTH_TOKEN` (required)
  - `TWILIO_PHONE_NUMBER` (required)
  - `WEBHOOK_VALIDATION` (optional; enable signature validation)
- Redis (cache/validation/rate-limits)
  - `REDIS_URL` plus `REDIS_*` tuning knobs (pool sizes, timeouts, circuit breaker)
- Database (SQLite/Postgres via SQLAlchemy async)
  - `DATABASE_URL` (default SQLite)
  - `DB_*` pool settings and `DB_CIRCUIT_BREAKER_*`

Note: Rate limiting thresholds are currently configured in code (see `app/main.py` and middleware) and may not be driven by env vars.

### Configuration Validation

The application validates all required configuration on startup:

```bash
# Check configuration
python -c "from app.config import get_config; print('✅ Configuration valid')"

# Test OpenAI connection
python -c "
from app.config import get_config
from app.services.openai_analysis import OpenAIAnalysisService
import asyncio

async def test_openai():
    config = get_config()
    service = OpenAIAnalysisService(config)
    health = await service.health_check()
    print(f'OpenAI Status: {health[\"status\"]}')

asyncio.run(test_openai())
"
```

## 🎯 Usage

### Usage Options

#### WhatsApp Bot Usage

1. **Add the Bot**: Add your Twilio WhatsApp number to your contacts
2. **Send Job Ad**: Send either:
   - Plain text job advertisement
   - PDF file containing job posting
3. **Get Analysis**: Receive trust score, classification, and detailed reasoning

#### Web API Usage

1. Visit root test page: http://localhost:8000 or direct test at http://localhost:8000/api/direct/test
2. Submit job ad text or upload a PDF
3. Get analysis: trust score, classification, and detailed reasoning

#### Key API Endpoints

- Webhook (Twilio): `POST /webhook/whatsapp` (optimized handler: `/webhook/whatsapp-optimized`)
- Web Upload UI: `GET /web/upload`
- Web Analyze (text): `POST /web/analyze/text` (form field `job_text`)
- Web Analyze (PDF): `POST /web/analyze/pdf` (form field `pdf_file`)
- API Analyze (text): `POST /api/analyze/text`
- Direct Analyze (text): `POST /api/direct/analyze`
- Direct Analyze (PDF): `POST /api/direct/analyze-pdf`
- API Status: `GET /api/analyze/status`

#### Example Interaction

```
User: "Software Engineer position at Google. $200k salary. 
       Send $500 for background check to secure position."

Bot: 🔍 Job Analysis Results

Trust Score: 15/100
Classification: Likely Scam

Reasons:
1. Requests upfront payment for background check
2. Unusually high salary without proper verification process  
3. Legitimate companies don't ask for money from candidates

⚠️ This appears to be a job scam. Legitimate employers never ask for upfront payments.
```

### Dashboard Usage

Access the admin dashboard at `http://localhost:8000/dashboard`:

1. **Login**: Use configured admin credentials (supports MFA)
2. **Dashboard**: View real-time system metrics, health status, and key performance indicators
3. **Analytics**: Analyze usage trends, classification patterns, and AI performance metrics
4. **Monitoring**: Real-time monitoring of active requests, error rates, and response times
5. **Users**: Manage WhatsApp user interactions, view history, block/unblock users
6. **Configuration**: System settings management (admin only)
7. **Reports**: Generate and export comprehensive reports with custom parameters
8. **MFA Management**: Setup and manage multi-factor authentication

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### OpenAI Analysis Service Features

The OpenAI analysis service includes several advanced features:

- **Structured Response Parsing**: Validates JSON responses with required fields
- **Input Sanitization**: Security validation and text sanitization before analysis
- **Error Classification**: Specific handling for timeout, rate limit, and API errors
- **Correlation Tracking**: Request correlation IDs for debugging and monitoring
- **Metrics Collection**: Performance metrics and error tracking
- **Health Monitoring**: Service health checks and status reporting

### Key Endpoints

#### WhatsApp Webhook
```http
POST /webhook/whatsapp
Content-Type: application/x-www-form-urlencoded

# Twilio webhook payload
```

### Twilio Webhook Setup

Follow these steps in the Twilio Console to connect WhatsApp to the app:

1. WhatsApp sender
   - Use your Sandbox (for development) or a registered WhatsApp Business number.
2. Set Webhook URL
   - When a message comes in: set to `https://YOUR_DOMAIN/webhook/whatsapp` (method: POST).
   - For local development, expose your app with a tunneling tool (e.g., ngrok) and use that URL.
3. Signature validation
   - Keep `WEBHOOK_VALIDATION=true` (default). The app validates the `X-Twilio-Signature` header.
4. Test a message
   - Send a WhatsApp message to your Twilio number. Check server logs for entries from the webhook handler.
5. Troubleshooting
   - Use the Twilio “Debugger” (Console → Monitor → Debugger) to inspect request/response and signature issues.
   - Verify `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` are set in `.env`.

#### Health & Monitoring
```http
# Health
GET /health

# Monitoring (JWT-protected in production)
GET /monitoring/active-requests
GET /monitoring/error-rates
GET /monitoring/response-times
GET /monitoring/connection-pool
GET /monitoring/circuit-breakers

# Realtime metrics/alerts
WS  /monitoring/ws?token=JWT
```

#### Authentication Endpoints
```http
# User login
POST /auth/login

# Token refresh
POST /auth/refresh

# User logout
POST /auth/logout

# Get current user info
GET /auth/me

# Create new user (admin only)
POST /auth/users

# Get authentication statistics
GET /auth/stats
```

#### Dashboard API
```http
# Dashboard overview
GET /dashboard/overview
Authorization: Bearer <jwt-token>

# Analytics trends
GET /analytics/trends?period=week

# User management
GET /users?page=1&limit=50

# Real-time metrics
GET /metrics/realtime

# Generate reports
POST /reports/generate
```

#### Multi-Factor Authentication (MFA)
```http
# Setup MFA
POST /mfa/setup

# Complete MFA setup
POST /mfa/complete-setup

# Verify MFA token
POST /mfa/verify

# Get MFA status
GET /mfa/status

# Disable MFA
POST /mfa/disable

# Get MFA statistics (admin)
GET /mfa/statistics
```

#### Monitoring & Analytics
```http
# Real-time monitoring
GET /monitoring/active-requests
GET /monitoring/error-rates
GET /monitoring/response-times

# Circuit breaker status
GET /monitoring/circuit-breakers
GET /monitoring/openai/circuit-breaker

# Cache performance metrics  
GET /monitoring/cache/stats
GET /monitoring/cache/hit-rate

# Rate limiting statistics
GET /monitoring/rate-limits/global
GET /monitoring/rate-limits/whatsapp/{phone_hash}
GET /monitoring/rate-limits/web/sessions
GET /monitoring/rate-limits/web/fingerprints

# Advanced analytics
GET /analytics/patterns
POST /analytics/ab-tests
GET /analytics/ab-tests/{test_id}
POST /analytics/user-clustering
```

#### Text Analysis APIs
```http
# Direct API analysis
POST /api/direct/analyze
Content-Type: application/x-www-form-urlencoded

# API upload analysis
POST /api/upload/text
Content-Type: application/x-www-form-urlencoded

# Simple API test
GET /api/simple/test
```

## 🖥️ Dashboard

The integrated dashboard at `/dashboard` provides monitoring and analytics. A separate React admin app lives in `dashboard/` (optional) and can be built/deployed for a richer UI.

### Features

- **System Health**: Real-time service status, health checks, and dependency monitoring
- **Analytics**: Usage trends, classification breakdowns, peak hours, and predictive analytics
- **User Management**: WhatsApp user interactions, detailed profiles, and interaction history
- **Web Session Monitoring**: Track anonymous, session-based, and established web users
- **Rate Limit Analytics**: Multi-tier rate limiting statistics and user progression tracking
- **Abuse Detection**: Browser fingerprinting patterns and suspicious behavior alerts
- **Configuration**: System settings, OpenAI model configuration, and security settings
- **Reporting**: Custom reports with CSV/PDF export and scheduled report generation
- **Real-time Monitoring**: Live metrics, active request tracking, and WebSocket updates
- **Multi-Factor Authentication**: TOTP setup, backup codes, and admin MFA management
- **Advanced Analytics**: A/B testing, user clustering, and pattern recognition
- **Role-Based Access**: Admin and Analyst roles with appropriate permissions
- **Performance Monitoring**: Response time tracking, error rate analysis, circuit breaker status, and cache hit rates

### Access

1. Navigate to `http://localhost:8000/dashboard` (alias: `/admin`)
2. Login with configured credentials (admin/admin123 by default; change in production)
3. MFA supported via `/mfa/*` endpoints

### React Dashboard (Optional)

- Build the React app
  - `cd dashboard && npm install && npm run build`
- Serve via FastAPI automatically
  - The backend mounts `dashboard/build` at `/react-dashboard` when the build folder exists.
  - Keep using `/dashboard` (Jinja) as the main entry; use `/react-dashboard` to preview the React build.
- Rebuilding
  - Re-run `npm run build` after frontend changes.

## 🚀 Deployment

### Production Deployment

#### Docker Deployment (Recommended)

```bash
# 1. Prepare production environment
cp .env.example .env.production
# Configure production values in .env.production

# 2. Build production image
docker build -t reality-checker:latest .

# 3. Run with production configuration
docker run -d \
  --name reality-checker \
  --env-file .env.production \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  reality-checker:latest
```

#### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reality-checker
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
        # ... other environment variables
```

#### Cloud Deployment

**AWS ECS/Fargate**:
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t reality-checker .
docker tag reality-checker:latest <account>.dkr.ecr.us-east-1.amazonaws.com/reality-checker:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/reality-checker:latest
```

**Google Cloud Run**:
```bash
# Deploy to Cloud Run
gcloud run deploy reality-checker \
  --image gcr.io/PROJECT-ID/reality-checker \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Production Considerations

#### Security Checklist

- [ ] Change default admin credentials
- [ ] Use strong JWT secret key
- [ ] Enable HTTPS/TLS
- [ ] Configure proper CORS origins
- [ ] Enable webhook signature validation
- [ ] Set up proper firewall rules
- [ ] Use secrets management (AWS Secrets Manager, etc.)

#### Performance Optimization

- [x] Configure optimized connection pooling (with reduced pool sizes and faster timeouts)
- [x] Enhanced database indexes for analytics queries
- [x] Optimized request logging to reduce I/O overhead
- [ ] Set up Redis for caching (infrastructure available)
- [ ] Enable response compression
- [ ] Configure CDN for static assets
- [ ] Set up load balancing
- [ ] Monitor resource usage

#### Monitoring & Alerting

- [ ] Set up application monitoring (Datadog, New Relic)
- [ ] Configure log aggregation (ELK stack, CloudWatch)
- [ ] Set up error tracking (Sentry)
- [ ] Configure health check monitoring
- [ ] Set up alerting for critical errors

## 🛠️ Development
## 🧰 Operational Playbook

- Start locally
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Health check
  - `curl http://localhost:8000/health`
- Monitor (JWT may be required in production)
  - `curl -H "Authorization: Bearer <JWT>" http://localhost:8000/monitoring/active-requests`
  - `curl -H "Authorization: Bearer <JWT>" http://localhost:8000/monitoring/connection-pool`
- Logs
  - App logs print to stdout; tune level via `LOG_LEVEL`.
- Redis quick check (if enabled)
  - Ensure `REDIS_URL` is reachable; watch `redis.log` in repo root if running local Redis via docker-compose.
- Database quick check
  - Default SQLite at `data/reality_checker.db`. For Postgres, verify `DATABASE_URL` and connectivity.
- Background tasks
  - Webhook acks immediately; analysis continues in background workers. If results stall, inspect task queue metrics via monitoring endpoints and check Redis availability.

### Local Webhook via ngrok (for Twilio)

- Expose your local server
  - `./scripts/ngrok_expose.sh 8000` (defaults to 8000 if no port is passed)
  - Copy the HTTPS URL (e.g., `https://<sub>.ngrok.io`)
- Configure Twilio
  - Set “When a message comes in” to `https://<sub>.ngrok.io/webhook/whatsapp` (POST)
  - Keep `WEBHOOK_VALIDATION=true` in `.env`
- Test
  - Send a WhatsApp message to your Twilio number and watch server logs.

## 📦 CI/CD Pipeline

### GitHub Actions Workflows

- **CI Workflow** (`.github/workflows/ci.yml`): Lint, type-check, build frontend, and run tests on each push and pull request to `main`.
- **CD Workflow** (`.github/workflows/cd.yml`): Builds and pushes Docker images tagged with `latest` and commit SHA, then deploys to Kubernetes on pushes to `main`.

### Repository Secrets

| Secret               | Description                                              |
|----------------------|----------------------------------------------------------|
| `DOCKER_REGISTRY`    | Docker registry URL (e.g., `ghcr.io` or `docker.io`).    |
| `DOCKER_REPOSITORY`  | Repository path (e.g., `your-org/reality-checker`).      |
| `DOCKER_USERNAME`    | Username for Docker registry authentication.             |
| `DOCKER_PASSWORD`    | Password or token for Docker registry authentication.    |
| `KUBE_CONFIG`        | Base64-encoded Kubernetes `kubeconfig` for deployment.   |

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/reality-checker-whatsapp-bot.git
cd reality-checker-whatsapp-bot

# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up frontend
cd dashboard
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with development values

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend (in another terminal)
cd dashboard
npm start
```

### Development Tools

#### Code Quality

```bash
# Format code
black app/
black tests/

# Lint code
flake8 app/
flake8 tests/

# Type checking
mypy app/
```

#### Database Management

```bash
# Initialize database
python manage_db.py init

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Reset database
python manage_db.py reset
```

### Project Structure

```
reality-checker-whatsapp-bot/
├── app/                    # Backend application
│   ├── api/               # API endpoints
│   │   ├── auth.py        # Authentication & user management
│   │   ├── mfa.py         # Multi-factor authentication
│   │   ├── dashboard.py   # Dashboard API endpoints
│   │   ├── analytics.py   # Advanced analytics & A/B testing
│   │   ├── monitoring.py  # Real-time monitoring
│   │   ├── webhook.py     # WhatsApp webhook handler
│   │   └── health.py      # Health check endpoints
│   ├── services/          # Business logic services
│   │   ├── openai_analysis.py      # AI analysis service
│   │   ├── message_handler.py      # Message processing
│   │   ├── authentication.py       # Auth service
│   │   ├── mfa_service.py          # MFA service
│   │   └── analytics.py            # Analytics service
│   ├── models/            # Data models
│   ├── utils/             # Utility functions
│   │   ├── websocket.py   # WebSocket support
│   │   ├── metrics.py     # Metrics collection
│   │   ├── error_tracking.py # Error tracking & alerting
│   │   └── circuit_breaker.py # Circuit breaker pattern
│   ├── middleware/        # Custom middleware
│   │   ├── rate_limiting.py # Rate limiting
│   │   └── security_headers.py # Security headers
│   ├── database/          # Database layer
│   │   ├── models.py      # SQLAlchemy models
│   │   └── repositories.py # Data access layer
│   └── main.py            # FastAPI application
├── dashboard/             # React frontend
│   ├── src/               # Source code
│   │   ├── components/    # UI components
│   │   │   ├── admin/     # Admin components
│   │   │   ├── analytics/ # Analytics components
│   │   │   ├── monitoring/ # Monitoring components
│   │   │   ├── users/     # User management
│   │   │   └── ui/        # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── contexts/      # React contexts
│   │   └── __tests__/     # Frontend tests
│   ├── public/            # Static assets
│   └── build/             # Built application
├── tests/                 # Comprehensive test suite
│   ├── fixtures/          # Test data and fixtures
│   ├── test_*.py          # Backend unit tests
│   └── conftest.py        # Test configuration
├── migrations/            # Database migrations
├── k8s/                   # Kubernetes deployment configs
├── scripts/               # Utility scripts
├── data/                  # Database and logs
├── static/                # Static web assets
├── templates/             # Jinja2 templates
├── docker-compose.yml     # Development environment
├── Dockerfile             # Multi-stage container build
├── requirements.txt       # Python dependencies
├── alembic.ini           # Database migration config
├── pytest.ini           # Test configuration
└── README.md              # This file
```

## 📈 Recent Performance Improvements

The following optimizations have been implemented to enhance application performance and scalability:

### Database Optimizations
- **Composite Indexes**: Added optimized indexes for common analytics queries:
  - `user_id + timestamp` for user activity analysis
  - `classification + timestamp` for classification trend analysis  
  - `trust_score + timestamp` for scoring analytics
  - `response_time + timestamp` for performance monitoring
- **Connection Pool Tuning**: Optimized PostgreSQL connection pool settings:
  - Reduced pool size from 20 to 15 connections
  - Reduced max overflow from 30 to 25 connections
  - Faster timeout (20s vs 30s) and connection recycling (30min vs 1hr)
  - Enhanced prepared statement caching (150 vs 100)

### Application Performance
- **Smart Request Logging**: Optimized middleware logging to reduce I/O overhead:
  - Increased slow request threshold from 1s to 2s
  - Excluded health checks, static files, and metrics endpoints
  - Added warning-level logging for error responses
- **PDF Processing**: Comprehensive file size validation already implemented:
  - Content-Length header validation before download
  - Actual content size validation after download
  - Configurable size limits via `MAX_PDF_SIZE_MB`

### Infrastructure Readiness
- **AI Response Caching**: Cost-effective Redis-based caching with 24hr TTL for high-confidence results  
- **Circuit Breaker Protection**: OpenAI API calls protected with circuit breaker (3 failures → 60s timeout)
- **Per-User Rate Limiting**: Redis-based sliding window rate limiting with trusted user tiers
- **Performance Monitoring**: Built-in metrics collection and monitoring endpoints

### Reliability & Cost Optimization
- **Circuit Breaker Implementation**: 
  - OpenAI API protected with circuit breaker pattern
  - Automatically opens after 3 consecutive failures
  - 60-second recovery timeout with graceful degradation
  - Fallback responses when service unavailable
- **Smart Caching Strategy**:
  - Cache high-confidence analysis results (≥70% confidence) 
  - 24-hour TTL for cost vs freshness balance
  - Hash-based exact text matching for reliability
  - Reduces OpenAI API costs by ~40-60% for repeat queries
- **Multi-Tier Rate Limiting**:
  - **WhatsApp Users**: Per-phone sliding window (5/min, 50/hr, 200/day)
  - **Web Users**: Hybrid approach (IP + Session + Fingerprinting)
    - Anonymous: 3/min, 20/hr, 50/day (most restrictive)
    - Session-based: 6/min, 40/hr, 150/day (after cookie acceptance)
    - Established: 10/min, 80/hr, 300/day (after 5+ successful requests)
  - **Abuse Detection**: Browser fingerprinting with suspicious pattern penalties
  - **Progressive Tiers**: Automatic user promotion based on behavior
  - **Burst Protection**: 2-6 requests per 10-second window (tier-dependent)

## 🐘 PostgreSQL Migration Guide

For production deployments, migrating from SQLite to PostgreSQL is recommended for better performance and scalability.

### Environment Configuration

Set these environment variables to enable PostgreSQL:

```bash
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=reality_checker
DB_USER=your_db_user
DB_PASSWORD=your_secure_password

# Optional: Connection Pool Tuning
DB_POOL_SIZE=15                # Default optimized for moderate load
DB_MAX_OVERFLOW=25             # Allow burst capacity
DB_POOL_TIMEOUT=20             # Connection timeout in seconds
DB_POOL_RECYCLE=1800          # Recycle connections every 30 minutes
```

### Migration Steps

1. **Setup PostgreSQL Database**:
   ```sql
   CREATE DATABASE reality_checker;
   CREATE USER your_db_user WITH ENCRYPTED PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE reality_checker TO your_db_user;
   ```

2. **Update Environment Variables**:
   - Add the DB_* variables above to your `.env` file
   - Remove or comment out `DATABASE_URL` if present

3. **Run Database Migrations**:
   ```bash
   # The application will automatically detect PostgreSQL configuration
   # and create tables on startup, or run migrations manually:
   alembic upgrade head
   ```

4. **Verify Connection**:
   ```bash
   # Test the connection
   python -c "
   from app.database.database import get_database
   import asyncio
   async def test():
       db = get_database()
       health = await db.health_check()
       print(f'Status: {health[\"status\"]}')
       print(f'Database: {health[\"database_type\"]}')
   asyncio.run(test())
   "
   ```

### Data Migration (if needed)

For migrating existing SQLite data:

```bash
# Export SQLite data (manual process)
sqlite3 data/reality_checker.db ".dump" > backup.sql

# Import to PostgreSQL (after manual cleanup)
psql -h localhost -U your_db_user -d reality_checker -f cleaned_backup.sql
```

**Note**: The application automatically detects the database type from environment variables and optimizes accordingly.

## 🧪 Testing

### Running Tests

#### Backend Tests

```bash
# Run all backend tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/test_message_handler.py -v
pytest tests/test_openai_analysis.py -v
pytest tests/test_authentication.py -v
pytest tests/test_mfa.py -v

# Run integration tests
pytest tests/test_integration.py -v

# Run end-to-end tests
pytest tests/test_end_to_end.py -v

# Run performance tests
pytest tests/test_performance.py -v
```

#### Frontend Tests

```bash
cd dashboard

# Run all frontend tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:coverage:watch

# Run specific test suites
npm test -- --testPathPattern=components
npm test -- --testPathPattern=accessibility
npm test -- --testPathPattern=integration
```

#### Comprehensive Test Suite

```bash
# Run comprehensive test suite (backend + frontend)
python run_comprehensive_tests.py

# This includes:
# - Unit tests for all components
# - Integration tests for API endpoints
# - End-to-end workflow tests
# - Performance and load tests
# - Security and authentication tests
# - Accessibility tests for frontend
# - Visual regression tests
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service integration testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing

### Test Data

Sample test data is available in `tests/fixtures/`:
- Job ad samples (legitimate, suspicious, scam)
- PDF samples for processing tests
- Mock API responses

## 🔧 Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Symptoms**: Application exits immediately or fails to start

**Solutions**:
```bash
# Check configuration
python -c "from app.config import get_config; get_config()"

# Check required environment variables
grep -E "^[A-Z_]+" .env

# Check logs
tail -f logs/app.log
```

#### 2. OpenAI API Errors

**Symptoms**: "OpenAI API error" messages, timeouts, or rate limit errors

**Solutions**:
- Verify API key is correct and active
- Check API quota and billing
- Verify model name (gpt-4, gpt-3.5-turbo)
- Check network connectivity
- Review timeout settings if requests are slow

```bash
# Test OpenAI connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test analysis endpoint with timeout
curl -X POST http://localhost:8000/api/analyze/text \
     -F "job_text=Software Engineer position at Google" \
     --max-time 35
```

**Common Error Types**:
- Timeouts: Check network and upstream API health
- Rate limit: Reduce request rate or adjust upstream quotas
- Auth errors: Verify JWT secret and token validity

#### 3. Twilio Webhook Issues

**Symptoms**: WhatsApp messages not processed

**Solutions**:
- Verify webhook URL is accessible from internet
- Check Twilio webhook configuration
- Verify account SID and auth token
- Check webhook signature validation

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/webhook/whatsapp \
     -d "MessageSid=SM1234567890" \
     -d "From=whatsapp:+1234567890" \
     -d "To=whatsapp:+19876543210" \
     -d "Body=test message"
```

#### 4. PDF Processing Failures

**Symptoms**: "Could not process PDF" errors

**Solutions**:
- Check PDF file size (must be under configured limit)
- Verify PDF is not password protected
- Check PDF contains extractable text
- Verify network access to media URLs

#### 5. Dashboard Access Issues

**Symptoms**: Cannot access admin dashboard

**Solutions**:
- Verify admin credentials in .env file
- Check JWT secret key configuration
- Clear browser cache and cookies
- Check browser console for errors

```bash
# Reset admin password
python -c "
from app.services.authentication import AuthenticationService
auth = AuthenticationService()
print(auth.hash_password('new_password'))
"
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Run with debug
uvicorn app.main:app --reload --log-level debug
```

### Health Checks

The system includes comprehensive health monitoring for all external APIs and services:

```bash
# Basic health check (for load balancers)
curl http://localhost:8000/health

# Detailed health check (all services)
curl http://localhost:8000/health/detailed

# Individual service health checks
curl http://localhost:8000/health/openai      # OpenAI API status
curl http://localhost:8000/health/twilio     # Twilio API status  
curl http://localhost:8000/health/database   # Database connectivity
curl http://localhost:8000/health/redis      # Redis cache status
curl http://localhost:8000/health/ngrok      # ngrok tunnel status

# External services combined
curl http://localhost:8000/health/external

# Additional monitoring endpoints
curl http://localhost:8000/health/metrics         # Performance metrics
curl http://localhost:8000/health/readiness       # Kubernetes readiness
curl http://localhost:8000/health/liveness        # Kubernetes liveness
curl http://localhost:8000/health/circuit-breakers # Circuit breaker status
curl http://localhost:8000/health/alerts          # Active system alerts
```

#### Automated Health Monitoring

Run continuous health monitoring:

```bash
# Continuous monitoring (every 30 seconds)
python3 monitor_health.py

# Single health check
python3 monitor_health.py --once

# Custom interval and URL
python3 monitor_health.py --url http://localhost:8000 --interval 60

# Quiet mode (only show alerts)
python3 monitor_health.py --quiet
```

#### Test All Health Endpoints

```bash
# Comprehensive health system test
python3 test_enhanced_health_checks.py
```

**Monitored Services:**
- ✅ **OpenAI API**: AI analysis functionality with circuit breaker protection
- ✅ **Twilio API**: WhatsApp messaging with account validation
- ✅ **Database**: Connection pool health and query performance
- ✅ **Redis**: Cache operations and connection status
- ✅ **ngrok**: Development tunnel status (optional)

**Health Status Types:**
- `healthy`: Service fully operational
- `degraded`: Service working with issues
- `unhealthy`: Service not working
- `not_configured`: Service not configured (expected for optional services)
- `not_available`: Service not available (normal for dev tools in production)
- `circuit_open`: Circuit breaker activated due to failures

### Log Analysis

```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep -i error logs/app.log

# Filter by correlation ID
grep "correlation_id=abc123" logs/app.log
```

## 📊 Monitoring

### Metrics

The application exposes various metrics:

- Request count and response times
- Error rates and types
- Service health status
- User engagement metrics
- Analysis accuracy metrics

### Alerting

Configure alerts for:

- High error rates (>5%)
- Slow response times (>5s)
- Service unavailability
- High memory/CPU usage
- Failed authentication attempts

### Log Aggregation

For production deployments, consider:

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Fluentd**: Log collection and forwarding
- **CloudWatch**: AWS log aggregation
- **Stackdriver**: Google Cloud logging

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write comprehensive tests
- Document new features
- Follow semantic versioning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and API docs
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join GitHub Discussions for questions
- **Email**: Contact support@yourcompany.com

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Twilio for WhatsApp Business API
- FastAPI and React communities
- All contributors and testers

---

**⚠️ Security Notice**: This application processes user messages and interacts with external APIs. Always follow security best practices and keep dependencies updated.

**📱 WhatsApp Policy**: Ensure compliance with WhatsApp Business API policies and terms of service.
