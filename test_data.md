# Reality Checker WhatsApp Bot - Test Data

## 🧪 Development Testing Guide

### 1. Health Check Test
**URL**: http://localhost:8000/health
**Method**: GET
**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-15T18:05:46.842152+00:00",
  "services": {
    "openai": "connected",
    "twilio": "connected", 
    "pdf_processing": "ready"
  },
  "version": "1.0.0",
  "uptime": "running"
}
```

### 2. Webhook GET Test
**URL**: http://localhost:8000/webhook/whatsapp
**Method**: GET
**Expected Response**:
```json
{
  "status": "active",
  "message": "WhatsApp webhook endpoint is operational",
  "methods": "POST"
}
```

### 3. Webhook POST Test (Simulating WhatsApp Messages)

#### Test Case 1: Text Message - Legitimate Job
**URL**: http://localhost:8000/webhook/whatsapp
**Method**: POST
**Content-Type**: application/x-www-form-urlencoded
**Body**:
```
MessageSid=SM1234567890abcdef1234567890abcdef
From=whatsapp:+15551234567
To=whatsapp:+17087405918
Body=Software Engineer position at Google. Full-time remote work. Salary: $120,000-$150,000. Requirements: 3+ years Python experience, Bachelor's degree in Computer Science. Contact: hr@google.com for application details.
NumMedia=0
```

#### Test Case 2: Text Message - Suspicious Job
**URL**: http://localhost:8000/webhook/whatsapp
**Method**: POST
**Content-Type**: application/x-www-form-urlencoded
**Body**:
```
MessageSid=SM2234567890abcdef1234567890abcdef
From=whatsapp:+15551234567
To=whatsapp:+17087405918
Body=URGENT! Make $5000/week working from home! No experience needed! Just send $99 registration fee to get started immediately! Contact WhatsApp: +1234567890
NumMedia=0
```

#### Test Case 3: Text Message - Likely Scam
**URL**: http://localhost:8000/webhook/whatsapp
**Method**: POST
**Content-Type**: application/x-www-form-urlencoded
**Body**:
```
MessageSid=SM3234567890abcdef1234567890abcdef
From=whatsapp:+15551234567
To=whatsapp:+17087405918
Body=Congratulations! You've been selected for a $10,000/month data entry job! Send your SSN, bank details, and $200 processing fee to secure your position today!
NumMedia=0
```

#### Test Case 4: Help Request
**URL**: http://localhost:8000/webhook/whatsapp
**Method**: POST
**Content-Type**: application/x-www-form-urlencoded
**Body**:
```
MessageSid=SM4234567890abcdef1234567890abcdef
From=whatsapp:+15551234567
To=whatsapp:+17087405918
Body=help
NumMedia=0
```

#### Test Case 5: Short Invalid Message
**URL**: http://localhost:8000/webhook/whatsapp
**Method**: POST
**Content-Type**: application/x-www-form-urlencoded
**Body**:
```
MessageSid=SM5234567890abcdef1234567890abcdef
From=whatsapp:+15551234567
To=whatsapp:+17087405918
Body=hi
NumMedia=0
```

#### Test Case 6: PDF Media Message
**URL**: http://localhost:8000/webhook/whatsapp
**Method**: POST
**Content-Type**: application/x-www-form-urlencoded
**Body**:
```
MessageSid=SM6234567890abcdef1234567890abcdef
From=whatsapp:+15551234567
To=whatsapp:+17087405918
Body=
NumMedia=1
MediaUrl0=https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
MediaContentType0=application/pdf
```

### 4. cURL Commands for Terminal Testing

#### Health Check:
```bash
curl -X GET http://localhost:8000/health
```

#### Webhook GET:
```bash
curl -X GET http://localhost:8000/webhook/whatsapp
```

#### Legitimate Job Test:
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=SM1234567890abcdef1234567890abcdef&From=whatsapp:+15551234567&To=whatsapp:+17087405918&Body=Software Engineer position at Google. Full-time remote work. Salary: $120,000-$150,000. Requirements: 3+ years Python experience, Bachelor's degree in Computer Science. Contact: hr@google.com for application details.&NumMedia=0"
```

#### Scam Job Test:
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=SM2234567890abcdef1234567890abcdef&From=whatsapp:+15551234567&To=whatsapp:+17087405918&Body=URGENT! Make $5000/week working from home! No experience needed! Just send $99 registration fee to get started immediately! Contact WhatsApp: +1234567890&NumMedia=0"
```

#### Help Request Test:
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "MessageSid=SM4234567890abcdef1234567890abcdef&From=whatsapp:+15551234567&To=whatsapp:+17087405918&Body=help&NumMedia=0"
```

### 5. Expected Behaviors

#### For Legitimate Jobs:
- Trust Score: 70-100
- Classification: "Legit"
- Response includes positive indicators

#### For Suspicious Jobs:
- Trust Score: 30-69
- Classification: "Suspicious" 
- Response includes warning signs

#### For Scam Jobs:
- Trust Score: 0-29
- Classification: "Likely Scam"
- Response includes strong warnings

#### For Help Requests:
- Welcome message with usage instructions

#### For Invalid Content:
- Error message asking for more detailed job information

### 6. Monitoring Logs

Watch the terminal where you started the server to see:
- Request processing logs
- Service health status
- Error handling
- Response generation

### 7. Testing with Postman/Insomnia

Import these requests into Postman or Insomnia for easier testing:
- Set base URL: http://localhost:8000
- Use the endpoints and data provided above
- Check response status codes and JSON responses