# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Reality Checker WhatsApp Bot.

## 🚨 Quick Diagnostics

### Health Check Commands

```bash
# Check application health
curl http://localhost:8000/health

# Check specific services
curl http://localhost:8000/api/health/openai
curl http://localhost:8000/api/health/twilio

# Check logs
tail -f logs/app.log

# Check Docker container status
docker ps
docker logs reality-checker-app
```

### Configuration Validation

```bash
# Validate environment configuration
python -c "
from app.config import get_config
try:
    config = get_config()
    print('✅ Configuration loaded successfully')
    print(f'OpenAI Model: {config.openai_model}')
    print(f'Log Level: {config.log_level}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"

# Check required environment variables
python -c "
import os
required_vars = ['OPENAI_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'❌ Missing required variables: {missing}')
else:
    print('✅ All required environment variables are set')
"
```

## 🔧 Common Issues and Solutions

### 1. Application Startup Issues

#### Issue: Application fails to start

**Symptoms:**
- Application exits immediately
- "Configuration error" messages
- Import errors

**Diagnosis:**
```bash
# Check Python environment
python --version
pip list | grep -E "(fastapi|uvicorn|openai|twilio)"

# Check configuration
python -c "from app.config import get_config; get_config()"

# Check for missing dependencies
pip install -r requirements.txt
```

**Solutions:**

1. **Missing Environment Variables:**
```bash
# Copy and configure environment file
cp .env.example .env
# Edit .env with your actual values
nano .env
```

2. **Invalid API Keys:**
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test Twilio credentials
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json" \
     -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN
```

3. **Python Path Issues:**
```bash
# Ensure app module is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "import app.main"
```

#### Issue: Port already in use

**Symptoms:**
- "Address already in use" error
- Cannot bind to port 8000

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000
netstat -tulpn | grep :8000

# Kill process using port
kill -9 <PID>

# Use different port
uvicorn app.main:app --port 8001
```

### 2. OpenAI API Issues

#### Issue: OpenAI API errors

**Symptoms:**
- "OpenAI API error" in logs
- Analysis requests failing
- Rate limit errors

**Diagnosis:**
```bash
# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-4","messages":[{"role":"user","content":"test"}],"max_tokens":10}' \
     https://api.openai.com/v1/chat/completions

# Check API key format
echo $OPENAI_API_KEY | grep -E "^sk-[a-zA-Z0-9]{48}$"
```

**Solutions:**

1. **Invalid API Key:**
```bash
# Verify API key is correct
# Get new key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY=sk-your-new-key
```

2. **Rate Limiting:**
```bash
# Check usage and limits
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/usage

# Implement exponential backoff in code
# Or upgrade OpenAI plan
```

3. **Model Access Issues:**
```bash
# List available models
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Use available model
export OPENAI_MODEL=gpt-3.5-turbo
```

4. **Network Connectivity:**
```bash
# Test network connectivity
ping api.openai.com
nslookup api.openai.com

# Check firewall rules
# Ensure outbound HTTPS (443) is allowed
```

### 3. Twilio Integration Issues

#### Issue: WhatsApp messages not received

**Symptoms:**
- Webhook endpoint not called
- Messages sent but no response
- Twilio webhook errors

**Diagnosis:**
```bash
# Test webhook endpoint locally
curl -X POST http://localhost:8000/webhook/whatsapp \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "From=+1234567890&To=+0987654321&Body=test message"

# Check Twilio webhook configuration
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers.json" \
     -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN
```

**Solutions:**

1. **Webhook URL Not Accessible:**
```bash
# For local development, use ngrok
ngrok http 8000
# Update Twilio webhook URL to ngrok URL

# For production, ensure public accessibility
curl -I https://your-domain.com/webhook/whatsapp
```

2. **Invalid Twilio Credentials:**
```bash
# Verify credentials
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json" \
     -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN

# Check phone number configuration
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/IncomingPhoneNumbers.json" \
     -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN
```

3. **Webhook Signature Validation:**
```bash
# Disable validation for testing
export WEBHOOK_VALIDATION=false

# Or implement proper signature validation
# See Twilio documentation for signature validation
```

#### Issue: Cannot send WhatsApp messages

**Symptoms:**
- Outbound messages fail
- "Forbidden" or "Unauthorized" errors
- WhatsApp sandbox issues

**Solutions:**

1. **WhatsApp Sandbox Setup:**
```bash
# Join WhatsApp sandbox
# Send "join <sandbox-keyword>" to your Twilio WhatsApp number
# Example: "join reality-checker"
```

