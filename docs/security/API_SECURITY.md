# API Security Guide

This guide explains how to secure your Procode Agent Framework deployment for production use.

## Overview

The framework includes three layers of security:

1. **Rate Limiting** - Prevents abuse by limiting requests per IP address
2. **API Key Authentication** - Requires valid API key for all requests
3. **CORS Restriction** - Limits which domains can access the API

## Quick Setup for Production

### 1. Generate a Secure API Key

```bash
# Generate a random 32-byte hex string
openssl rand -hex 32
```

### 2. Configure Environment Variables

Edit your `.env` or `.env.portainer` file:

```bash
# Enable security
ENABLE_API_SECURITY=true

# Set your generated API key
DEMO_API_KEY=your-generated-key-here

# Configure rate limits (adjust based on your needs)
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=1000

# Restrict CORS to your domain only
ALLOWED_ORIGINS=https://yourdomain.com
```

### 3. Configure Frontend

The frontend needs the same API key to authenticate requests.

For Docker deployment, add to your frontend environment:

```bash
DEMO_API_KEY=your-generated-key-here
```

For Next.js development, add to `frontend/.env.local`:

```bash
DEMO_API_KEY=your-generated-key-here
```

### 4. Restart Services

```bash
# Docker Compose
docker-compose down && docker-compose up -d

# Or in Portainer
# Update stack environment variables and redeploy
```

## Security Features

### Rate Limiting

Protects against abuse by limiting requests per IP address across three time windows:

- **Per Minute**: Default 10 requests (configurable via `RATE_LIMIT_PER_MINUTE`)
- **Per Hour**: Default 100 requests (configurable via `RATE_LIMIT_PER_HOUR`)
- **Per Day**: Default 1000 requests (configurable via `RATE_LIMIT_PER_DAY`)

When rate limit is exceeded, the API returns:
- HTTP 429 (Too Many Requests)
- Remaining quota information
- Reset time for each window
- `Retry-After` header

Response headers include quota information:
```
X-RateLimit-Remaining-Minute: 8
X-RateLimit-Remaining-Hour: 95
X-RateLimit-Remaining-Day: 987
```

### API Key Authentication

Requires a valid API key for all requests (except health checks).

**How to provide the API key:**

Option 1: HTTP Header (Recommended)
```bash
curl -H "X-API-Key: your-api-key" https://api.example.com/
```

Option 2: Query Parameter
```bash
curl https://api.example.com/?api_key=your-api-key
```

**Error responses:**

Missing API key (HTTP 401):
```json
{
  "error": "API key required",
  "message": "Please provide an API key via X-API-Key header or api_key query parameter"
}
```

Invalid API key (HTTP 403):
```json
{
  "error": "Invalid API key",
  "message": "The provided API key is invalid"
}
```

### CORS Restriction

Limits which domains can access your API.

**Development (multiple origins):**
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8501
```

**Production (single domain):**
```bash
ALLOWED_ORIGINS=https://yourdomain.com
```

**Production (multiple domains):**
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Deployment Scenarios

### Local Development (No Security)

For local development, security is disabled by default:

```bash
# .env
ENABLE_API_SECURITY=false
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Public Demo (Full Security)

For public demos, enable all security features:

```bash
# .env.portainer
ENABLE_API_SECURITY=true
DEMO_API_KEY=your-secure-key-here
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=1000
ALLOWED_ORIGINS=https://proagent.harjadi.com
```

### Private API (API Key Only)

For private APIs with trusted clients, you might want API key without rate limiting:

```bash
ENABLE_API_SECURITY=true
DEMO_API_KEY=your-secure-key-here
RATE_LIMIT_PER_MINUTE=1000  # Very high limit
RATE_LIMIT_PER_HOUR=10000
RATE_LIMIT_PER_DAY=100000
ALLOWED_ORIGINS=*  # Allow all origins (not recommended)
```

## Testing Security

### Test Rate Limiting

```bash
# Make multiple requests quickly
for i in {1..15}; do
  curl -H "X-API-Key: your-key" https://api.example.com/
  echo "Request $i"
done

# After 10 requests, you should see HTTP 429
```

### Test API Key Authentication

```bash
# Without API key (should fail with 401)
curl https://api.example.com/

# With invalid API key (should fail with 403)
curl -H "X-API-Key: wrong-key" https://api.example.com/

# With valid API key (should succeed)
curl -H "X-API-Key: your-key" https://api.example.com/
```

### Test CORS Restriction

