# Reality Checker WhatsApp Bot Testing Guide

This guide provides comprehensive instructions for testing both the WhatsApp bot services and the real-time monitoring dashboard features of the Reality Checker application.

## Part 1: WhatsApp Bot Services Testing

### 1. Setting Up the Testing Environment

First, ensure you have the necessary environment variables set up:

```bash
# Create a .env file with required credentials
cp .env.example .env

# Edit the .env file with your test credentials
# Required variables:
# - OPENAI_API_KEY
# - TWILIO_ACCOUNT_SID
# - TWILIO_AUTH_TOKEN
# - TWILIO_PHONE_NUMBER
```

### 2. Unit Testing Individual Services

#### 2.1 Testing the Message Handler Service

The `MessageHandlerService` orchestrates the entire workflow:

```bash
# Run specific tests for the message handler
pytest tests/test_message_handler.py -v
```

Key test cases:

- Text message processing
- PDF message processing
- Help request handling
- Error handling scenarios
- Content validation

#### 2.2 Testing the OpenAI Analysis Service

The `OpenAIAnalysisService` handles job ad analysis:

```bash
# Run OpenAI analysis service tests
pytest tests/test_openai_analysis.py -v
```

Key test cases:

- Job ad analysis with different scenarios (legitimate, suspicious, scam)
- Error handling for API failures
- Response parsing and validation

#### 2.3 Testing the PDF Processing Service

The `PDFProcessingService` handles PDF downloads and text extraction:

```bash
# Run PDF processing tests
pytest tests/test_pdf_processing.py -v
```

Key test cases:

- PDF download functionality
- Text extraction from PDFs
- Error handling for corrupted files
- Size limit validation

#### 2.4 Testing the Twilio Response Service

The `TwilioResponseService` handles sending WhatsApp messages:

```bash
# Run Twilio response tests
pytest tests/test_twilio_response.py -v
```

Key test cases:

- Formatting analysis results
- Sending messages via Twilio
- Error handling for API failures
- Welcome message formatting

### 3. Integration Testing

#### 3.1 Testing the Webhook Endpoint

The webhook endpoint receives messages from Twilio:

```bash
# Run webhook integration tests
pytest tests/test_webhook.py -v
```

Key test cases:

- Signature validation
- Request parsing
- Error handling
- Integration with message handler

#### 3.2 End-to-End Testing

Test the complete flow from webhook to response:

```bash
# Run end-to-end tests
pytest tests/test_end_to_end.py -v
```

Key test cases:

- Complete flow for legitimate job postings
- Complete flow for suspicious job postings
- Complete flow for scam job postings
- PDF processing flow
- Error handling scenarios

### 4. Manual Testing with Twilio

For manual testing with real Twilio integration:

#### 4.1 Setting Up Twilio Webhook

1. Install ngrok to expose your local server:

   ```bash
   # Start ngrok on port 8000
   ngrok http 8000
   ```

2. Configure your Twilio WhatsApp Sandbox:
   - Go to Twilio Console > Messaging > Try it > WhatsApp
   - Set the webhook URL to your ngrok URL + `/webhook/whatsapp`
   - Example: `https://a1b2c3d4.ngrok.io/webhook/whatsapp`

#### 4.2 Starting the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --reload
```

#### 4.3 Manual Test Scenarios

1. **Text Message Testing**:

   - Send a legitimate job posting text to your Twilio WhatsApp number
   - Send a suspicious job posting text
   - Send a scam job posting text
   - Send "help" to test welcome message

2. **PDF Testing**:

   - Send a PDF with a legitimate job posting
   - Send a PDF with a suspicious job posting
   - Send a PDF with a scam job posting
   - Send a corrupted PDF to test error handling

3. **Error Scenario Testing**:
   - Send an unsupported file type (e.g., image)
   - Send a very short message to test validation
   - Send an extremely long message to test limits

### 5. Performance Testing

For testing performance and concurrency:

```bash
# Run performance tests
pytest tests/test_performance.py -v
```

Key metrics to monitor:

- Response time under load
- Error rates during concurrent requests
- Memory usage during extended operation

### 6. Security Testing

For testing security aspects:

```bash
# Run security tests
pytest tests/test_security.py -v
```

Key security aspects:

- Webhook signature validation
- Input sanitization
- Rate limiting
- Error handling without information leakage

## Part 2: Real-Time Monitoring Dashboard Testing

### 1. Backend Setup Verification

First, verify that the backend is properly set up for real-time monitoring:

- The WebSocket server implementation in `app/utils/websocket.py` is complete and should handle connections, broadcasting metrics, and alerts
- The monitoring API endpoints in `app/api/monitoring.py` are implemented for:
  - `/monitoring/ws` - WebSocket endpoint for real-time updates
  - `/monitoring/active-requests` - API for current processing requests
  - `/monitoring/error-rates` - API for error rate data
  - `/monitoring/response-times` - API for response time data
- The WebSocket alert handler is registered in `app/main.py`

### 2. Frontend Components Verification

The frontend components are properly implemented:

- `useWebSocket` hook in `dashboard/src/hooks/useWebSocket.ts` for WebSocket connection
- `MonitoringPage` component in `dashboard/src/pages/MonitoringPage.tsx` for the main monitoring page
- Four key monitoring components:
  - `LiveMetricsCard` - Shows real-time system metrics
  - `ActiveRequestsTable` - Displays currently processing requests
  - `ErrorRateChart` - Visualizes error rates over time
  - `ResponseTimeChart` - Tracks response times with percentiles
- The route to the monitoring page is correctly set up in `dashboard/src/App.tsx`

### 3. Manual Testing Steps

To manually test the dashboard:

1. **Start the Backend Server**:

   ```bash
   # Navigate to the project root
   cd /path/to/reality-checker-whatsapp-bot

   # Start the FastAPI server
   uvicorn app.main:app --reload
   ```

2. **Start the Frontend Development Server**:

   ```bash
   # Navigate to the dashboard directory
   cd /path/to/reality-checker-whatsapp-bot/dashboard

   # Start the React development server
   npm run build
   npm start
   ```

3. **Access the Dashboard**:

   - Open your browser and navigate to `http://localhost:3000`
   - Log in with valid credentials
   - Navigate to the Monitoring page