2. **Phone Number Format:**
```bash
# Ensure proper E.164 format
export TWILIO_PHONE_NUMBER="+1234567890"  # Include country code with +
```

3. **Account Verification:**
```bash
# Check account status
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json" \
     -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN | jq '.status'
```

### 4. PDF Processing Issues

#### Issue: PDF processing failures

**Symptoms:**
- "Could not process PDF" errors
- Empty text extraction
- Download failures

**Diagnosis:**
```bash
# Test PDF processing manually
python -c "
from app.services.pdf_processing import PDFProcessingService
import asyncio

async def test_pdf():
    service = PDFProcessingService()
    # Test with a sample PDF URL
    text = await service.extract_text_from_url('https://example.com/sample.pdf')
    print(f'Extracted text length: {len(text)}')

asyncio.run(test_pdf())
"
```

**Solutions:**

1. **PDF Size Limits:**
```bash
# Check file size
curl -I https://example.com/sample.pdf | grep -i content-length

# Increase size limit
export MAX_PDF_SIZE_MB=20
```

2. **PDF Format Issues:**
```bash
# Test PDF manually
wget https://example.com/sample.pdf
python -c "
import pdfplumber
with pdfplumber.open('sample.pdf') as pdf:
    text = ''.join(page.extract_text() or '' for page in pdf.pages)
    print(f'Text length: {len(text)}')
"
```

3. **Network Access Issues:**
```bash
# Test URL accessibility
curl -I https://example.com/sample.pdf

# Check for authentication requirements
# Ensure PDF URLs are publicly accessible
```

### 5. Dashboard Access Issues

#### Issue: Cannot access admin dashboard

**Symptoms:**
- Login page not loading
- Authentication failures
- 404 errors on dashboard routes

**Diagnosis:**
```bash
# Check if dashboard is built
ls -la dashboard/build/

# Test authentication endpoint
curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'

# Check static file serving
curl -I http://localhost:8000/admin
```

**Solutions:**

1. **Dashboard Not Built:**
```bash
cd dashboard
npm install
npm run build
cd ..
```

2. **Authentication Issues:**
```bash
# Check admin credentials
echo "Username: $ADMIN_USERNAME"
echo "Password: $ADMIN_PASSWORD"

# Reset admin password
python -c "
from app.services.authentication import AuthenticationService
auth = AuthenticationService()
hashed = auth.hash_password('new_password')
print(f'Hashed password: {hashed}')
"
```

3. **JWT Configuration:**
```bash
# Check JWT secret
echo "JWT Secret length: ${#JWT_SECRET_KEY}"

# Generate new JWT secret
python -c "
import secrets
print(f'New JWT secret: {secrets.token_urlsafe(32)}')
"
```

### 6. Database Issues

#### Issue: Database connection failures

**Symptoms:**
- "Database connection error"
- Migration failures
- Data not persisting

**Diagnosis:**
```bash
# Test database connection
python -c "
from app.database.database import get_database
import asyncio

async def test_db():
    try:
        db = get_database()
        result = await db.execute('SELECT 1')
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database error: {e}')

asyncio.run(test_db())
"
```

**Solutions:**

1. **SQLite Issues:**
```bash
# Check database file permissions
ls -la data/reality_checker.db

# Create data directory
mkdir -p data
chmod 755 data

# Initialize database
python manage_db.py init
```

2. **PostgreSQL Issues:**
```bash
# Test PostgreSQL connection
psql $DATABASE_URL -c "SELECT version();"

# Check connection parameters
echo $DATABASE_URL
```

3. **Migration Issues:**
```bash
# Check migration status
alembic current

# Apply pending migrations
alembic upgrade head

# Reset migrations (CAUTION: destroys data)
alembic downgrade base
alembic upgrade head
```

### 7. Performance Issues

#### Issue: Slow response times

**Symptoms:**
- High response times (>5 seconds)
- Timeouts
- High CPU/memory usage

**Diagnosis:**
```bash
# Check system resources
top
htop
docker stats

# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# curl-format.txt content:
#     time_namelookup:  %{time_namelookup}\n
#        time_connect:  %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#    time_pretransfer:  %{time_pretransfer}\n
#       time_redirect:  %{time_redirect}\n
#  time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#          time_total:  %{time_total}\n
```

**Solutions:**

1. **Resource Optimization:**
```bash
# Increase container resources
docker run --memory=1g --cpus=2 reality-checker:latest

# Optimize Python settings
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

2. **Database Optimization:**
```bash
# Add database indexes
# Check slow queries
# Optimize database configuration
```

3. **Caching:**
```bash
# Enable Redis caching
export REDIS_URL=redis://localhost:6379/0

