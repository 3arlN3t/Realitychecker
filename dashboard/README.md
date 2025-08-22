# Reality Checker Dashboard

Admin dashboard for the Reality Checker WhatsApp bot system. Built with React, TypeScript, and Material-UI.

## Features

- **Authentication**: JWT-based login system with role-based access control
- **Dashboard Overview**: System metrics and health monitoring
- **Analytics**: Usage statistics, classification trends, and AI analysis performance
- **Real-time Monitoring**: Live system metrics, OpenAI API status, and active request tracking
- **User Management**: WhatsApp user interaction history and management
- **Configuration**: System settings management including OpenAI model configuration (admin only)
- **Reports**: Generate and export comprehensive reports with analysis accuracy metrics

## Technology Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for UI components
- **React Router** for navigation
- **React Query** for data fetching and caching
- **Axios** for HTTP requests

## Getting Started

### Prerequisites

- Node.js 16 or higher
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
│   └── ProtectedRoute.tsx # Route protection component
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication context
├── pages/              # Page components
│   ├── LoginPage.tsx   # Login page
│   ├── DashboardPage.tsx # Main dashboard
│   └── AnalyticsPage.tsx # Analytics dashboard
├── providers/          # Context providers
│   └── QueryProvider.tsx # React Query provider
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

## Future Enhancements

- Real-time WebSocket integration for live updates
- Data visualization with Chart.js/Recharts
- Advanced filtering and search capabilities
- Export functionality for reports
- Dark mode theme support