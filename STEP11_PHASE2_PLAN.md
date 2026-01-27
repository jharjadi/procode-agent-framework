# Step 11 Phase 2: Core Security Components

## Status: Ready to Start

## Phase 1 Completion ✅
- ✅ Database schema created (4 tables: organizations, api_keys, api_key_usage, rate_limit_tracking)
- ✅ Alembic migration tested (upgrade/downgrade/re-upgrade)
- ✅ Seed script creates default organization and test API key
- ✅ PostgreSQL migration complete (removed SQLite)
- ✅ Documentation comprehensive
- ✅ Changes committed and pushed to Git
- ✅ Docker images built and pushed to production
- ✅ Production deployment verified working

## Phase 2 Tasks (Days 2-3)

### 2.1 API Key Generator ⏳
**File**: `security/api_key_generator.py`

**Implementation**:
```python
class APIKeyGenerator:
    def generate_key(environment='live') -> dict:
        # Use secrets.token_urlsafe(32) for secure random token
        # Create key with prefix: pk_{environment}_{token}
        # Hash key with SHA-256
        # Extract last 4 chars as hint
        # Return full_key, key_hash, key_hint, key_prefix
    
    def validate_key_format(key: str) -> bool:
        # Check prefix format (pk_live_ or pk_test_)
        # Check length (should be ~50 chars)
        # Check character set (URL-safe base64)
```

**Tests**: `tests/test_api_key_generator.py`
- Test key generation
- Test key format validation
- Test uniqueness
- Test different environments (live, test)

---

### 2.2 API Key Hasher ⏳
**File**: `security/api_key_hasher.py`

**Implementation**:
```python
class APIKeyHasher:
    def hash_key(key: str) -> str:
        # Use SHA-256
        # Return hex digest
    
    def verify_key(key: str, key_hash: str) -> bool:
        # Hash provided key
        # Compare with stored hash
        # Use constant-time comparison (secrets.compare_digest)
```

**Tests**: `tests/test_api_key_hasher.py`
- Test hashing
- Test verification
- Test timing attack resistance

---

### 2.3 Database Repositories ⏳

#### Organization Repository
**File**: `database/repositories/organization_repository.py`

**Methods**:
- `get_by_id(org_id: UUID) -> Optional[Organization]`
- `get_by_slug(slug: str) -> Optional[Organization]`
- `get_by_email(email: str) -> Optional[Organization]`
- `create(name, email, plan) -> Organization`
- `update(org_id, **kwargs) -> Organization`
- `get_all(limit, offset) -> list[Organization]`

#### API Key Repository
**File**: `database/repositories/api_key_repository.py`

**Methods**:
- `get_by_id(key_id: UUID) -> Optional[APIKey]`
- `get_by_hash(key_hash: str) -> Optional[APIKey]`
- `get_by_organization(org_id: UUID) -> list[APIKey]`
- `create(org_id, key_data) -> APIKey`
- `update_last_used(key_id: UUID) -> None`
- `increment_request_count(key_id: UUID) -> None`
- `revoke(key_id: UUID, reason: str, revoked_by: UUID) -> None`
- `delete_expired() -> int`

#### Usage Repository
**File**: `database/repositories/usage_repository.py`

**Methods**:
- `create(usage_data) -> Usage`
- `get_by_key(key_id, start_date, end_date) -> list[Usage]`
- `get_by_organization(org_id, start_date, end_date) -> list[Usage]`
- `get_summary(org_id, month) -> dict`
- `get_daily_stats(org_id, start_date, end_date) -> list[dict]`

#### Database Models
**File**: `database/models.py` (update)

**Add Models**:
- `Organization` - SQLAlchemy model
- `APIKey` - SQLAlchemy model
- `APIKeyUsage` - SQLAlchemy model
- `RateLimitTracking` - SQLAlchemy model
- Add relationships between models

**Tests**:
- `tests/test_organization_repository.py`
- `tests/test_api_key_repository.py`
- `tests/test_usage_repository.py`

---

## Implementation Order

1. **Start with API Key Generator** (30 min)
   - Simple, no dependencies
   - Can test immediately
   - Needed by other components

2. **API Key Hasher** (20 min)
   - Simple, no dependencies
   - Needed by repositories

3. **Database Models** (40 min)
   - Update `database/models.py`
   - Add SQLAlchemy models for 4 tables
   - Define relationships

4. **Organization Repository** (30 min)
   - Simplest repository
   - No complex queries

5. **API Key Repository** (45 min)
   - More complex
   - Multiple query methods
   - Update operations

6. **Usage Repository** (45 min)
   - Most complex
   - Aggregation queries
   - Date range filtering

7. **Write Tests** (60 min)
   - Unit tests for generator and hasher
   - Integration tests for repositories

---

## Estimated Time: 4-5 hours

## Deliverables
- ✅ `security/api_key_generator.py`
- ✅ `security/api_key_hasher.py`
- ✅ `database/repositories/organization_repository.py`
- ✅ `database/repositories/api_key_repository.py`
- ✅ `database/repositories/usage_repository.py`
- ✅ Updated `database/models.py`
- ✅ Comprehensive unit tests

---

## Next Steps After Phase 2
**Phase 3**: API Key Service (Day 4)
- Create `security/api_key_service.py`
- Orchestrate all components
- Implement business logic
- Add rate limiting integration

---

## Ready to Start? 🚀

Run these commands to begin:
```bash
# Create test files
touch tests/test_api_key_generator.py
touch tests/test_api_key_hasher.py
touch tests/test_organization_repository.py
touch tests/test_api_key_repository.py
touch tests/test_usage_repository.py

# Start implementation
# 1. security/api_key_generator.py
# 2. security/api_key_hasher.py
# 3. database/models.py (update)
# 4. database/repositories/organization_repository.py
# 5. database/repositories/api_key_repository.py
# 6. database/repositories/usage_repository.py
```