```bash
# From allowed origin (should succeed)
curl -H "Origin: https://yourdomain.com" https://api.example.com/

# From disallowed origin (should fail)
curl -H "Origin: https://evil.com" https://api.example.com/
```

## Monitoring

### Check Rate Limiter Stats

The rate limiter tracks usage statistics. You can add an admin endpoint to view them:

```python
# In __main__.py
from security.api_security import APISecurityMiddleware

@app.route("/admin/rate-limit-stats")
async def rate_limit_stats(request):
    # Add authentication here
    middleware = app.middleware[0]  # Get security middleware
    stats = middleware.rate_limiter.get_stats()
    return JSONResponse(stats)
```

### Monitor Logs

Security events are logged. Check your application logs for:
- Rate limit violations
- Invalid API key attempts
- CORS violations

## Best Practices

1. **Rotate API Keys Regularly**
   - Generate new keys periodically
   - Update both backend and frontend
   - Invalidate old keys

2. **Use Environment Variables**
   - Never commit API keys to git
   - Use `.env` files (already in `.gitignore`)
   - Use secrets management in production (AWS Secrets Manager, etc.)

3. **Adjust Rate Limits Based on Usage**
   - Monitor actual usage patterns
   - Set limits that prevent abuse but allow legitimate use
   - Consider different limits for different endpoints

4. **Use HTTPS in Production**
   - Always use HTTPS for production deployments
   - API keys sent over HTTP can be intercepted
   - Configure SSL/TLS certificates properly

5. **Monitor and Alert**
   - Set up monitoring for rate limit violations
   - Alert on suspicious patterns
   - Review logs regularly

## Troubleshooting

### Frontend Can't Connect to Backend

**Symptom:** Frontend shows "I'm having trouble connecting to the backend"

**Solutions:**
1. Check `DEMO_API_KEY` is set in frontend environment
2. Verify `ALLOWED_ORIGINS` includes your frontend domain
3. Check `NEXT_PUBLIC_AGENT_URL` points to correct backend URL

### Rate Limit Too Restrictive

**Symptom:** Legitimate users hitting rate limits

**Solutions:**
1. Increase rate limits in environment variables
2. Consider per-user rate limiting instead of per-IP
3. Implement API key tiers with different limits

### CORS Errors

**Symptom:** Browser shows CORS policy errors

**Solutions:**
1. Add your domain to `ALLOWED_ORIGINS`
2. Check domain matches exactly (including protocol and port)
3. Verify CORS middleware is configured correctly

## Security Considerations

### What This Protects Against

✅ **Brute force attacks** - Rate limiting prevents rapid-fire requests
✅ **Unauthorized access** - API key prevents random users from accessing API
✅ **Cross-site attacks** - CORS prevents malicious sites from calling your API
✅ **Resource exhaustion** - Rate limiting prevents single user from consuming all resources

### What This Doesn't Protect Against

❌ **DDoS attacks** - Use CloudFlare or AWS Shield for DDoS protection
❌ **Compromised API keys** - Rotate keys regularly and monitor usage
❌ **Application vulnerabilities** - Keep dependencies updated, use security scanning
❌ **Data breaches** - Implement proper data encryption and access controls

## Advanced Configuration

### Custom Rate Limits per Endpoint

You can implement different rate limits for different endpoints by modifying the security middleware:

```python
# In security/api_security.py
def get_rate_limit_for_path(self, path: str) -> tuple:
    """Return (per_minute, per_hour, per_day) for given path"""
    if path.startswith("/admin"):
        return (5, 50, 500)  # Stricter for admin
    elif path.startswith("/public"):
        return (20, 200, 2000)  # More lenient for public
    else:
        return (10, 100, 1000)  # Default
```

### Multiple API Keys

For multiple clients with different access levels:

```python
# In security/api_security.py
API_KEYS = {
    "demo-key-123": {"name": "Public Demo", "rate_limit_multiplier": 1.0},
    "premium-key-456": {"name": "Premium Client", "rate_limit_multiplier": 10.0},
}
```

### IP Whitelisting

For trusted IPs that bypass rate limiting:

```python
# In security/api_security.py
WHITELISTED_IPS = ["1.2.3.4", "5.6.7.8"]

if client_ip in WHITELISTED_IPS:
    return await call_next(request)  # Skip rate limiting
```

## Related Documentation

- [Docker Deployment](DOCKER_DEPLOYMENT.md) - Docker setup and configuration
- [Production Roadmap](PRODUCTION_ROADMAP.md) - Production deployment checklist
- [Database Integration](DATABASE_INTEGRATION.md) - Database security considerations
