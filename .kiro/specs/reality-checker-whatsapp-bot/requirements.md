# Requirements Document

## Introduction

The Reality Checker is a WhatsApp bot application built with Python FastAPI that analyzes job advertisements to detect potential scams. The bot receives job ads via WhatsApp messages (either as plain text or PDF uploads), processes them using AI analysis, and returns a trust score with classification and reasoning to help users identify legitimate job opportunities versus potential scams.

## Requirements

### Requirement 1

**User Story:** As a WhatsApp user, I want to send job ad text directly to the bot, so that I can quickly get a scam analysis without needing to upload files.

#### Acceptance Criteria

1. WHEN a user sends a plain text message containing a job ad THEN the system SHALL process the text directly for analysis
2. WHEN the system receives plain text input THEN it SHALL validate that the message contains sufficient content for analysis
3. IF the text is too short or lacks job-related content THEN the system SHALL respond with a helpful message asking for more details

### Requirement 2

**User Story:** As a WhatsApp user, I want to upload PDF job postings to the bot, so that I can analyze job ads that I received as documents.

#### Acceptance Criteria

1. WHEN a user uploads a PDF file via WhatsApp THEN the system SHALL download and extract the text content using pdfplumber
2. WHEN PDF text extraction is successful THEN the system SHALL use the extracted text for scam analysis
3. IF PDF extraction fails or returns empty content THEN the system SHALL respond with an error message explaining the issue
4. WHEN a PDF is processed THEN the system SHALL handle files up to reasonable size limits to prevent resource exhaustion

### Requirement 3

**User Story:** As a WhatsApp user, I want to receive a comprehensive scam analysis with scoring, so that I can make informed decisions about job opportunities.

#### Acceptance Criteria

1. WHEN job ad content is analyzed THEN the system SHALL generate a trust score between 0-100
2. WHEN analysis is complete THEN the system SHALL classify the job ad as "Legit", "Suspicious", or "Likely Scam"
3. WHEN providing classification THEN the system SHALL include exactly 3 specific reasons supporting the classification
4. WHEN generating the response THEN the system SHALL format it appropriately for WhatsApp messaging with clear structure

### Requirement 4

**User Story:** As a WhatsApp user, I want to receive responses through the same WhatsApp interface, so that I can get results seamlessly without switching platforms.

#### Acceptance Criteria

1. WHEN analysis is complete THEN the system SHALL send the response back to the user via Twilio WhatsApp API
2. WHEN sending responses THEN the system SHALL ensure proper message formatting for WhatsApp display
3. IF the response is too long THEN the system SHALL split it into multiple messages while maintaining readability
4. WHEN errors occur THEN the system SHALL send user-friendly error messages via WhatsApp

### Requirement 5

**User Story:** As a system administrator, I want the application to handle Twilio webhook requests properly, so that WhatsApp messages are processed reliably.

#### Acceptance Criteria

1. WHEN Twilio sends a webhook POST request THEN the system SHALL receive and validate the incoming message data
2. WHEN processing webhook requests THEN the system SHALL handle Twilio's expected response format
3. WHEN webhook validation fails THEN the system SHALL log the error and return appropriate HTTP status codes
4. WHEN processing messages THEN the system SHALL handle concurrent requests without data corruption

### Requirement 6

**User Story:** As a developer, I want the application to use OpenAI GPT-4 for intelligent job ad analysis, so that the scam detection is accurate and contextual.

#### Acceptance Criteria

1. WHEN analyzing job ad content THEN the system SHALL use OpenAI GPT-4 API for analysis
2. WHEN calling OpenAI API THEN the system SHALL include specific prompts for scam detection analysis
3. IF OpenAI API calls fail THEN the system SHALL handle errors gracefully and provide fallback responses
4. WHEN API responses are received THEN the system SHALL parse and validate the structured response format

### Requirement 7

**User Story:** As a system administrator, I want secure configuration management, so that API keys and sensitive data are protected.

#### Acceptance Criteria