4. **Test WebSocket Connection**:

   - Check the browser console for WebSocket connection messages
   - Verify that the "WebSocket Connected" status appears on the monitoring page
   - The LiveMetricsCard should update automatically every 5 seconds

5. **Test Real-Time Updates**:

   - Make some API requests to the backend to generate metrics
   - Verify that the metrics update in real-time on the dashboard
   - The charts should update with new data points

6. **Test Alert Notifications**:
   - Trigger an error in the backend (e.g., make an invalid API request)
   - Verify that an alert notification appears on the dashboard

### 4. Specific Features to Test

1. **LiveMetricsCard**:

   - Should display current request count, error rate, and response time
   - Should update automatically with new data
   - Should show service health status for each service

2. **ActiveRequestsTable**:

   - Should display currently processing requests
   - Should show request type, status, duration, and user
   - Should update as new requests come in and existing ones complete

3. **ErrorRateChart**:

   - Should display error rate over time
   - Should update with new data points
   - Should show both error rate percentage and error count

4. **ResponseTimeChart**:

   - Should display response time over time
   - Should show average, 95th percentile, and 99th percentile
   - Should update with new data points

5. **Alert Notifications**:
   - Should appear when critical events occur
   - Should display severity, title, and message
   - Should be dismissable

### 5. Troubleshooting Common Issues

If you encounter issues during testing:

1. **WebSocket Connection Issues**:

   - Check that CORS is properly configured in the backend
   - Verify that the WebSocket URL is correct (ws:// for HTTP, wss:// for HTTPS)
   - Check browser console for connection errors

2. **No Real-Time Updates**:

   - Verify that the WebSocket manager's broadcast task is running
   - Check that metrics are being collected in the backend
   - Ensure the frontend is correctly processing WebSocket messages

3. **Chart Data Issues**:

   - Verify that the data format matches what the charts expect
   - Check that timestamps are properly formatted
   - Ensure data arrays aren't growing too large (should be limited to ~20 points)

4. **Authentication Issues**:
   - Verify that the token is being passed correctly in WebSocket connection
   - Check that API endpoints are properly validating authentication

### 6. Expected Behavior

When everything is working correctly:

- The monitoring page should load with initial data
- The WebSocket connection should establish automatically
- Metrics should update every 5 seconds without page refresh
- Charts should show smooth transitions as new data arrives
- Alert notifications should appear promptly when triggered
- The UI should remain responsive and performant

### 7. Generating Test Data

To generate test data for the monitoring dashboard:

1. **Generate Request Metrics**:

   ```bash
   # Make multiple API requests to generate metrics
   curl http://localhost:8000/health
   curl http://localhost:8000/health/detailed
   curl http://localhost:8000/health/metrics
   ```

2. **Generate Errors**:

   ```bash
   # Make invalid requests to generate errors
   curl http://localhost:8000/nonexistent-endpoint
   curl -X POST http://localhost:8000/health
   ```

3. **Simulate Service Calls**:
   - Use the application normally to generate service calls
   - Or create a test script that makes multiple API calls to external services

### 8. Performance Testing

To test the performance of the real-time monitoring:

1. **Connection Handling**:

   - Open multiple browser tabs with the monitoring dashboard
   - Verify that all instances receive updates correctly

2. **Data Volume**:

   - Generate a large volume of metrics data
   - Verify that the dashboard remains responsive
   - Check that charts handle large datasets appropriately

3. **Long-Running Connection**:
   - Keep the dashboard open for an extended period (hours)
   - Verify that the WebSocket connection remains stable
   - Check that memory usage doesn't increase significantly over time

## Part 3: Comprehensive Testing

### 1. Integrated System Testing

Test the complete system with both WhatsApp bot and dashboard components:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app
```

### 2. Monitoring WhatsApp Bot Activity

1. Start both the backend and frontend servers
2. Send test messages to the WhatsApp bot
3. Observe the real-time updates on the monitoring dashboard
4. Verify that user interactions appear in the user management section
5. Check that error rates and response times are accurately tracked

### 3. Troubleshooting Common Issues

If you encounter issues during testing:

1. **OpenAI API Issues**:

   - Check API key validity
   - Verify rate limits
   - Check for model availability

2. **Twilio API Issues**:

   - Verify account SID and auth token
   - Check WhatsApp sandbox status
   - Verify webhook URL configuration

3. **PDF Processing Issues**:

   - Check PDF file format and encoding
   - Verify size limits
   - Check for text extraction capabilities

4. **WebSocket Connection Issues**:
   - Verify CORS configuration
   - Check authentication token
   - Ensure proper WebSocket URL format

By following this comprehensive testing approach, you can ensure that all components of the Reality Checker application function correctly according to the requirements and design specifications.
