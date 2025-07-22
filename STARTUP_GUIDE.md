# 🚀 WhatsApp Bot Startup Guide

## Simple Setup - Choose Your Mode

### 🔧 Development Mode (Recommended)
```bash
./dev.sh
```
**What it does:**
- Starts FastAPI server with auto-reload
- Starts ngrok tunnel for webhook
- Shows webhook URL for Twilio configuration
- Copies webhook URL to clipboard (macOS)

**Use when:** Daily development and testing

### 📊 Full Development (API + Dashboard)
```bash
./start.sh
```
**What it does:**
- Everything from dev.sh PLUS:
- React dashboard on port 3000
- Redis (if available)
- Full monitoring setup

**Use when:** You need the web dashboard

### 🚀 Production Mode
```bash
./prod.sh
```
**What it does:**
- Starts FastAPI with multiple workers
- No ngrok (uses your production domain)
- Production environment variables

**Use when:** Deploying to production server

## 📋 Quick Setup

1. **For daily development:**
   ```bash
   ./dev.sh
   ```

2. **Copy the webhook URL from terminal**

3. **Configure in Twilio Console:**
   - Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
   - Paste webhook URL in "When a message comes in"
   - Set method to POST

4. **Test with WhatsApp**

## 🛑 Stop Services
Press `Ctrl+C` in any running script

## 🔧 Troubleshooting

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**ngrok not working:**
```bash
# Check if ngrok is installed
which ngrok

# Install if missing (macOS)
brew install ngrok
```

That's it! No more confusion with multiple scripts.