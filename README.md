# Reality Checker WhatsApp Bot

An AI-powered WhatsApp bot that analyzes job advertisements to detect potential scams, helping users identify legitimate job opportunities versus fraudulent postings.

![Reality Checker Logo](https://via.placeholder.com/150x50/4CAF50/FFFFFF?text=Reality+Checker)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-org/reality-checker-whatsapp-bot)
[![CI](https://github.com/your-org/reality-checker-whatsapp-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/reality-checker-whatsapp-bot/actions/workflows/ci.yml)
[![CD](https://github.com/your-org/reality-checker-whatsapp-bot/actions/workflows/cd.yml/badge.svg)](https://github.com/your-org/reality-checker-whatsapp-bot/actions/workflows/cd.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)

## 🚀 Features

- **WhatsApp Integration**: Seamless interaction through Twilio WhatsApp Business API
- **AI-Powered Analysis**: Uses OpenAI GPT-4 for intelligent scam detection
- **PDF Processing**: Extracts and analyzes text from uploaded PDF job postings
- **Trust Scoring**: Provides 0-100 trust scores with detailed reasoning
- **Admin Dashboard**: Web-based interface for monitoring and management
- **Real-time Analytics**: Live metrics, user management, and reporting
- **Secure & Scalable**: Production-ready with comprehensive security measures

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Dashboard](#dashboard)
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

- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

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

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Build for production
npm run build

# Or run development server
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

#### Optional Variables

```bash
# Application Settings
OPENAI_MODEL=gpt-4                    # OpenAI model to use
MAX_PDF_SIZE_MB=10                    # Maximum PDF file size
LOG_LEVEL=INFO                        # Logging level
WEBHOOK_VALIDATION=true               # Enable Twilio webhook validation

# Authentication
JWT_SECRET_KEY=your-secret-key        # JWT signing key (CHANGE IN PRODUCTION!)
JWT_EXPIRY_HOURS=24                   # Token expiry time
ADMIN_USERNAME=admin                  # Default admin username
ADMIN_PASSWORD=admin123               # Default admin password (CHANGE!)

# Database (optional)
DATABASE_URL=sqlite:///data/reality_checker.db
```

### Configuration Validation

The application validates all required configuration on startup:

```bash
# Check configuration
python -c "from app.config import get_config; print('✅ Configuration valid')"
```

## 🎯 Usage

### WhatsApp Bot Usage

1. **Add the Bot**: Add your Twilio WhatsApp number to your contacts
2. **Send Job Ad**: Send either:
   - Plain text job advertisement
   - PDF file containing job posting
3. **Get Analysis**: Receive trust score, classification, and detailed reasoning

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

Access the admin dashboard at `http://localhost:8000/admin`:

1. **Login**: Use configured admin credentials
2. **Monitor**: View real-time system metrics and health
3. **Analytics**: Analyze usage trends and detection patterns
4. **Users**: Manage WhatsApp user interactions
5. **Reports**: Generate and export comprehensive reports

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### WhatsApp Webhook
```http
POST /webhook/whatsapp
Content-Type: application/x-www-form-urlencoded

# Twilio webhook payload
```

#### Health Check
```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-01-16T10:30:00Z",
  "services": {
    "openai": "connected",
    "twilio": "connected"
  }
}
```

#### Dashboard API
```http
GET /api/dashboard/overview
Authorization: Bearer <jwt-token>

Response:
{
  "total_requests": 1250,
  "requests_today": 45,
  "error_rate": 2.3,
  "avg_response_time": 1.2
}
```

## 🖥️ Dashboard

The web dashboard provides comprehensive monitoring and management capabilities:

### Features

- **System Health**: Real-time service status and metrics
- **Analytics**: Usage trends, classification breakdowns, peak hours
- **User Management**: WhatsApp user interactions and history
- **Configuration**: System settings and bot configuration
- **Reporting**: Custom reports with CSV/PDF export
- **Real-time Monitoring**: Live metrics and active request tracking

### Access

1. Navigate to `http://localhost:8000/admin`
2. Login with configured credentials
3. Explore different sections using the navigation menu

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

- [ ] Configure connection pooling
- [ ] Set up Redis for caching
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
│   ├── services/          # Business logic services
│   ├── models/            # Data models
│   ├── utils/             # Utility functions
│   └── main.py            # FastAPI application
├── dashboard/             # React frontend
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   └── build/             # Built application
├── tests/                 # Test suite
├── migrations/            # Database migrations
├── data/                  # Database and logs
├── docker-compose.yml     # Development environment
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_message_handler.py

# Run frontend tests
cd dashboard
npm test

# Run frontend tests with coverage
npm run test:coverage
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

**Symptoms**: "OpenAI API error" messages

**Solutions**:
- Verify API key is correct and active
- Check API quota and billing
- Verify model name (gpt-4, gpt-3.5-turbo)
- Check network connectivity

```bash
# Test OpenAI connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

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
     -d "From=+1234567890&Body=test message"
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

```bash
# Check application health
curl http://localhost:8000/health

# Check specific service health
curl http://localhost:8000/api/health/openai
curl http://localhost:8000/api/health/twilio
```

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
