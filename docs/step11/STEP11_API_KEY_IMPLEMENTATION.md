# Step 11: API Key Authentication - Implementation Checklist

## Overview

**Estimated Timeline**: 7 days (1.5 weeks)  
**Prerequisites**: Step 10 (Database Integration) completed ✓  
**Dependencies**: PostgreSQL, SQLAlchemy, Alembic, Redis (optional)

---

## Phase 1: Database Schema & Migrations (Day 1)

### 1.1 Create Alembic Migration
- [ ] Create migration: `alembic revision -m "add_api_key_authentication"`
- [ ] Define `organizations` table
  - [ ] `id`, `name`, `slug`, `email`, `plan`
  - [ ] `is_active`, `created_at`, `updated_at`
  - [ ] `monthly_request_limit`, `rate_limit_per_minute`, `max_api_keys`
  - [ ] Indexes on `slug` and `email`
- [ ] Define `api_keys` table
  - [ ] `id`, `organization_id`, `key_prefix`, `key_hash`, `key_hint`
  - [ ] `name`, `description`, `environment`
  - [ ] `is_active`, `created_at`, `last_used_at`, `expires_at`
  - [ ] `revoked_at`, `revoked_by`, `revoked_reason`
  - [ ] `scopes` (JSONB), `custom_rate_limit`
  - [ ] `total_requests`, `last_request_at`
  - [ ] Indexes on `organization_id`, `key_hash`, `is_active`, `key_prefix`
- [ ] Define `api_key_usage` table
  - [ ] `id`, `api_key_id`, `organization_id`
  - [ ] `timestamp`, `endpoint`, `method`, `status_code`
  - [ ] `response_time_ms`, `tokens_used`, `cost_usd`
  - [ ] `ip_address`, `user_agent`, `error_message`, `error_code`
  - [ ] Indexes on `api_key_id`, `organization_id`, `timestamp`
- [ ] Define `rate_limit_tracking` table (for development, use Redis in production)
  - [ ] `id`, `api_key_id`, `window_start`, `window_end`
  - [ ] `request_count`, `created_at`, `updated_at`

### 1.2 Seed Default Data
- [ ] Create seed script: `scripts/seed_api_keys.py`
- [ ] Create default organization:
  - [ ] Name: "Default Organization"
  - [ ] Slug: "default"
  - [ ] Plan: "free"
- [ ] Generate default API key:
  - [ ] Environment: "test"
  - [ ] Name: "Default Test Key"
  - [ ] Scopes: ["*"]
  - [ ] Log the generated key to console

### 1.3 Run Migration
- [ ] Test migration: `alembic upgrade head`
- [ ] Verify tables created
- [ ] Run seed script: `python scripts/seed_api_keys.py`
- [ ] Save default API key for testing
- [ ] Test rollback: `alembic downgrade -1`
- [ ] Re-apply: `alembic upgrade head`

**Deliverables**:
- `alembic/versions/XXXXX_add_api_key_authentication.py`
- `scripts/seed_api_keys.py`
- Default test API key

---

## Phase 2: Core Security Components (Days 2-3)

### 2.1 API Key Generator
- [ ] Create [`security/api_key_generator.py`](security/api_key_generator.py)
- [ ] Implement `APIKeyGenerator` class
  - [ ] `generate_key(environment='live') -> dict`
    - [ ] Use `secrets.token_urlsafe(32)` for secure random token
    - [ ] Create key with prefix: `pk_{environment}_{token}`
    - [ ] Hash key with SHA-256
    - [ ] Extract last 4 chars as hint
    - [ ] Return full_key, key_hash, key_hint, key_prefix
  - [ ] `validate_key_format(key: str) -> bool`
    - [ ] Check prefix format
    - [ ] Check length
    - [ ] Check character set
- [ ] Add unit tests: `tests/test_api_key_generator.py`
  - [ ] Test key generation
  - [ ] Test key format validation
  - [ ] Test uniqueness
  - [ ] Test different environments

### 2.2 API Key Hasher
- [ ] Create [`security/api_key_hasher.py`](security/api_key_hasher.py)
- [ ] Implement `APIKeyHasher` class
  - [ ] `hash_key(key: str) -> str`
    - [ ] Use SHA-256
    - [ ] Return hex digest
  - [ ] `verify_key(key: str, key_hash: str) -> bool`
    - [ ] Hash provided key
    - [ ] Compare with stored hash
    - [ ] Use constant-time comparison
