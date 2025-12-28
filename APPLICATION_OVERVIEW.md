# Reality Checker WhatsApp Bot - Application Overview

## 📋 Executive Summary

**Reality Checker** is an AI-powered WhatsApp bot that protects job seekers from employment scams by analyzing job advertisements and detecting fraudulent postings. The application provides instant analysis through multiple channels (WhatsApp, Web, API) with trust scores, classifications, and detailed reasoning to help users make informed decisions.

---

## 🎯 Primary Purpose

The application serves as a **fraud detection system for job advertisements**, helping users identify:
- ✅ Legitimate job opportunities
- ⚠️ Suspicious postings that require caution
- ❌ Likely scams that should be avoided

### Problem Being Solved
Employment scams are a growing global problem where fraudsters post fake job ads to:
- Extract money from job seekers (background check fees, training costs, etc.)
- Steal personal information for identity theft
- Trick victims into money laundering schemes
- Exploit desperate job seekers with false promises

**Reality Checker** provides an accessible, instant verification tool that anyone can use via WhatsApp.

---

## 🚀 Core Capabilities

### 1. **Multi-Channel Job Analysis**

#### WhatsApp Integration
- Send job ad text or PDF files directly to the bot
- Receive instant analysis with trust scores
- Accessible to anyone with a mobile phone
- No app installation required

#### Web Interface
- Upload job postings via web form at `/web/upload`
- Analyze both text and PDF formats
- View results in browser
- Test interface at `/api/direct/test`

#### Direct API Access
- RESTful API for programmatic integration
- Supports bulk analysis for platforms
- JSON response format
- Comprehensive API documentation at `/docs`

### 2. **AI-Powered Analysis**

**Technology**: OpenAI GPT-4 (configurable model) with advanced error handling

**Analysis Components**:
- **Trust Score** (0-100): Numerical assessment of legitimacy
- **Classification**: "Legitimate", "Suspicious", or "Likely Scam"
- **Detailed Reasoning**: Specific red flags and concerns identified
- **Confidence Level**: Analysis certainty indicator

**Scam Detection Factors**:
- Upfront payment requests
- Unrealistic salary offers
- Poor grammar and spelling
- Suspicious contact methods
- Vague job descriptions
- Pressure tactics and urgency
- Too-good-to-be-true benefits
- Requests for personal financial information

### 3. **PDF Processing**
- Extracts text from uploaded PDF job postings
- Validates file size and format
- Handles password-protected PDFs
- Supports multiple PDF standards
- Size limits (configurable, default 10MB)

### 4. **Admin Dashboard**

**Accessible at**: `http://localhost:8000/dashboard` (or `/admin`)

**Features**:
- 📊 **System Health**: Real-time service status and monitoring
- 📈 **Analytics**: Usage trends, classification patterns, peak hours
- 👥 **User Management**: WhatsApp user interactions and history
- 🌐 **Web Sessions**: Track anonymous and established users
- 🚦 **Rate Limiting**: Multi-tier rate limit analytics
- 🛡️ **Security**: Abuse detection and suspicious behavior alerts
- ⚙️ **Configuration**: System settings and security controls
- 📄 **Reporting**: Generate and export custom reports
- 🔐 **MFA Management**: TOTP setup and backup codes
- 📊 **Advanced Analytics**: A/B testing, user clustering, patterns

### 5. **Security & Protection**

**Authentication**:
- Multi-factor authentication (TOTP-based)
- JWT token-based sessions
- Role-based access control (Admin/Analyst)
- Backup codes for MFA recovery

**Rate Limiting**:
- **WhatsApp Users**: 5/min, 50/hr, 200/day (per phone number)
- **Web Users**: Tiered system with automatic progression
  - Anonymous: 3/min, 20/hr, 50/day
  - Session-based: 6/min, 40/hr, 150/day
  - Established: 10/min, 80/hr, 300/day
- Browser fingerprinting for abuse detection
- Burst protection (2-6 requests per 10-second window)

