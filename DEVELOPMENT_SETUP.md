# 🚀 WhatsApp Bot Development Setup

This guide provides multiple ways to start your WhatsApp bot development environment with automatic webhook configuration.

## 📋 Prerequisites

- Python 3.11+
- ngrok installed (`brew install ngrok` on macOS)
- Twilio account with WhatsApp sandbox access
- OpenAI API key

## 🛠️ Available Startup Scripts

### 1. Enhanced Development Script (Recommended)
```bash
./start_dev.sh
```

**Features:**
- ✅ Comprehensive dependency checking
- ✅ Automatic service startup (FastAPI + ngrok)
- ✅ Health monitoring
- ✅ Colored terminal output
- ✅ Webhook URL generation and display
- ✅ Configuration file generation
- ✅ Service monitoring

**Output includes:**
- Service URLs (local and public)
- Webhook configuration instructions
- Testing guidelines
- Real-time status updates

### 2. Quick Start Script (Fast Testing)
```bash
./quick_start.sh
```

**Features:**
- ⚡ Minimal setup for rapid testing
- 🔗 Automatic webhook URL generation
- 📋 Clipboard integration (macOS)
- 🎯 Essential services only

### 3. Original Start Script (Full Environment)
```bash
./start.sh
```

**Features:**
- 📊 Includes React dashboard
- 🔴 Redis integration
- 🔧 Full development environment
- 🌐 Automatic webhook configuration

### 4. Manual Webhook Configuration
```bash
python3 auto_webhook_config.py
```

**Use when:**
- Services are already running
- Need to update webhook URL
- ngrok URL changed

## 🔧 Configuration Process

### Automatic Setup (Recommended)
1. Run any startup script
2. Copy the webhook URL from terminal output
3. Go to [Twilio Console](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)
4. Paste webhook URL in "When a message comes in"
5. Set method to POST and save

### Manual Setup
1. Start services: `./quick_start.sh`
2. Get webhook URL from terminal
3. Configure in Twilio console manually

## 📱 Testing Your Bot

### Join WhatsApp Sandbox
1. Go to Twilio Console WhatsApp sandbox
2. Note your join code (e.g., "join abc123")
3. Send this to `+1 415 523 8886` from WhatsApp
4. Wait for confirmation

### Test Messages
```
# Help command
help

# Scam detection test
Software Engineer position at Google. Salary 200k. Send 500 dollars for background check to secure position.

# Legitimate job test
Senior Software Engineer at Microsoft. 5+ years experience required. Competitive salary and benefits. Apply through our careers page.
```

## 📊 Monitoring and Debugging

### Service URLs
- **Local API**: http://localhost:8000
- **Public API**: https://[random].ngrok-free.app
- **API Docs**: https://[random].ngrok-free.app/docs
- **Health Check**: https://[random].ngrok-free.app/health
- **ngrok Dashboard**: http://localhost:4040

### Log Files
```bash
# Server logs
tail -f server.log

# ngrok logs
tail -f ngrok.log

# Real-time monitoring
curl -s http://localhost:8000/health | python3 -m json.tool
```

### Common Issues

**Port Already in Use**
```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9
lsof -ti:4040 | xargs kill -9
```

**ngrok URL Not Found**
```bash
# Check ngrok status
curl -s http://localhost:4040/api/tunnels | python3 -m json.tool

# Or try alternative port
curl -s http://localhost:4041/api/tunnels | python3 -m json.tool
```

**Webhook 401 Errors**
- Ensure `WEBHOOK_VALIDATION=false` in .env for development
- Check Twilio webhook URL matches exactly

## 🔄 Development Workflow

### Daily Development
```bash
# Start everything
./start_dev.sh

# Make code changes (auto-reload enabled)
# Test in WhatsApp

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

### Production Preparation
```bash
# Set environment variables
WEBHOOK_VALIDATION=true
DEVELOPMENT_MODE=false

# Deploy to cloud platform
# Configure production webhook URL
```

## 📁 Generated Files

The scripts create several files for easy access:

- `webhook_config.txt` - Current configuration
- `current_webhook_config.json` - JSON configuration
- `server.log` - FastAPI server logs
- `ngrok.log` - ngrok tunnel logs

## 🎯 Pro Tips

1. **Bookmark Twilio Console**: Keep the sandbox page open for quick webhook updates
2. **Use Quick Start**: For rapid iteration during development
3. **Monitor Logs**: Keep `tail -f server.log` open in a separate terminal
4. **Test Incrementally**: Start with "help" command, then test scam detection
5. **Clipboard Integration**: Webhook URLs are auto-copied on macOS

## 🔒 Security Notes

- Webhook validation is disabled in development mode
- Never commit real API keys to version control
- Use environment variables for all secrets
- Enable webhook validation in production

## 🆘 Troubleshooting

### Services Won't Start
1. Check Python version: `python3 --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Verify .env file exists and has required variables

### Webhook Not Receiving Messages
1. Verify ngrok URL is accessible: `curl [ngrok-url]/health`
2. Check Twilio console webhook configuration
3. Ensure phone number is joined to sandbox

### Bot Not Responding
1. Check server logs: `tail -f server.log`
2. Verify OpenAI API key is valid
3. Test health endpoint: `curl [ngrok-url]/health`

Need help? Check the logs first, then review the configuration files generated by the startup scripts.