- [ ] Add unit tests: `tests/test_api_key_hasher.py`
  - [ ] Test hashing
  - [ ] Test verification
  - [ ] Test timing attack resistance

### 2.3 Database Repositories
- [ ] Create [`database/repositories/organization_repository.py`](database/repositories/organization_repository.py)
  - [ ] `get_by_id(org_id: UUID) -> Optional[Organization]`
  - [ ] `get_by_slug(slug: str) -> Optional[Organization]`
  - [ ] `get_by_email(email: str) -> Optional[Organization]`
  - [ ] `create(name, email, plan) -> Organization`
  - [ ] `update(org_id, **kwargs) -> Organization`
  - [ ] `get_all(limit, offset) -> list[Organization]`

- [ ] Create [`database/repositories/api_key_repository.py`](database/repositories/api_key_repository.py)
  - [ ] `get_by_id(key_id: UUID) -> Optional[APIKey]`
  - [ ] `get_by_hash(key_hash: str) -> Optional[APIKey]`
  - [ ] `get_by_organization(org_id: UUID) -> list[APIKey]`
  - [ ] `create(org_id, key_data) -> APIKey`
  - [ ] `update_last_used(key_id: UUID) -> None`
  - [ ] `increment_request_count(key_id: UUID) -> None`
  - [ ] `revoke(key_id: UUID, reason: str, revoked_by: UUID) -> None`
  - [ ] `delete_expired() -> int`

- [ ] Create [`database/repositories/usage_repository.py`](database/repositories/usage_repository.py)
  - [ ] `create(usage_data) -> Usage`
  - [ ] `get_by_key(key_id, start_date, end_date) -> list[Usage]`
  - [ ] `get_by_organization(org_id, start_date, end_date) -> list[Usage]`
  - [ ] `get_summary(org_id, month) -> dict`
  - [ ] `get_daily_stats(org_id, start_date, end_date) -> list[dict]`

- [ ] Update [`database/models.py`](database/models.py)
  - [ ] Add `Organization` model
  - [ ] Add `APIKey` model
  - [ ] Add `APIKeyUsage` model
  - [ ] Add `RateLimitTracking` model
  - [ ] Add relationships

- [ ] Add repository tests:
  - [ ] `tests/test_organization_repository.py`
  - [ ] `tests/test_api_key_repository.py`
  - [ ] `tests/test_usage_repository.py`

**Deliverables**:
- `security/api_key_generator.py`
- `security/api_key_hasher.py`
- `database/repositories/organization_repository.py`
- `database/repositories/api_key_repository.py`
- `database/repositories/usage_repository.py`
- Updated `database/models.py`
- Comprehensive unit tests

---

## Phase 3: API Key Service (Day 4)

### 3.1 API Key Service Implementation
- [ ] Create [`security/api_key_service.py`](security/api_key_service.py)
- [ ] Implement `APIKeyService` class
  - [ ] `__init__(key_repo, org_repo, usage_repo, hasher, generator, audit_logger)`
  - [ ] `validate_key(api_key: str) -> dict`
    - [ ] Validate key format
    - [ ] Hash key
    - [ ] Get key from database
    - [ ] Check is_active
    - [ ] Check not expired
    - [ ] Check not revoked
    - [ ] Get organization
    - [ ] Check organization is_active
    - [ ] Return auth context
  - [ ] `create_key(org_id, name, environment, scopes, expires_in_days) -> dict`
    - [ ] Check organization exists
    - [ ] Check max_api_keys limit
    - [ ] Generate key
    - [ ] Store in database
    - [ ] Log audit event
    - [ ] Return key data (including full key)
  - [ ] `revoke_key(key_id, reason, revoked_by) -> None`
    - [ ] Mark key as revoked
    - [ ] Log audit event
  - [ ] `list_keys(org_id) -> list[dict]`
    - [ ] Get all keys for organization
    - [ ] Return sanitized data (no full keys)
  - [ ] `track_usage(key_id, endpoint, method, status_code, response_time, tokens, cost) -> None`
    - [ ] Create usage record
    - [ ] Update key last_used_at
    - [ ] Increment request count
  - [ ] `get_usage_stats(org_id, start_date, end_date) -> dict`
    - [ ] Get usage summary
    - [ ] Calculate totals
    - [ ] Group by endpoint, day, etc.