# Configure cache TTL
export CACHE_TTL=300
```

### 8. Memory Issues

#### Issue: High memory usage or memory leaks

**Symptoms:**
- Gradually increasing memory usage
- Out of memory errors
- Container restarts

**Diagnosis:**
```bash
# Monitor memory usage
docker stats reality-checker-app

# Check Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Profile memory usage
pip install memory-profiler
python -m memory_profiler app/main.py
```

**Solutions:**

1. **Optimize Code:**
```python
# Use generators instead of lists
# Close file handles properly
# Clear large variables when done
```

2. **Container Limits:**
```bash
# Set memory limits
docker run --memory=512m reality-checker:latest

# Monitor and adjust limits
docker update --memory=1g reality-checker-app
```

3. **Garbage Collection:**
```python
# Force garbage collection
import gc
gc.collect()

# Tune garbage collection
import gc
gc.set_threshold(700, 10, 10)
```

## 🔍 Debugging Tools

### Log Analysis

```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep -i error logs/app.log

# Filter by correlation ID
grep "correlation_id=abc123" logs/app.log

# Analyze log patterns
awk '/ERROR/ {print $1, $2, $NF}' logs/app.log | sort | uniq -c
```

### Network Debugging

```bash
# Test network connectivity
ping api.openai.com
ping api.twilio.com

# Check DNS resolution
nslookup api.openai.com
dig api.openai.com

# Test HTTPS connectivity
openssl s_client -connect api.openai.com:443

# Check firewall rules
iptables -L
ufw status
```

### Database Debugging

```bash
# SQLite debugging
sqlite3 data/reality_checker.db ".tables"
sqlite3 data/reality_checker.db ".schema users"

# PostgreSQL debugging
psql $DATABASE_URL -c "\dt"
psql $DATABASE_URL -c "\d users"

# Check database locks
psql $DATABASE_URL -c "SELECT * FROM pg_locks;"
```

## 📊 Monitoring and Alerting

### Health Monitoring

```bash
# Continuous health monitoring
while true; do
    curl -s http://localhost:8000/health | jq '.status'
    sleep 30
done

# Monitor specific services
curl -s http://localhost:8000/health | jq '.services'
```

### Performance Monitoring

```bash
# Monitor response times
ab -n 100 -c 10 http://localhost:8000/health

# Load testing
wrk -t12 -c400 -d30s http://localhost:8000/health
```

### Log Monitoring

```bash
# Monitor error rates
tail -f logs/app.log | grep -i error | wc -l

# Real-time log analysis
tail -f logs/app.log | grep -E "(ERROR|CRITICAL)"
```

## 🆘 Emergency Procedures

### Service Recovery

```bash
# Quick restart
docker restart reality-checker-app

# Full restart with cleanup
docker stop reality-checker-app
docker rm reality-checker-app
docker run -d --name reality-checker-app \
  --env-file .env \
  -p 8000:8000 \
  reality-checker:latest
```

### Data Recovery

```bash
# Restore from backup
cp backup/reality_checker.db data/reality_checker.db

# Restore logs
cp -r backup/logs/* logs/
```

### Rollback Procedures

```bash
# Docker rollback
docker stop reality-checker-app
docker run -d --name reality-checker-app \
  --env-file .env \
  -p 8000:8000 \
  reality-checker:previous-version

# Kubernetes rollback
kubectl rollout undo deployment/reality-checker
```

## 📞 Getting Help

### Support Channels

1. **Documentation**: Check README.md and API docs
2. **GitHub Issues**: Report bugs and feature requests
3. **Logs**: Always include relevant log excerpts
4. **Configuration**: Share sanitized configuration (remove secrets)

### Information to Include

When reporting issues, include:

- **Environment**: OS, Python version, Docker version
- **Configuration**: Sanitized .env file
- **Logs**: Relevant log entries with timestamps
- **Steps to Reproduce**: Detailed reproduction steps
- **Expected vs Actual**: What you expected vs what happened

### Log Collection

```bash
# Collect diagnostic information
echo "=== System Information ===" > debug.log
uname -a >> debug.log
python --version >> debug.log
docker --version >> debug.log

echo "=== Configuration ===" >> debug.log
env | grep -E "^(OPENAI|TWILIO|LOG|MAX)" | sed 's/=.*/=***/' >> debug.log

echo "=== Recent Logs ===" >> debug.log
tail -100 logs/app.log >> debug.log

echo "=== Health Check ===" >> debug.log
curl -s http://localhost:8000/health >> debug.log
```

---

This troubleshooting guide covers the most common issues you may encounter. For additional help, please refer to the documentation or contact support with detailed information about your issue.