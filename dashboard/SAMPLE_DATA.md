# Reality Checker Dashboard - Sample Data Reference

## Authentication Test Accounts

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Admin
- **Features**: Full access including Configuration menu, system alerts, all dashboard features

### Analyst Accounts
- **Username**: `analyst`
- **Password**: `analyst123`
- **Role**: Analyst
- **Features**: Dashboard, Analytics, Monitoring, Reports (no Configuration access)

- **Username**: `demo`
- **Password**: `demo123`
- **Role**: Analyst
- **Features**: Same as analyst, demo account for testing

## Dashboard Sample Data

### Real-time Metrics (Updates every 10 seconds)
- **Total Requests**: 1,250-1,350 (base + random variation)
- **Requests Today**: 30-80 requests
- **Error Rate**: 1.0-4.0% (triggers admin alerts if >2.5%)
- **Active Users**: 15-30 users
- **System Status**: 
  - `healthy` (green) when error rate < 2%
  - `warning` (orange) when error rate 2-3%
  - `critical` (red) when error rate > 3%

### Quick Stats
- **Average Response Time**: 1.2s (static)
- **Success Rate**: Calculated as (100 - error rate)%
- **Peak Hour**: 2:00 PM (static)
- **Server Uptime**: 99.9% (static)

### Recent Activity (Static Sample)
- WhatsApp message processed: Job posting analysis
- PDF document uploaded and analyzed
- User authentication successful
- System health check completed
- Analytics report generated

## Analytics Sample Data

### Key Metrics (Updates every 30 seconds)
- **Classification Accuracy**: 85-95%
- **Total Analyses**: 2,500-3,000
- **Weekly Growth**: 5-25%

### Analysis Categories
1. **Job Postings**: ~800-1000 requests (45%)
2. **Scam Detection**: ~600-750 requests (32%)
3. **Document Analysis**: ~300-400 requests (15%)
4. **General Inquiry**: ~150-230 requests (8%)

### User Engagement
- **Daily Active Users**: 40-60 users
- **Average Session Time**: 3-8 minutes
- **Return Rate**: 70-85%

### System Performance
- **Average Response Time**: 0.5-1.3 seconds
- **Success Rate**: 95-100%
- **System Uptime**: 99.5-100%

### Recent Insights (Static Sample)
- Job posting detection accuracy improved by 3%
- Peak usage hours: 2-4 PM weekdays
- Scam detection requests increased 15%
- New user onboarding rate: 85%
- Most common query: Job legitimacy check

## Role-Based Features

### Admin-Only Features
- **Configuration Menu**: Visible only to admin users
- **System Alerts**: Warning alerts when error rate > 2.5%
- **Full Access**: All dashboard sections and settings

### Analyst Features
- **Dashboard**: System metrics and real-time monitoring
- **Analytics**: Usage statistics and performance metrics
- **Monitoring**: Real-time system health (placeholder)
- **Reports**: Generate and export reports (placeholder)
- **No Configuration**: Cannot access system settings

## Testing Scenarios

### 1. Authentication Flow
```
1. Visit http://localhost:3000
2. Should redirect to /login
3. Try invalid credentials → See error message
4. Login with admin/admin123 → Redirect to dashboard
5. Logout → Redirect back to login
```

### 2. Role-Based Access
```
1. Login as analyst/analyst123
2. Configuration menu should NOT be visible
3. Try direct URL /config → Should redirect/show unauthorized
4. Login as admin/admin123
5. Configuration menu should be visible
```

### 3. Real-Time Updates
```
1. Login and go to Dashboard
2. Watch metrics update every 10 seconds
3. Watch for error rate > 2.5% to trigger admin alert
4. Go to Analytics page
5. Watch metrics update every 30 seconds
```

### 4. Session Persistence
```
1. Login with any account
2. Refresh page → Should stay logged in
3. Close and reopen browser → Should stay logged in
4. Logout → Should clear session
```

## Quick Start Testing

1. **Start the server**:
   ```bash
   cd dashboard
   npm start
   ```

2. **Test admin features**:
   - Login: `admin` / `admin123`
   - Check all menu items are visible
   - Wait for high error rate alert

3. **Test analyst features**:
   - Login: `analyst` / `analyst123`
   - Verify Configuration menu is hidden
   - Test dashboard and analytics pages

4. **Test real-time updates**:
   - Watch dashboard metrics change every 10 seconds
   - Watch analytics data change every 30 seconds
   - Check system status color changes

## Data Refresh Intervals

- **Dashboard Metrics**: Every 10 seconds
- **Analytics Data**: Every 30 seconds
- **System Status**: Based on current error rate
- **Last Updated Time**: Shows current time on each refresh

## Color Coding

### System Status
- 🟢 **Green (Healthy)**: Error rate < 2%
- 🟡 **Orange (Warning)**: Error rate 2-3%
- 🔴 **Red (Critical)**: Error rate > 3%

### Metrics
- **Primary Blue**: Total requests, main metrics
- **Success Green**: Positive metrics, success rates
- **Warning Orange**: Caution metrics, moderate values
- **Error Red**: Critical metrics, high error rates
- **Info Blue**: Informational metrics, neutral values