### 3.2 Rate Limiter Enhancement
- [ ] Update [`security/rate_limiter.py`](security/rate_limiter.py)
- [ ] Add API key-specific rate limiting
  - [ ] `check_api_key_limit(key_id, limit) -> bool`
  - [ ] Use sliding window algorithm
  - [ ] Support Redis for production
  - [ ] Fallback to database for development
  - [ ] Return remaining requests
- [ ] Add rate limit headers helper
  - [ ] `get_rate_limit_headers(key_id, limit) -> dict`

### 3.3 Custom Exceptions
- [ ] Create [`security/api_key_exceptions.py`](security/api_key_exceptions.py)
- [ ] Define exceptions:
  - [ ] `APIKeyError` (base)
  - [ ] `InvalidAPIKeyError`
  - [ ] `ExpiredAPIKeyError`
  - [ ] `RevokedAPIKeyError`
  - [ ] `RateLimitExceededError`
  - [ ] `InsufficientScopeError`
  - [ ] `OrganizationInactiveError`

### 3.4 Tests
- [ ] Create `tests/test_api_key_service.py`
  - [ ] Test key validation (happy path)
  - [ ] Test invalid key
  - [ ] Test expired key
  - [ ] Test revoked key
  - [ ] Test key creation
  - [ ] Test key revocation
  - [ ] Test usage tracking
  - [ ] Test usage stats

**Deliverables**:
- `security/api_key_service.py`
- Updated `security/rate_limiter.py`
- `security/api_key_exceptions.py`
- Comprehensive integration tests

---

## Phase 4: FastAPI Middleware & Endpoints (Days 5-6)

### 4.1 API Key Middleware
- [ ] Create [`core/api_key_middleware.py`](core/api_key_middleware.py)
- [ ] Implement `APIKeyMiddleware` class
  - [ ] `__init__(app, api_key_service, rate_limiter, public_paths)`
  - [ ] `async def __call__(request, call_next)`
    - [ ] Check if path is public (skip auth)
    - [ ] Extract API key from Authorization header
    - [ ] Validate API key
    - [ ] Check rate limit
    - [ ] Inject auth context into `request.state.auth`
    - [ ] Process request
    - [ ] Add rate limit headers to response
    - [ ] Track usage (async)
    - [ ] Handle exceptions (401, 403, 429)
  - [ ] `extract_api_key(request) -> Optional[str]`
    - [ ] Get Authorization header
    - [ ] Extract Bearer token
  - [ ] `create_auth_context(key_data, org_data) -> dict`
    - [ ] Create context with org_id, key_id, scopes, limits

### 4.2 Scope Decorator
- [ ] Create [`core/api_key_decorators.py`](core/api_key_decorators.py)
- [ ] Implement decorators:
  - [ ] `@require_api_key` - Require valid API key
  - [ ] `@require_scope(scope: str)` - Require specific scope
  - [ ] `@require_any_scope(*scopes)` - Require any of the scopes

### 4.3 Admin Endpoints
- [ ] Create [`api/admin_api_keys.py`](api/admin_api_keys.py)
- [ ] Implement endpoints:
  - [ ] `POST /admin/organizations` - Create organization
  - [ ] `GET /admin/organizations` - List organizations
  - [ ] `GET /admin/organizations/{org_id}` - Get organization
  - [ ] `PUT /admin/organizations/{org_id}` - Update organization
  - [ ] `POST /admin/organizations/{org_id}/keys` - Create API key
  - [ ] `GET /admin/organizations/{org_id}/keys` - List keys
  - [ ] `DELETE /admin/organizations/{org_id}/keys/{key_id}` - Revoke key
  - [ ] `GET /admin/organizations/{org_id}/usage` - Get usage stats
- [ ] Add admin authentication (hardcoded admin key or separate auth)

### 4.4 Update Main App
- [ ] Update [`__main__.py`](../__main__.py)
- [ ] Add APIKeyMiddleware to app
- [ ] Register admin routes
- [ ] Configure public paths: `/health`, `/docs`, `/openapi.json`
- [ ] Add exception handlers for API key errors
- [ ] Add rate limit error handler

