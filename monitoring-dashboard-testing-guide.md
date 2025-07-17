# Real-Time Monitoring Dashboard Testing Guide

This guide provides instructions for testing the real-time monitoring dashboard features of the Reality Checker WhatsApp Bot.

## 1. Backend Setup Verification

First, verify that the backend is properly set up for real-time monitoring:

- The WebSocket server implementation in `app/utils/websocket.py` is complete and should handle connections, broadcasting metrics, and alerts
- The monitoring API endpoints in `app/api/monitoring.py` are implemented for:
  - `/monitoring/ws` - WebSocket endpoint for real-time updates
  - `/monitoring/active-requests` - API for current processing requests
  - `/monitoring/error-rates` - API for error rate data
  - `/monitoring/response-times` - API for response time data
- The WebSocket alert handler is registered in `app/main.py`

## 2. Frontend Components Verification

The frontend components are properly implemented:

- `useWebSocket` hook in `dashboard/src/hooks/useWebSocket.ts` for WebSocket connection
- `MonitoringPage` component in `dashboard/src/pages/MonitoringPage.tsx` for the main monitoring page
- Four key monitoring components:
  - `LiveMetricsCard` - Shows real-time system metrics
  - `ActiveRequestsTable` - Displays currently processing requests
  - `ErrorRateChart` - Visualizes error rates over time
  - `ResponseTimeChart` - Tracks response times with percentiles
- The route to the monitoring page is correctly set up in `dashboard/src/App.tsx`

## 3. Manual Testing Steps

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

## 4. Specific Features to Test

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

## 5. Troubleshooting Common Issues

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

## 6. Expected Behavior

When everything is working correctly:

- The monitoring page should load with initial data
- The WebSocket connection should establish automatically
- Metrics should update every 5 seconds without page refresh
- Charts should show smooth transitions as new data arrives
- Alert notifications should appear promptly when triggered
- The UI should remain responsive and performant

## 7. Generating Test Data

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

## 8. Performance Testing

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

By following these testing steps, you can verify that all the newly added real-time monitoring features are working correctly.
