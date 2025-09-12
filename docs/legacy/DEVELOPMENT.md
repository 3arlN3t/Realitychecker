# 🛠️ Development Guide

This comprehensive guide covers development setup, testing, and local development workflows for the Reality Checker WhatsApp Bot.

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- ngrok installed (`brew install ngrok` on macOS)
- Twilio account with WhatsApp sandbox access
- OpenAI API key

## 🚀 Quick Start Options

### 1. Full Development Environment (Recommended)
```bash
./start.sh
```

**Features:**
- 📊 Includes React dashboard
- 🔴 Redis integration
- 🔧 Full development environment
- 🌐 Complete monitoring setup

## ⚙️ Development Setup

### Manual Installation

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
npm install

# Build for production
npm run build

# Or run development server
npm start
```

### Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
# Required Variables
OPENAI_API_KEY=sk-your-openai-api-key
TWILIO_ACCOUNT_SID=ACyour-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Authentication (Change in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Development Settings
WEBHOOK_VALIDATION=false
LOG_LEVEL=DEBUG

# Optional Settings
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
MAX_PDF_SIZE_MB=10
JWT_EXPIRY_HOURS=24
```

## 🔧 Webhook Configuration

### Automatic Setup (Recommended)
1. Run any startup script
2. Copy the webhook URL from terminal output
3. Go to [Twilio Console](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)
4. Paste webhook URL in "When a message comes in"
5. Set method to POST and save

### Manual Webhook Configuration
```bash
python3 auto_webhook_config.py
```

### Using ngrok for Local Development

```bash
# Start ngrok tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update Twilio webhook URL to: https://abc123.ngrok.io/webhook/whatsapp
```

## 🧪 Testing

### Unit Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_message_handler.py -v
pytest tests/test_openai_analysis.py -v
pytest tests/test_pdf_processing.py -v
pytest tests/test_twilio_response.py -v
```

### Integration Testing

```bash
# Run webhook integration tests
pytest tests/test_webhook.py -v

# Run end-to-end tests
pytest tests/test_end_to_end.py -v
```

### Manual Testing with WhatsApp

#### Join WhatsApp Sandbox
1. Go to Twilio Console WhatsApp sandbox
2. Note your join code (e.g., "join abc123")
3. Send this to `+1 415 523 8886` from WhatsApp
4. Wait for confirmation

#### Test Messages

**Help Command:**

```text
help
```

**Legitimate Job Test:**

```text
Software Engineer position at Google. Full-time remote work. Salary: $120,000-$150,000. Requirements: 3+ years Python experience, Bachelor's degree in Computer Science. Contact: hr@google.com for application details.
```

**Scam Detection Test:**

```text
URGENT! Make $5000/week working from home! No experience needed! Just send $99 registration fee to get started immediately!
```

**Suspicious Job Test:**

```text
Software Engineer position at Google. Salary 200k. Send 500 dollars for background check to secure position.
```

### API Testing with cURL

#### Health Check

```bash
curl -X GET http://localhost:8000/health
```

#### Webhook Test

```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=SM1234567890abcdef1234567890abcdef&From=whatsapp:+15551234567&To=whatsapp:+17087405918&Body=help&NumMedia=0"
```

#### Legitimate Job Analysis

```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=SM1234567890abcdef1234567890abcdef&From=whatsapp:+15551234567&To=whatsapp:+17087405918&Body=Software Engineer position at Google. Full-time remote work. Salary: $120,000-$150,000. Requirements: 3+ years Python experience.&NumMedia=0"
```

## 📊 Real-Time Monitoring Dashboard Testing

### Backend Verification

Ensure these components are working:
- WebSocket server implementation in `app/utils/websocket.py`
- Monitoring API endpoints in `app/api/monitoring.py`
- WebSocket alert handler registered in `app/main.py`

### Frontend Components

Verify these components are functioning:
- `useWebSocket` hook for WebSocket connections
- `MonitoringPage` component for main monitoring interface
- `LiveMetricsCard` - Real-time system metrics
- `ActiveRequestsTable` - Currently processing requests
- `ErrorRateChart` - Error rate visualization
- `ResponseTimeChart` - Response time tracking

### Manual Dashboard Testing

1. **Start Services:**
   ```bash
   # Backend
   uvicorn app.main:app --reload
   
   # Frontend
   cd dashboard && npm start
   ```

2. **Access Dashboard:**
   - Navigate to `http://localhost:3000`
   - Login with admin credentials
   - Go to Monitoring page

3. **Test Features:**
   - Verify WebSocket connection status
   - Check real-time metric updates
   - Generate test data by making API requests
   - Verify alert notifications appear

### Generating Test Data

```bash
# Generate request metrics
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed

# Generate errors
curl http://localhost:8000/nonexistent-endpoint

# Test webhook processing
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=TEST&From=whatsapp:+15551234567&To=whatsapp:+17087405918&Body=test message&NumMedia=0"
```

## 🔍 Development Tools

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Database Management

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

### Log Monitoring

```bash
# View recent logs
tail -f server.log

# Monitor errors
tail -f server.log | grep -i error

# Real-time health monitoring
watch -n 5 'curl -s http://localhost:8000/health | python3 -m json.tool'
```