### 4.5 Tests
- [ ] Create `tests/test_api_key_middleware.py`
  - [ ] Test key extraction
  - [ ] Test auth context injection
  - [ ] Test public path bypass
  - [ ] Test 401 on missing key
  - [ ] Test 401 on invalid key
  - [ ] Test 429 on rate limit
- [ ] Create `tests/test_admin_api_keys.py`
  - [ ] Test organization creation
  - [ ] Test key generation
  - [ ] Test key listing
  - [ ] Test key revocation
  - [ ] Test usage stats

**Deliverables**:
- `core/api_key_middleware.py`
- `core/api_key_decorators.py`
- `api/admin_api_keys.py`
- Updated main app with middleware
- Comprehensive API tests

---

## Phase 5: Integration & CLI Tools (Day 7)

### 5.1 Update Existing Components
- [ ] Update [`core/agent_router.py`](core/agent_router.py)
  - [ ] Accept auth context from request.state.auth
  - [ ] Log organization_id and key_id with agent executions
  - [ ] Track token usage for billing
- [ ] Update [`core/conversation_memory.py`](core/conversation_memory.py)
  - [ ] Associate conversations with organization_id
  - [ ] Filter conversations by organization
- [ ] Update [`security/audit_logger.py`](security/audit_logger.py)
  - [ ] Add organization_id and key_id to audit logs
  - [ ] Add API key events (created, revoked, invalid_attempt)
- [ ] Update [`observability/centralized_logger.py`](observability/centralized_logger.py)
  - [ ] Add organization_id to log context
  - [ ] Add API key usage logging methods

### 5.2 CLI Tool for Key Management
- [ ] Create `scripts/procode_admin.py`
- [ ] Implement commands:
  - [ ] `org create --name "Acme" --email "admin@acme.com" --plan pro`
  - [ ] `org list`
  - [ ] `org show --slug acme`
  - [ ] `key create --org acme --name "Prod Key" --env live`
  - [ ] `key list --org acme`
  - [ ] `key revoke --key key_xyz --reason "Compromised"`
  - [ ] `usage --org acme --month 2026-01`
- [ ] Add to Makefile:
  - [ ] `make admin-org-create`
  - [ ] `make admin-key-create`
  - [ ] `make admin-key-list`
  - [ ] `make admin-usage`

### 5.3 Frontend Updates
- [ ] Create `frontend/components/APIKeyInput.tsx`
  - [ ] Input field for API key
  - [ ] Save to localStorage
  - [ ] Validation feedback
- [ ] Update `frontend/lib/apiClient.ts`
  - [ ] Add Authorization header with API key
  - [ ] Handle 401/429 errors
  - [ ] Show user-friendly error messages
- [ ] Update `frontend/components/AgentDashboard.tsx`
  - [ ] Add API key input section
  - [ ] Show rate limit info
  - [ ] Show usage stats (if available)

### 5.4 Documentation
- [ ] Create `docs/API_KEY_USAGE.md`
  - [ ] How to get an API key
  - [ ] How to use API key in requests
  - [ ] Rate limits and quotas
  - [ ] Error handling
  - [ ] Best practices
- [ ] Update `README.md`
  - [ ] Add API key authentication section
  - [ ] Quick start with API key
- [ ] Update `docs/API_SECURITY.md`
  - [ ] API key security best practices
  - [ ] Key rotation guidelines

### 5.5 Tests
- [ ] Create `tests/test_agent_router_api_key.py`
  - [ ] Test agent execution with API key
  - [ ] Test organization_id logging
  - [ ] Test token usage tracking
- [ ] Create `tests/integration/test_api_key_flow.py`
  - [ ] Test complete flow: create org → create key → make request
  - [ ] Test rate limiting
  - [ ] Test usage tracking
  - [ ] Test key revocation

**Deliverables**:
- Updated agent router with API key context
- CLI tool for key management
- Updated frontend with API key input
- Complete documentation
- Integration tests

---

## Phase 6: Testing & Deployment (Day 8)

### 6.1 Comprehensive Testing
- [ ] Run all unit tests: `make test`
- [ ] Run integration tests
- [ ] Test rate limiting under load
- [ ] Test with multiple organizations
- [ ] Test key expiration
- [ ] Test key revocation
- [ ] Achieve >80% code coverage