**Other Security Measures**:
- Webhook signature validation (Twilio)
- Input sanitization and validation
- CORS and security headers
- Trusted host middleware
- XSS and injection protection

### 6. **Performance & Reliability**

**Optimization Features**:
- Circuit breaker for OpenAI API (auto-recovery after failures)
- Redis-based caching (24hr TTL, ~40-60% cost reduction)
- Connection pool optimization
- Background task processing
- Fast webhook acknowledgment (<500ms)
- Comprehensive health checks

**Monitoring**:
- Real-time metrics collection
- WebSocket updates for live data
- Error tracking and alerting
- Performance monitoring
- Circuit breaker status
- Cache hit rate tracking

---

## 🏗️ Technical Architecture

### High-Level Flow

```
┌─────────────────┐
│  External User  │ (WhatsApp, Web, API)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Twilio (WA)    │ or Web Browser or API Client
└────────┬────────┘
         │
         v HTTPS
┌──────────────────────────────────────────────┐
│         FastAPI Backend (app/main.py)        │
│  - Webhook handlers (/webhook/whatsapp)      │
│  - Web routes (/web/*, /api/*)               │
│  - Dashboard (/dashboard, /admin)            │
│  - Health checks (/health/*)                 │
│  - Monitoring (/monitoring/*)                │
└────────┬─────────────────────────────────────┘
         │ immediate ACK (<500ms)
         v
┌──────────────────────────────────────────────┐
│      Background Task Queue (Redis)           │
│  - Async processing of analysis requests     │
│  - Retry logic and error handling            │
└────────┬─────────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────────┐
│      Message Handler Service                 │
│  - Routes text vs PDF requests               │
│  - Orchestrates analysis workflow            │
└────┬───────────────────────────────┬─────────┘
     │                               │
     │ text                          │ PDF
     │                               v
     │                    ┌──────────────────────┐
     │                    │ PDF Processing       │
     │                    │ - Download & validate│
     │                    │ - Extract text       │
     │                    └──────────┬───────────┘
     │                               │
     v                               v
┌──────────────────────────────────────────────┐
│   Enhanced AI Analysis Service (OpenAI)      │
│  - GPT-4 analysis with circuit breaker       │
│  - Structured response parsing               │
│  - Similarity detection & history            │
│  - Caching for cost optimization             │
└────────┬─────────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────────┐
│      Twilio Response Service                 │
│  - Format and send WhatsApp messages         │
└────────┬─────────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────────┐
│      User Management & Database              │
│  - Record interactions and history           │
│  - Analytics data collection                 │
│  - User profiles and preferences             │
└──────────────────────────────────────────────┘
```

### Supporting Infrastructure

**Redis**:
- Response caching
- Rate limiting storage
- Session management
- WebSocket state
- Circuit breaker state

**Database** (SQLite/PostgreSQL):
- User interactions
- Analysis history
- Analytics data
- Admin users and roles
- MFA secrets and backup codes

**External APIs**:
- OpenAI GPT-4 (AI analysis)
- Twilio WhatsApp Business (messaging)

### Sequence Diagrams

#### WhatsApp Text Analysis
```
User → Twilio → FastAPI /webhook/whatsapp
              → Quick validation + Redis cache check
              → Return 200 ACK (immediate)
              → Queue background task
              → MessageHandlerService
              → EnhancedAIAnalysisService (OpenAI)
              → TwilioResponseService
              → Twilio → User (analysis results)
              → Database (record interaction)
```

#### WhatsApp PDF Analysis
```
User → Twilio → FastAPI /webhook/whatsapp
              → Return 200 ACK (immediate)
              → Queue background task
              → MessageHandlerService
              → PDFProcessingService
                 - Download PDF from Twilio media URL
                 - Validate size and format
                 - Extract text content
              → EnhancedAIAnalysisService (OpenAI)
              → TwilioResponseService
              → Twilio → User (analysis results)
              → Database (record interaction)
```