1. WHEN the application starts THEN it SHALL load configuration from environment variables using python-dotenv
2. WHEN accessing sensitive data THEN the system SHALL use .env file for OpenAI and Twilio API credentials
3. WHEN deploying THEN the system SHALL not expose API keys in code or logs
4. IF required environment variables are missing THEN the system SHALL fail to start with clear error messages

### Requirement 8

**User Story:** As a system administrator, I want health monitoring capabilities, so that I can verify the application is running correctly.

#### Acceptance Criteria

1. WHEN the system is running THEN it SHALL provide a /health endpoint for health checks
2. WHEN /health is accessed THEN the system SHALL return HTTP 200 with system status information
3. WHEN health checks are performed THEN the system SHALL verify critical dependencies are accessible
4. IF critical services are unavailable THEN the health check SHALL return appropriate error status

### Requirement 9

**User Story:** As a system administrator, I want a web-based admin dashboard, so that I can monitor system health, view metrics, and manage the bot configuration.

#### Acceptance Criteria

1. WHEN accessing the admin dashboard THEN the system SHALL provide a web interface at /admin with authentication
2. WHEN viewing the dashboard THEN it SHALL display real-time system metrics including request counts, error rates, and response times
3. WHEN monitoring services THEN the dashboard SHALL show the health status of OpenAI, Twilio, and other critical dependencies
4. WHEN managing configuration THEN the dashboard SHALL allow updating bot settings without requiring application restart

### Requirement 10

**User Story:** As a business analyst, I want an analytics dashboard, so that I can view usage statistics, analysis trends, and user insights.

#### Acceptance Criteria

1. WHEN accessing analytics THEN the system SHALL provide charts and graphs showing job analysis trends over time
2. WHEN viewing statistics THEN the dashboard SHALL display classification breakdowns (Legit vs Suspicious vs Scam)
3. WHEN analyzing usage THEN the system SHALL show user engagement metrics and peak usage times
4. WHEN generating reports THEN the system SHALL allow exporting data in CSV and PDF formats

### Requirement 11

**User Story:** As a system administrator, I want real-time monitoring dashboards, so that I can track active requests, error rates, and service performance.

#### Acceptance Criteria

1. WHEN monitoring in real-time THEN the system SHALL display live metrics updating every 5-10 seconds
2. WHEN viewing active requests THEN the dashboard SHALL show current processing status and queue depth
3. WHEN tracking errors THEN the system SHALL display error rates with drill-down capabilities to view specific errors
4. WHEN monitoring performance THEN the dashboard SHALL show response time percentiles and service latency

### Requirement 12

**User Story:** As a system administrator, I want user management capabilities, so that I can view WhatsApp user interactions and manage user access.

#### Acceptance Criteria

1. WHEN managing users THEN the system SHALL display a list of WhatsApp users who have interacted with the bot
2. WHEN viewing user details THEN the system SHALL show interaction history, analysis requests, and user patterns
3. WHEN managing access THEN the system SHALL allow blocking/unblocking users if needed
4. WHEN analyzing user behavior THEN the system SHALL provide insights into user engagement and usage patterns

### Requirement 13

**User Story:** As a business stakeholder, I want reporting capabilities, so that I can generate reports on scam detection patterns and system performance.

#### Acceptance Criteria

1. WHEN generating reports THEN the system SHALL create comprehensive reports on scam detection trends
2. WHEN analyzing patterns THEN reports SHALL include common scam indicators and detection accuracy metrics
3. WHEN reviewing performance THEN reports SHALL include system uptime, response times, and error rates
4. WHEN scheduling reports THEN the system SHALL allow automated report generation and email delivery

### Requirement 14

**User Story:** As a developer, I want clear documentation and setup instructions, so that I can easily run and deploy the application.

#### Acceptance Criteria

1. WHEN setting up the project THEN there SHALL be a comprehensive README with setup instructions
2. WHEN running locally THEN the documentation SHALL include uvicorn server startup commands
3. WHEN deploying THEN the documentation SHALL include deployment guidelines and requirements
4. WHEN configuring THEN the documentation SHALL explain all required environment variables and their purposes