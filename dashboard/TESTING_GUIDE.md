# Reality Checker Dashboard - Testing Guide

## Sample Authentication Data

The dashboard includes mock authentication for testing purposes. Use these credentials to test different user roles:

### Test Accounts

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| `admin` | `admin123` | Admin | Full access to all features including configuration |
| `analyst` | `analyst123` | Analyst | Access to dashboards, analytics, and reports |
| `demo` | `demo123` | Analyst | Demo account for testing analyst features |

## Testing Instructions

### 1. Start the Development Server

```bash
cd dashboard
npm start
```

The application will open at [http://localhost:3000](http://localhost:3000)

### 2. Test Authentication Flow

1. **Login Page**: You'll be redirected to `/login` if not authenticated
2. **Try Invalid Credentials**: Test error handling with wrong username/password
3. **Login with Admin**: Use `admin` / `admin123` to test admin features
4. **Login with Analyst**: Use `analyst` / `analyst123` to test analyst features

### 3. Test Dashboard Features

#### Admin User (`admin` / `admin123`)
- ✅ Access to all navigation items including "Configuration"
- ✅ See warning alerts when error rate is high (>2.5%)
- ✅ View all dashboard metrics and real-time updates
- ✅ Access to user management and system configuration

#### Analyst User (`analyst` / `analyst123`)
- ✅ Access to Dashboard, Analytics, Monitoring, Reports
- ❌ No access to Configuration (admin only)
- ✅ View dashboard metrics and analytics
- ✅ Real-time data updates every 10 seconds

### 4. Test Navigation and Layout

1. **Responsive Design**: Test on different screen sizes
2. **Mobile Navigation**: Test hamburger menu on mobile
3. **Sidebar Navigation**: Click through different sections
4. **User Profile Menu**: Test logout functionality
5. **Protected Routes**: Try accessing `/config` as analyst (should redirect)

### 5. Test Real-time Features

- **Dashboard Updates**: Metrics update every 10 seconds
- **System Status**: Watch status chip change colors based on error rate
- **Alerts**: Admin users see warnings when error rate > 2.5%
- **Last Updated Time**: Shows current time of last data refresh

### 6. Test Session Persistence

1. **Login and Refresh**: Login, refresh page, should stay logged in
2. **Browser Restart**: Close browser, reopen, should stay logged in
3. **Logout**: Click logout, should clear session and redirect to login

## Sample Data Explained

### Dashboard Metrics
- **Total Requests**: Base 1,250 + random variation (1,250-1,350)
- **Requests Today**: Random 30-80 requests
- **Error Rate**: Random 1.0-4.0% (triggers alerts if >2.5%)
- **Active Users**: Random 15-30 users
- **System Status**: Based on error rate (healthy/warning/critical)

### Real-time Updates
- Data refreshes every 10 seconds
- Simulates live system monitoring
- Error rates and user counts change dynamically

## Testing Different Scenarios

### High Error Rate Scenario
- Wait for error rate to exceed 2.5%
- Admin users will see warning alert
- System status chip will turn orange/red
- Success rate in Quick Stats will decrease

### Role-based Access Testing
1. Login as `analyst`
2. Try to access Configuration menu (should not be visible)
3. Try direct URL `/config` (should redirect to unauthorized)
4. Login as `admin`
5. Configuration menu should now be visible

### Session Management Testing
1. Login with any account
2. Open browser dev tools → Application → Local Storage
3. See `auth_token` and `auth_user` stored
4. Logout and verify storage is cleared
5. Manually delete storage and refresh (should redirect to login)

## Expected Behavior

### Login Page
- Clean Material-UI design
- Form validation (required fields)
- Loading state during authentication
- Error messages for invalid credentials
- Redirect to intended page after login

### Dashboard
- Responsive grid layout
- Real-time updating metrics
- Color-coded status indicators
- Role-based content (admin alerts)
- Recent activity feed
- Quick stats sidebar

### Navigation
- Collapsible sidebar on desktop
- Mobile-friendly drawer
- Role-based menu items
- User profile with logout
- Active page highlighting

## Troubleshooting

### Common Issues

1. **Build Errors**: Run `npm install` to ensure all dependencies are installed
2. **Port Conflicts**: Change port with `PORT=3001 npm start`
3. **Authentication Issues**: Clear localStorage and try again
4. **Styling Issues**: Ensure Material-UI is properly installed

### Debug Mode

Enable React DevTools and check:
- AuthContext state
- Component re-renders
- Local storage contents
- Network requests (none for mock data)

## Next Steps for Real Integration

When ready to connect to the actual backend:

1. Replace mock authentication in `AuthContext.tsx`
2. Update API endpoints in login function
3. Add real API calls for dashboard data
4. Implement WebSocket for real-time updates
5. Add proper error handling for network requests

## Performance Testing

- Dashboard should load quickly (<2s)
- Real-time updates should be smooth
- Navigation should be responsive
- Mobile experience should be fluid
- Memory usage should remain stable during long sessions