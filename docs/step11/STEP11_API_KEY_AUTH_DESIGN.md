# Step 11: API Key Authentication - Design Document

## 1. Overview

This document outlines the design for implementing API key-based authentication for the ProCode Agent Framework, similar to how OpenAI, Anthropic, and other API providers manage customer access.

### 1.1 Goals
- API key generation and management for customers/developers
- Secure API key authentication for all backend endpoints
- Usage tracking and rate limiting per API key
- Organization/project-based key management
- Key rotation and revocation capabilities
- Audit logging for all API key usage

### 1.2 Use Case
Customers/developers who want to use the ProCode Agent Framework will:
1. Sign up for an account (via admin portal or CLI)
2. Create an organization/project
3. Generate API keys for their applications
4. Use API keys to authenticate requests to the agent backend
5. Monitor usage and manage keys via dashboard

### 1.3 Non-Goals
- User login/password authentication (not needed)
- Frontend authentication (frontend is just a demo UI)
- Session management (stateless API key auth)

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Client Application                          │
│  (Customer's code using our agent API)                       │
│                                                               │
│  const response = await fetch('https://api.procode.com/chat',│
│    {                                                          │
│      headers: {                                               │
│        'Authorization': 'Bearer pk_live_abc123...',           │
│        'Content-Type': 'application/json'                     │
│      },                                                       │
│      body: JSON.stringify({message: 'Hello'})                │
│    }                                                          │
│  );                                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTPS + API Key
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           API Key Middleware                          │   │
│  │  - Extract API key from Authorization header         │   │
│  │  - Validate key format and signature                 │   │
│  │  - Check key active and not expired                  │   │
│  │  - Load organization context                         │   │
│  │  - Check rate limits                                 │   │
│  │  - Inject context into request                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────┴──────────────────────────┐    │
│  │                                                      │    │
│  ▼                                                      ▼    │
│  ┌──────────────────┐                    ┌──────────────────┐
│  │  Agent Endpoints │                    │  Admin Endpoints │
│  │  /chat           │                    │  /admin/keys     │
│  │  /agents/*       │                    │  /admin/orgs     │
│  │  /conversations  │                    │  /admin/usage    │
│  └──────────────────┘                    └──────────────────┘
│           │                                       │           │
│           ▼                                       ▼           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Security Layer                           │   │
│  │  - API key generation (cryptographically secure)     │   │
│  │  - Key hashing (SHA-256)                              │   │
│  │  - Rate limiting per key                              │   │
│  │  - Usage tracking                                     │   │
│  │  - Audit logging                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Database Layer                           │   │
│  │  - OrganizationRepository                             │   │
│  │  - APIKeyRepository                                   │   │
│  │  - UsageRepository                                    │   │
│  │  - AuditRepository                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  orgs    │  │ api_keys │  │  usage   │  │  limits  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 3. Database Schema

### 3.1 Organizations Table
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Limits
    monthly_request_limit INTEGER DEFAULT 1000,
    rate_limit_per_minute INTEGER DEFAULT 60,
    max_api_keys INTEGER DEFAULT 5
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_email ON organizations(email);
```

### 3.2 API Keys Table
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Key identification
    key_prefix VARCHAR(20) NOT NULL, -- e.g., 'pk_live_' or 'pk_test_'
    key_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash of full key
    key_hint VARCHAR(10) NOT NULL, -- Last 4 chars for display
    
    -- Metadata
    name VARCHAR(255), -- User-friendly name
    description TEXT,
    environment VARCHAR(20) DEFAULT 'production', -- production, test, development
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP, -- NULL = never expires
    revoked_at TIMESTAMP,
    revoked_by UUID,
    revoked_reason TEXT,
    
    -- Permissions (JSON)
    scopes JSONB DEFAULT '["*"]', -- e.g., ["chat", "agents", "conversations"]
    
    -- Rate limiting (overrides org defaults if set)
    custom_rate_limit INTEGER, -- requests per minute
    
    -- Usage tracking
    total_requests BIGINT DEFAULT 0,
    last_request_at TIMESTAMP
);

CREATE INDEX idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
```

### 3.3 API Key Usage Table
```sql
CREATE TABLE api_key_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Request details
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    
    -- Performance
    response_time_ms INTEGER,
    
    -- Cost tracking
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Error tracking
    error_message TEXT,
    error_code VARCHAR(50)
);

-- Partitioned by month for performance
CREATE INDEX idx_usage_api_key ON api_key_usage(api_key_id, timestamp DESC);
CREATE INDEX idx_usage_org ON api_key_usage(organization_id, timestamp DESC);
CREATE INDEX idx_usage_timestamp ON api_key_usage(timestamp DESC);
```

### 3.4 Rate Limit Tracking Table (In-Memory/Redis in production)
```sql
CREATE TABLE rate_limit_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rate_limit_key_window ON rate_limit_tracking(api_key_id, window_start);

-- Note: In production, use Redis for rate limiting
-- This table is for development/testing only
```

## 4. API Key Format

### 4.1 Key Structure
```
pk_live_1234567890abcdefghijklmnopqrstuvwxyz
│  │    │
│  │    └─ Random secure token (32 chars)
│  └────── Environment (live, test)
└───────── Prefix (pk = ProCode Key)
```

### 4.2 Key Types

**Live Keys** (`pk_live_...`):
- Used in production
- Full access to all features
- Usage is billed
- Rate limits enforced

**Test Keys** (`pk_test_...`):
- Used in development/testing
- Same features as live keys
- Usage not billed
- Separate rate limits
- Can use test data

### 4.3 Key Generation
```python
import secrets
import hashlib

def generate_api_key(environment='live'):
    # Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)  # 32 bytes = 43 chars base64
    
    # Create key with prefix
    prefix = f"pk_{environment}_"
    full_key = f"{prefix}{token}"
    
    # Hash for storage (never store plaintext)
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Get hint (last 4 chars)
    key_hint = token[-4:]
    
    return {
        'full_key': full_key,  # Show once to user
        'key_hash': key_hash,  # Store in database
        'key_hint': key_hint,  # Store for display
        'key_prefix': prefix   # Store for identification
    }
```

## 5. Authentication Flow

### 5.1 API Request with Key

```
┌──────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│Client│          │Middleware│          │  APIKey  │          │ Database │
│      │          │          │          │ Service  │          │          │
└──┬───┘          └────┬─────┘          └────┬─────┘          └────┬─────┘
   │                   │                     │                     │
   │ POST /chat        │                     │                     │
   │ Authorization: Bearer pk_live_abc123... │                     │
   ├──────────────────>│                     │                     │
   │                   │                     │                     │
   │                   │ extract_api_key()   │                     │
   │                   │                     │                     │
   │                   │ validate_key()      │                     │
   │                   ├────────────────────>│                     │
   │                   │                     │                     │
   │                   │                     │ hash_key()          │
   │                   │                     │ SHA-256(key)        │
   │                   │                     │                     │
   │                   │                     │ get_key_by_hash()   │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ key_record          │
   │                   │                     │                     │
   │                   │                     │ check_active()      │
   │                   │                     │ check_not_expired() │
   │                   │                     │ check_not_revoked() │
   │                   │                     │                     │
   │                   │                     │ get_organization()  │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ org_record          │
   │                   │                     │                     │
   │                   │                     │ check_rate_limit()  │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ within_limit ✓      │
   │                   │                     │                     │
   │                   │<────────────────────┤                     │
   │                   │ auth_context        │                     │
   │                   │ {org_id, key_id,    │                     │
   │                   │  scopes, limits}    │                     │
   │                   │                     │                     │
   │                   │ inject_context()    │                     │
   │                   │ request.state.auth = auth_context         │
   │                   │                     │                     │
   │                   │ forward_to_endpoint()                     │
   │                   │                     │                     │
   │                   │ track_usage()       │                     │
   │                   ├────────────────────>│                     │
   │                   │                     │                     │
   │                   │                     │ log_request()       │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │<──────────────────┤                     │                     │
   │ 200 OK            │                     │                     │
   │ {response}        │                     │                     │
   │                   │                     │                     │
```

### 5.2 Error Scenarios

**Invalid API Key**:
```json
HTTP 401 Unauthorized
{
  "error": {
    "type": "invalid_api_key",
    "message": "Invalid API key provided",
    "code": "invalid_api_key"
  }
}
```

**Expired API Key**:
```json
HTTP 401 Unauthorized
{
  "error": {
    "type": "expired_api_key",
    "message": "API key has expired",
    "code": "expired_api_key",
    "expired_at": "2026-01-01T00:00:00Z"
  }
}
```

**Rate Limit Exceeded**:
```json
HTTP 429 Too Many Requests
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Rate limit exceeded",
    "code": "rate_limit_exceeded",
    "limit": 60,
    "window": "1 minute",
    "retry_after": 45
  }
}
```

**Insufficient Scope**:
```json
HTTP 403 Forbidden
{
  "error": {
    "type": "insufficient_scope",
    "message": "API key does not have required scope",
    "code": "insufficient_scope",
    "required_scope": "admin",
    "available_scopes": ["chat", "agents"]
  }
}
```

## 6. API Key Management Endpoints

### 6.1 Admin Endpoints (Internal Use)

#### POST /admin/organizations
Create new organization
```json
Request:
{
  "name": "Acme Corp",
  "email": "admin@acme.com",
  "plan": "pro"
}

Response (201):
{
  "id": "org_abc123",
  "name": "Acme Corp",
  "slug": "acme-corp",
  "plan": "pro",
  "created_at": "2026-01-27T00:00:00Z"
}
```

#### POST /admin/organizations/{org_id}/keys
Generate API key for organization
```json
Request:
{
  "name": "Production API Key",
  "environment": "live",
  "scopes": ["chat", "agents"],
  "expires_in_days": 365
}

Response (201):
{
  "id": "key_xyz789",
  "key": "pk_live_1234567890abcdefghijklmnopqrstuvwxyz",
  "name": "Production API Key",
  "hint": "wxyz",
  "environment": "live",
  "scopes": ["chat", "agents"],
  "created_at": "2026-01-27T00:00:00Z",
  "expires_at": "2027-01-27T00:00:00Z",
  "warning": "This key will only be shown once. Store it securely."
}
```

#### GET /admin/organizations/{org_id}/keys
List API keys for organization
```json
Response (200):
{
  "keys": [
    {
      "id": "key_xyz789",
      "name": "Production API Key",
      "hint": "wxyz",
      "environment": "live",
      "is_active": true,
      "created_at": "2026-01-27T00:00:00Z",
      "last_used_at": "2026-01-27T01:00:00Z",
      "total_requests": 1523
    }
  ]
}
```

#### DELETE /admin/organizations/{org_id}/keys/{key_id}
Revoke API key
```json
Request:
{
  "reason": "Key compromised"
}

Response (200):
{
  "id": "key_xyz789",
  "revoked_at": "2026-01-27T02:00:00Z",
  "reason": "Key compromised"
}
```

#### GET /admin/organizations/{org_id}/usage
Get usage statistics
```json
Response (200):
{
  "organization_id": "org_abc123",
  "period": "2026-01",
  "total_requests": 15234,
  "total_tokens": 1523400,
  "total_cost_usd": 15.23,
  "by_endpoint": {
    "/chat": 10000,
    "/agents/tickets": 3000,
    "/agents/account": 2234
  },
  "by_day": [
    {"date": "2026-01-01", "requests": 500, "cost_usd": 0.50},
    {"date": "2026-01-02", "requests": 600, "cost_usd": 0.60}
  ]
}
```

## 7. Rate Limiting Strategy

### 7.1 Rate Limit Tiers

| Plan | Requests/Minute | Requests/Month | Max Keys |
|------|----------------|----------------|----------|
| Free | 10 | 1,000 | 2 |
| Pro | 60 | 100,000 | 10 |
| Enterprise | 300 | 1,000,000 | 50 |

### 7.2 Rate Limit Algorithm

**Sliding Window Counter**:
```python
def check_rate_limit(api_key_id: str, limit: int) -> bool:
    """
    Check if request is within rate limit using sliding window.
    
    Args:
        api_key_id: API key identifier
        limit: Requests per minute
    
    Returns:
        True if within limit, False otherwise
    """
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=1)
    
    # Count requests in last minute
    count = redis.zcount(
        f"rate_limit:{api_key_id}",
        window_start.timestamp(),
        now.timestamp()
    )
    
    if count >= limit:
        return False
    
    # Add current request
    redis.zadd(
        f"rate_limit:{api_key_id}",
        {str(uuid.uuid4()): now.timestamp()}
    )
    
    # Clean old entries
    redis.zremrangebyscore(
        f"rate_limit:{api_key_id}",
        0,
        window_start.timestamp()
    )
    
    # Set expiry
    redis.expire(f"rate_limit:{api_key_id}", 120)
    
    return True
```

### 7.3 Rate Limit Headers

Include rate limit info in response headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706000000
X-RateLimit-Used: 15
```

## 8. Usage Tracking & Billing

### 8.1 Usage Metrics

Track per request:
- Endpoint called
- Response time
- Tokens used (for LLM calls)
- Cost (based on token usage)
- Success/error status

### 8.2 Cost Calculation

```python
def calculate_cost(tokens_used: int, model: str) -> Decimal:
    """
    Calculate cost based on token usage.
    
    Pricing (example):
    - GPT-4: $0.03 per 1K tokens
    - GPT-3.5: $0.002 per 1K tokens
    """
    pricing = {
        'gpt-4': Decimal('0.03'),
        'gpt-3.5-turbo': Decimal('0.002')
    }
    
    cost_per_1k = pricing.get(model, Decimal('0.01'))
    cost = (Decimal(tokens_used) / 1000) * cost_per_1k
    
    return cost.quantize(Decimal('0.000001'))
```

### 8.3 Monthly Billing

```sql
-- Monthly usage summary
SELECT 
    o.id as organization_id,
    o.name as organization_name,
    o.plan,
    COUNT(*) as total_requests,
    SUM(u.tokens_used) as total_tokens,
    SUM(u.cost_usd) as total_cost_usd
FROM api_key_usage u
JOIN api_keys k ON u.api_key_id = k.id
JOIN organizations o ON k.organization_id = o.id
WHERE u.timestamp >= DATE_TRUNC('month', CURRENT_DATE)
  AND u.timestamp < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
GROUP BY o.id, o.name, o.plan
ORDER BY total_cost_usd DESC;
```

## 9. Security Considerations

### 9.1 Key Storage
- ✅ Never store plaintext API keys
- ✅ Hash keys with SHA-256 before storage
- ✅ Show full key only once during generation
- ✅ Store only last 4 characters for display

### 9.2 Key Transmission
- ✅ Always use HTTPS
- ✅ Keys in Authorization header (not URL)
- ✅ Never log full API keys
- ✅ Mask keys in error messages

### 9.3 Key Rotation
- ✅ Support key expiration
- ✅ Allow creating multiple keys
- ✅ Graceful key rotation (overlap period)
- ✅ Immediate revocation capability

### 9.4 Audit Logging
- ✅ Log all key generation events
- ✅ Log all key revocation events
- ✅ Log authentication failures
- ✅ Log rate limit violations
- ✅ Log unusual usage patterns

## 10. Implementation Components

### 10.1 Core Components

```
security/
├── api_key_generator.py    # Generate secure API keys
├── api_key_hasher.py        # Hash and verify keys
├── api_key_service.py       # Key management logic
├── api_key_middleware.py    # FastAPI middleware
└── rate_limiter.py          # Rate limiting (enhanced)

database/repositories/
├── organization_repository.py  # Org CRUD
├── api_key_repository.py       # Key CRUD
└── usage_repository.py         # Usage tracking

api/
├── admin_routes.py          # Admin endpoints
└── public_routes.py         # Public API endpoints
```

### 10.2 Middleware Implementation

```python
class APIKeyMiddleware:
    """
    Middleware to authenticate requests using API keys.
    """
    
    def __init__(self, app, api_key_service, rate_limiter):
        self.app = app
        self.api_key_service = api_key_service
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in ['/health', '/docs', '/openapi.json']:
            return await call_next(request)
        
        # Extract API key
        api_key = self.extract_api_key(request)
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"error": {"type": "missing_api_key", "message": "API key required"}}
            )
        
        # Validate API key
        try:
            auth_context = await self.api_key_service.validate_key(api_key)
        except InvalidAPIKeyError:
            return JSONResponse(
                status_code=401,
                content={"error": {"type": "invalid_api_key", "message": "Invalid API key"}}
            )
        except ExpiredAPIKeyError as e:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "type": "expired_api_key",
                        "message": "API key has expired",
                        "expired_at": e.expired_at.isoformat()
                    }
                }
            )
        
        # Check rate limit
        if not await self.rate_limiter.check_limit(auth_context['key_id'], auth_context['rate_limit']):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Rate limit exceeded",
                        "limit": auth_context['rate_limit'],
                        "retry_after": 60
                    }
                },
                headers={"Retry-After": "60"}
            )
        
        # Inject auth context
        request.state.auth = auth_context
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers['X-RateLimit-Limit'] = str(auth_context['rate_limit'])
        response.headers['X-RateLimit-Remaining'] = str(auth_context['remaining'])
        
        # Track usage (async)
        asyncio.create_task(
            self.api_key_service.track_usage(
                key_id=auth_context['key_id'],
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code
            )
        )
        
        return response
    
    def extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from Authorization header."""
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        return None
```

## 11. Frontend Integration

### 11.1 No User Authentication Needed

The frontend is just a demo/testing UI. It can:
1. Have a hardcoded test API key for demo purposes
2. Allow users to input their own API key
3. Store API key in localStorage (for demo only)

### 11.2 API Key Input Component

```typescript
// frontend/components/APIKeyInput.tsx
'use client';

import { useState } from 'react';

export function APIKeyInput() {
  const [apiKey, setApiKey] = useState(
    localStorage.getItem('procode_api_key') || ''
  );
  
  const handleSave = () => {
    localStorage.setItem('procode_api_key', apiKey);
    // Reload or update context
  };
  
  return (
    <div className="api-key-input">
      <label>API Key:</label>
      <input
        type="password"
        value={apiKey}
        onChange={(e) => setApiKey(e.target.value)}
        placeholder="pk_live_..."
      />
      <button onClick={handleSave}>Save</button>
    </div>
  );
}
```

### 11.3 API Client with Key

```typescript
// frontend/lib/apiClient.ts
export class ProCodeClient {
  private apiKey: string;
  private baseURL: string;
  
  constructor(apiKey: string, baseURL: string = 'https://api.procode.com') {
    this.apiKey = apiKey;
    this.baseURL = baseURL;
  }
  
  async chat(message: string) {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error.message);
    }
    
    return response.json();
  }
}
```

## 12. CLI Tool for Key Management

```bash
# Create organization
procode-admin org create --name "Acme Corp" --email "admin@acme.com" --plan pro

# Generate API key
procode-admin key create --org acme-corp --name "Production Key" --env live

# List keys
procode-admin key list --org acme-corp

# Revoke key
procode-admin key revoke --key key_xyz789 --reason "Compromised"

# View usage
procode-admin usage --org acme-corp --month 2026-01
```

## 13. Migration from Current System

### 13.1 Current State
- No authentication currently
- Open access to all endpoints

### 13.2 Migration Strategy

**Phase 1**: Add API key system (optional)
- Implement API key middleware
- Make authentication optional (feature flag)
- Allow both authenticated and unauthenticated requests

**Phase 2**: Gradual enforcement
- Create default organization and key
- Update frontend to use API key
- Monitor usage

**Phase 3**: Full enforcement
- Enable authentication requirement
- Reject unauthenticated requests
- Monitor for issues

## 14. Monitoring & Alerts

### 14.1 Key Metrics
- API key usage per organization
- Rate limit violations
- Invalid key attempts
- Cost per organization
- Token usage trends

### 14.2