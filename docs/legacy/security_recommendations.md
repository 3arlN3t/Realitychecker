# Security Recommendations for app/main.py

## Critical Security Issues

### 1. CORS Configuration
**Current Issue**: `allow_origins=["*"]` allows any domain to make requests
**Fix**: Restrict to specific domains in production

```python
# Environment-based CORS configuration
allowed_origins = (
    ["*"] if config.environment == "development" 
    else ["https://yourdomain.com", "https://dashboard.yourdomain.com"]
)
```

### 2. Trusted Host Middleware
**Current Issue**: `allowed_hosts=["*"]` accepts requests from any host
**Fix**: Restrict to known hosts

```python
allowed_hosts = (
    ["*"] if config.environment == "development"
    else ["localhost", "127.0.0.1", config.domain]
)
```

### 3. Headers Restriction
**Current Issue**: `allow_headers=["*"]` allows any header
**Fix**: Specify required headers only

```python
allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"]
```

### 4. Rate Limiting
**Current Issue**: Very restrictive limits (10/min) may impact legitimate users
**Recommendation**: Adjust based on environment and usage patterns

```python
requests_per_minute=60 if config.environment == "development" else 30
```

## Additional Security Enhancements

### 1. Add Request Size Limits
```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 2. Add Security Headers
Ensure your security headers middleware includes:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HTTPS only)

### 3. Input Validation
- Sanitize user agent logging (already done: `[:100]`)
- Validate correlation IDs
- Add request body size limits

### 4. Environment Variables
Store sensitive configuration in environment variables:
- ALLOWED_ORIGINS
- TRUSTED_HOSTS
- RATE_LIMIT_SETTINGS