#### Web Upload Analysis
```
User → Browser → GET /web/upload (form)
              → POST /web/analyze/text or /web/analyze/pdf
              → MessageHandlerService (direct, no queue)
              → [PDFProcessingService if PDF]
              → EnhancedAIAnalysisService (OpenAI)
              → JSON response to browser
              → Database (record interaction)
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI/ML**: OpenAI GPT-4 (configurable model), scikit-learn, pandas, numpy
- **Messaging**: Twilio WhatsApp Business API
- **Database**: SQLAlchemy (async) with SQLite/PostgreSQL
- **Cache**: Redis 5.0+ with connection pooling
- **Security**: JWT, bcrypt, PyOTP (TOTP), python-jose
- **PDF**: pdfplumber for text extraction
- **HTTP**: httpx for async external API calls
- **ASGI Server**: Uvicorn with standard extras

### Frontend
- **Framework**: React 18+ (TypeScript)
- **UI**: Custom components with modern design
- **State**: React Context API
- **Build**: Create React App
- **Templates**: Jinja2 for integrated dashboard

### Infrastructure
- **Containers**: Docker, Docker Compose
- **Orchestration**: Kubernetes (k8s configs included)
- **CI/CD**: GitHub Actions (CI, CD, nightly builds)
- **Monitoring**: Custom metrics, WebSocket real-time updates
- **Logging**: Structured logging with correlation IDs

---

## 📊 Use Cases & Examples

### Use Case 1: Individual Job Seeker
**Scenario**: Person receives job offer via email

**Workflow**:
1. Forward job description to WhatsApp bot
2. Receive instant analysis in <30 seconds
3. Make informed decision based on trust score

**Example**:
```
Input: "Data Entry position. Work from home. $5000/week. 
       Send $200 for equipment setup."

Output:
🔍 Job Analysis Results

Trust Score: 8/100
Classification: Likely Scam

⚠️ Red Flags Detected:
1. ❌ Requests upfront payment ($200 for equipment)
2. ❌ Unrealistic salary ($5000/week for data entry)
3. ❌ Work from home with no company verification
4. ❌ Generic job description with no specifics

Recommendation: This is likely a scam. Legitimate 
employers never ask for upfront payments.
```

### Use Case 2: HR Platform Integration
**Scenario**: Job board wants to auto-verify postings

**Workflow**:
1. Use API endpoint to analyze job postings
2. Flag suspicious listings automatically
3. Require additional verification for low-trust scores
4. Batch process large volumes via API

**API Example**:
```bash
curl -X POST http://localhost:8000/api/direct/analyze \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "job_text=Software Engineer at Microsoft..."