## 🎯 Test Data Sets

### Legitimate Job Posts

**Software Developer:**
```
Software Developer - ABC Tech Solutions
Location: San Francisco, CA
Salary: $80,000 - $120,000 per year

Requirements:
- Bachelor's degree in Computer Science
- 3+ years of experience in Python/JavaScript
- Experience with React and Node.js

To apply: careers@abctech.com
Website: www.abctech.com/careers
```

**Marketing Coordinator:**
```
Marketing Coordinator - GreenLeaf Marketing
Location: Austin, TX (Hybrid)
Salary: $45,000 - $55,000 annually

Requirements:
- Bachelor's degree in Marketing
- 1-2 years of marketing experience
- Social media management experience

Contact: hr@greenleafmarketing.com
Phone: (512) 555-0123
```

### Scam Job Posts

**Too Good to Be True:**
```
🚨 URGENT HIRING! 🚨
WORK FROM HOME - EARN $5000/WEEK!
NO EXPERIENCE NEEDED!

Simple data entry work!
Only 2-3 hours per day required!
Start immediately!

*Must pay $99 registration fee*
Contact: WhatsApp +1-555-SCAM-123
```

**Fake Government Job:**
```
GOVERNMENT POSITION AVAILABLE
DEPARTMENT OF HOMELAND SECURITY
REMOTE DATA ANALYST - $85,000/year

Due to sensitive nature, we require a $500 security deposit to process your clearance application.

Contact Agent Johnson: agent.johnson@dhs-hiring.net
```

**MLM/Pyramid Scheme:**
```
MARKETING REPRESENTATIVE OPPORTUNITY
UNLIMITED EARNING POTENTIAL!

Join our REVOLUTIONARY marketing team!
Earn $2000-10000 per month!

Investment Required:
- Starter kit: $299
- Monthly product purchase: $150
- Training seminar: $199

This is NOT a pyramid scheme!
```

### Red Flags to Test

1. **Unrealistic pay** - $5000/week for simple work
2. **No experience required** for high-paying positions
3. **Upfront fees** - Registration, training, equipment costs
4. **Urgency tactics** - "Apply now!", "Limited time!"
5. **Vague job descriptions** - No specific company details
6. **Personal information requests** - SSN, bank details upfront
7. **Guaranteed income** promises
8. **Contact via personal email/phone** instead of company systems

## 🔧 Troubleshooting Development Issues

### Common Issues

**Port Already in Use:**
```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9
lsof -ti:4040 | xargs kill -9
```

**ngrok URL Not Found:**
```bash
# Check ngrok status
curl -s http://localhost:4040/api/tunnels | python3 -m json.tool
```

**Webhook 401 Errors:**
- Ensure `WEBHOOK_VALIDATION=false` in .env for development
- Check Twilio webhook URL matches exactly

**OpenAI API Issues:**
```bash
# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

**Database Issues:**
```bash
# Test database connection
python -c "
from app.database.database import get_database
import asyncio
async def test():
    db = get_database()
    await db.execute('SELECT 1')
    print('Database OK')
asyncio.run(test())
"
```

### Service URLs

- **Local API**: <http://localhost:8000>
- **Public API**: <https://[random].ngrok-free.app>
- **API Docs**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/health>
- **Dashboard**: <http://localhost:3000>
- **ngrok Dashboard**: <http://localhost:4040>

## 🔄 Development Workflow

### Daily Development
```bash
# Start everything
./start_dev.sh

# Make code changes (auto-reload enabled)
# Test in WhatsApp or with cURL

# Stop services
Ctrl+C
```

### Quick Testing
```bash
# Fast startup
./quick_start.sh

# Test specific feature
# Stop when done
Ctrl+C
```

### Performance Testing

```bash
# Load testing
ab -n 100 -c 10 http://localhost:8000/health

# Stress testing
wrk -t12 -c400 -d30s http://localhost:8000/health
```

## 📁 Generated Development Files

The development scripts create several files:

- `webhook_config.txt` - Current webhook configuration
- `current_webhook_config.json` - JSON configuration
- `server.log` - FastAPI server logs
- `ngrok.log` - ngrok tunnel logs

## 🔒 Security Notes

- Webhook validation is disabled in development mode
- Never commit real API keys to version control
- Use environment variables for all secrets
- Enable webhook validation in production

## 🆘 Getting Help

When reporting development issues, include:

- **Environment**: OS, Python version, Node.js version
- **Configuration**: Sanitized .env file (remove secrets)
- **Logs**: Relevant log entries with timestamps
- **Steps to Reproduce**: Detailed reproduction steps

### Collect Diagnostic Information

```bash
echo "=== System Information ===" > debug.log
uname -a >> debug.log
python --version >> debug.log
node --version >> debug.log

echo "=== Configuration ===" >> debug.log
env | grep -E "^(OPENAI|TWILIO|LOG|MAX)" | sed 's/=.*/=***/' >> debug.log

echo "=== Recent Logs ===" >> debug.log
tail -100 server.log >> debug.log

echo "=== Health Check ===" >> debug.log
curl -s http://localhost:8000/health >> debug.log
```

---

This development guide provides everything needed for local development, testing, and debugging of the Reality Checker WhatsApp Bot.