### 6.2 Security Testing
- [ ] Test API key in URL (should fail)
- [ ] Test API key in logs (should be masked)
- [ ] Test timing attacks on key verification
- [ ] Test rate limit bypass attempts
- [ ] Run security scanner: `bandit -r security/`

### 6.3 Performance Testing
- [ ] Benchmark key validation: < 10ms
- [ ] Benchmark rate limit check: < 5ms
- [ ] Test concurrent requests
- [ ] Test database query performance

### 6.4 Environment Configuration
- [ ] Update `.env.example`:
  ```bash
  # API Key Configuration
  ENABLE_API_KEY_AUTH=true
  ALLOW_UNAUTHENTICATED=false
  DEFAULT_RATE_LIMIT=60
  
  # Redis (optional, for production rate limiting)
  REDIS_URL=redis://localhost:6379/0
  
  # Admin API Key (for admin endpoints)
  ADMIN_API_KEY=pk_admin_...
  ```
- [ ] Generate production admin API key
- [ ] Update Docker Compose with env vars

### 6.5 Database Migration
- [ ] Backup production database
- [ ] Test migration on staging
- [ ] Run migration on production: `alembic upgrade head`
- [ ] Run seed script
- [ ] Verify data integrity

### 6.6 Docker Build & Deploy
- [ ] Update Dockerfile if needed
- [ ] Build images: `make docker-build-all`
- [ ] Test locally with API key
- [ ] Push to Docker Hub: `make docker-push`
- [ ] Deploy to production
- [ ] Verify API key authentication works

### 6.7 Monitoring Setup
- [ ] Add API key metrics to Grafana:
  - [ ] Requests per organization
  - [ ] Rate limit violations
  - [ ] Invalid key attempts
  - [ ] Usage by endpoint
  - [ ] Cost per organization
- [ ] Set up alerts:
  - [ ] High invalid key attempt rate
  - [ ] Rate limit violations spike
  - [ ] Unusual usage patterns
  - [ ] Cost threshold exceeded

**Deliverables**:
- All tests passing
- Security audit complete
- Production deployment
- Monitoring dashboards
- Alert rules configured

---

## Success Criteria

### Functional
- [x] Organizations can be created
- [x] API keys can be generated and managed
- [x] API key authentication works on all endpoints
- [x] Rate limiting enforces limits correctly
- [x] Usage tracking captures all requests
- [x] Keys can be revoked immediately
- [x] Expired keys are rejected
- [x] Audit logging captures all key events

### Performance
- [x] Key validation < 10ms
- [x] Rate limit check < 5ms
- [x] No performance degradation on endpoints

### Security
- [x] Keys never stored in plaintext
- [x] Keys transmitted only via HTTPS
- [x] Keys not logged in plaintext
- [x] Timing attack resistant
- [x] Rate limiting prevents abuse

### Quality
- [x] Test coverage > 80%
- [x] Documentation complete
- [x] CLI tool functional
- [x] Frontend integrated

---

## Configuration Reference

### Environment Variables
```bash
# API Key Authentication
ENABLE_API_KEY_AUTH=true
ALLOW_UNAUTHENTICATED=false
DEFAULT_RATE_LIMIT=60
ADMIN_API_KEY=pk_admin_xxx

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
USE_REDIS_RATE_LIMIT=true

# Billing
ENABLE_USAGE_TRACKING=true
ENABLE_COST_CALCULATION=true
```

### Rate Limit Tiers
| Plan | RPM | Monthly | Max Keys |
|------|-----|---------|----------|
| Free | 10 | 1,000 | 2 |
| Pro | 60 | 100,000 | 10 |
| Enterprise | 300 | 1,000,000 | 50 |

---

## Quick Start Commands

```bash
# Phase 1: Database
alembic revision -m "add_api_key_authentication"
alembic upgrade head
python scripts/seed_api_keys.py

# Phase 2-3: Development
make test-auto
make test-coverage

# Phase 4-5: Integration
python scripts/procode_admin.py org create --name "Test Org" --email "test@example.com"
python scripts/procode_admin.py key create --org test-org --name "Test Key"

# Phase 6: Deployment
make docker-build-all
make docker-push
docker-compose up -d

# Monitoring
make logs-search query="event_type:api_key"
make logs-errors
```

---

**Ready to begin implementation!** 🚀

**Estimated Completion**: 8 days from start