Response:
{
  "trust_score": 85,
  "classification": "Legitimate",
  "reasoning": "Well-structured job description...",
  "confidence": 0.92
}
```

### Use Case 3: Educational Institution
**Scenario**: University career center helps students

**Workflow**:
1. Students submit job postings via web interface
2. Career counselors review flagged postings
3. Generate reports on scam trends
4. Educate students on red flags

### Use Case 4: Consumer Protection Agency
**Scenario**: Track and analyze job scam patterns

**Workflow**:
1. Collect user reports via WhatsApp
2. Analyze patterns in dashboard
3. Generate compliance reports
4. Share insights with law enforcement

---

## 📈 Key Metrics & Analytics

### System Performance
- **Webhook Response**: <500ms average
- **Analysis Latency**: 5-30 seconds (depends on OpenAI API)
- **Cache Hit Rate**: 40-60% for repeat queries
- **Uptime**: 99.9% target with health monitoring

### Usage Analytics
- Total analyses performed
- Classification breakdown (Legitimate/Suspicious/Scam)
- Peak usage hours and patterns
- User engagement metrics
- Response time trends

### Security Metrics
- Failed authentication attempts
- Rate limit violations
- Suspicious behavior patterns
- Circuit breaker activations
- API error rates

---

## 🔒 Security & Compliance

### Data Privacy
- Minimal data collection (only what's needed for analysis)
- Secure storage with encryption at rest
- No sharing of user data with third parties
- Configurable data retention policies

### Compliance Considerations
- WhatsApp Business API Terms of Service
- OpenAI API Usage Policies
- Data protection regulations (GDPR-ready)
- Webhook signature validation

### Security Best Practices
- Regular security audits
- Dependency vulnerability scanning
- Secrets management (no hardcoded credentials)
- HTTPS/TLS encryption for all communications
- Input sanitization and validation

---

## 🚀 Deployment Options

### 1. Docker (Recommended)
```bash
docker-compose up --build
```
- Easiest setup
- Includes all dependencies
- Production-ready configuration

### 2. Kubernetes
```bash
kubectl apply -f k8s/
```
- Scalable deployment
- Auto-healing and load balancing
- Comprehensive k8s manifests included

### 3. Cloud Platforms
- **AWS ECS/Fargate**: Container deployment
- **Google Cloud Run**: Serverless containers
- **Azure Container Instances**: Quick deployment
- **DigitalOcean App Platform**: Simple hosting

### 4. Manual Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📞 Access Points

### Production Endpoints
- **Root/Test**: `http://localhost:8000`
- **Dashboard**: `http://localhost:8000/dashboard`
- **Admin Panel**: `http://localhost:8000/admin` (alias)
- **API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **WhatsApp Webhook**: `POST /webhook/whatsapp` (for Twilio)

### API Endpoints
- `POST /api/analyze/text` - Analyze text job ad
- `POST /api/direct/analyze` - Direct analysis
- `POST /api/direct/analyze-pdf` - Direct PDF analysis
- `GET /api/direct/test` - Test interface
- `GET /health/detailed` - Comprehensive health check

### Dashboard Features
- `/auth/login` - User authentication
- `/dashboard/overview` - System overview
- `/analytics/*` - Analytics endpoints
- `/monitoring/*` - Real-time monitoring
- `/users` - User management
- `/reports/*` - Report generation

---

## 🎓 Getting Started

### Minimal Setup (5 minutes)
1. Clone repository
2. Copy `.env.example` to `.env`
3. Set `OPENAI_API_KEY` (required)
4. Set Twilio credentials (for WhatsApp)
5. Run `docker-compose up --build`
6. Access at `http://localhost:8000`

### Production Setup
1. Follow minimal setup
2. Change default admin credentials
3. Set strong JWT secret
4. Enable HTTPS/TLS
5. Configure proper CORS origins
6. Set up monitoring and alerting
7. Configure backup and recovery

---

## 🎯 Future Enhancements

### Planned Features
- Multi-language support
- SMS channel integration
- Telegram bot integration
- Machine learning model training on collected data
- Company verification database
- Collaborative filtering (crowd-sourced trust signals)
- Browser extension for job boards
- Mobile app for direct access

### Scalability Improvements
- Horizontal scaling with load balancers
- Distributed caching with Redis cluster
- Message queue for better async processing
- CDN for static assets
- Database read replicas

---

## 📚 Documentation

- **Main README**: `/README.md` - Comprehensive documentation
- **API Docs**: `http://localhost:8000/docs` - Interactive API documentation
- **Scripts**: `/scripts/README.md` - Utility scripts documentation
- **Legacy Docs**: `/docs/legacy/` - Historical documentation archive
- **This Document**: Application overview and purpose

---

## 🆘 Support & Contact

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check README.md and API docs
- **Health Monitoring**: Use `/health/*` endpoints for diagnostics
- **Logs**: Check application logs for troubleshooting

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **OpenAI**: GPT-4 API for AI-powered analysis
- **Twilio**: WhatsApp Business API for messaging
- **FastAPI**: Modern Python web framework
- **React**: Frontend framework
- **Open Source Community**: All contributors and maintainers

---

**Version**: 1.0.0 (Production-Ready)

**Status**: ✅ Active Development & Maintenance
