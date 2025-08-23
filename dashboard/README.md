# Reality Checker Dashboard

Admin dashboard for the Reality Checker WhatsApp bot system. Built with React, TypeScript, and Material-UI.

## Features

- **Authentication**: JWT-based login system with role-based access control and MFA support
- **Dashboard Overview**: System metrics and health monitoring with real-time updates
- **Analytics**: Usage statistics, classification trends, and AI analysis performance
- **Real-time Monitoring**: Live system metrics, WebSocket connections, and active request tracking
- **User Management**: WhatsApp user interaction history, blocking/unblocking, and detailed user profiles
- **Configuration**: System settings management including OpenAI model configuration (admin only)
- **Reports**: Generate and export comprehensive reports with analysis accuracy metrics
- **Multi-Factor Authentication**: TOTP-based MFA with backup codes and admin management
- **Advanced Analytics**: A/B testing, user clustering, pattern detection, and predictive analytics
- **Monitoring & Alerting**: Real-time error tracking, performance monitoring, and alert management

## Technology Stack

- **React 19** with TypeScript
- **Material-UI (MUI)** for UI components
- **Radix UI** for accessible component primitives
- **React Router** for navigation
- **TanStack Query (React Query)** for data fetching and caching
- **Axios** for HTTP requests
- **Recharts** for data visualization
- **Tailwind CSS** for styling
- **WebSocket** for real-time updates
- **CRACO** for build configuration

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The application will open at [http://localhost:3000](http://localhost:3000).

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App (one-way operation)

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main layout with navigation
│   ├── ProtectedRoute.tsx # Route protection component
│   ├── KeyboardShortcuts.tsx # Keyboard navigation support
│   ├── admin/          # Admin-specific components
│   ├── analytics/      # Analytics components with charts
│   ├── configuration/  # Configuration management components
│   ├── monitoring/     # Real-time monitoring components
│   ├── reporting/      # Report generation components
│   ├── ui/            # Reusable UI primitives (Radix UI)
│   └── users/         # User management components
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication context
├── hooks/              # Custom React hooks
│   ├── useWebSocket.ts # WebSocket connection hook
│   └── useKeyboardNavigation.ts # Keyboard navigation hook
├── pages/              # Page components
│   ├── LoginPage.tsx   # Login page with MFA support
│   ├── DashboardPage.tsx # Main dashboard with metrics
│   ├── AnalyticsPage.tsx # Analytics dashboard
│   ├── MonitoringPage.tsx # Real-time monitoring
│   ├── UsersPage.tsx   # User management
│   ├── ConfigurationPage.tsx # System configuration
│   └── ReportingPage.tsx # Report generation
├── providers/          # Context providers
│   └── QueryProvider.tsx # TanStack Query provider
├── test-utils/         # Testing utilities
│   └── api-mocks.ts   # API mocking for tests
├── lib/               # Utility libraries
│   └── utils.ts       # Common utility functions
└── App.tsx            # Main application component
```

## Authentication

The dashboard uses JWT-based authentication with role-based access control:

- **Admin**: Full access to all features including configuration
- **Analyst**: Access to dashboards, analytics, and reports (no configuration access)

## Development

### Adding New Pages

1. Create a new component in `src/pages/`
2. Add the route to `App.tsx`
3. Update navigation in `Layout.tsx` if needed

### API Integration

The dashboard is configured to work with the FastAPI backend. API calls should be made through the configured axios instance with proper authentication headers.

## Build and Deployment

To build for production:

```bash
npm run build
```

This creates a `build` folder with optimized production files ready for deployment.

## Current Features

- ✅ Real-time WebSocket integration for live updates
- ✅ Data visualization with Recharts
- ✅ Advanced filtering and search capabilities
- ✅ Export functionality for reports (CSV/PDF)
- ✅ Comprehensive test coverage with Jest
- ✅ Accessibility compliance with WCAG guidelines
- ✅ Multi-factor authentication (MFA) support
- ✅ Role-based access control (Admin/Analyst)
- ✅ Performance monitoring and optimization
- ✅ Keyboard navigation support

## Future Enhancements

- Dark mode theme support
- Advanced data visualization with custom charts
- Real-time collaboration features
- Mobile-responsive design improvements
- Internationalization (i18n) support
- Advanced user analytics and insights