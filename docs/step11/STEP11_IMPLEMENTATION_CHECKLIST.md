# Step 11: Authentication & Authorization - Implementation Checklist

This document provides a detailed, step-by-step checklist for implementing the authentication and authorization system as designed in [`STEP11_AUTH_DESIGN.md`](STEP11_AUTH_DESIGN.md).

## Overview

**Estimated Timeline**: 12 days (2.5 weeks)  
**Prerequisites**: Step 10 (Database Integration) completed ✓  
**Dependencies**: PostgreSQL, SQLAlchemy, Alembic, PyJWT, bcrypt

---

## Phase 1: Database Schema & Migrations (Day 1)

### 1.1 Create Alembic Migration
- [ ] Create new migration file: `alembic revision -m "add_authentication_tables"`
- [ ] Define `users` table enhancements (if not already complete)
  - [ ] Add `password_hash` column
  - [ ] Add `is_active`, `is_verified` columns
  - [ ] Add `last_login_at` column
  - [ ] Add `failed_login_attempts` column
  - [ ] Add `locked_until` column
  - [ ] Add indexes on `email` and `username`
- [ ] Define `roles` table
  - [ ] `id`, `name`, `description`, `created_at`
  - [ ] Unique constraint on `name`
- [ ] Define `permissions` table
  - [ ] `id`, `name`, `resource`, `action`, `description`, `created_at`
  - [ ] Unique constraint on `name`
- [ ] Define `user_roles` junction table
  - [ ] `user_id`, `role_id`, `assigned_at`, `assigned_by`
  - [ ] Composite primary key
  - [ ] Foreign key constraints with CASCADE
  - [ ] Index on `user_id`
- [ ] Define `role_permissions` junction table
  - [ ] `role_id`, `permission_id`
  - [ ] Composite primary key
  - [ ] Foreign key constraints with CASCADE
  - [ ] Index on `role_id`
- [ ] Define `refresh_tokens` table
  - [ ] `id`, `user_id`, `token_hash`, `expires_at`, `created_at`, `revoked_at`
  - [ ] `device_info`, `ip_address`
  - [ ] Indexes on `user_id`, `token_hash`, `expires_at`

### 1.2 Seed Default Data
- [ ] Create seed script: `scripts/seed_auth_data.py`
- [ ] Seed default roles:
  - [ ] `admin` - Full system access
  - [ ] `user` - Standard user access
  - [ ] `agent` - Agent-to-agent communication
  - [ ] `readonly` - Read-only access
- [ ] Seed default permissions:
  - [ ] `chat.create`, `chat.read`, `chat.update`, `chat.delete`
  - [ ] `agent.execute`, `agent.communicate`
  - [ ] `admin.users`, `admin.roles`, `admin.permissions`
  - [ ] `profile.read`, `profile.update`
- [ ] Assign permissions to roles:
  - [ ] Admin: `*.*` (all permissions)
  - [ ] User: chat.*, agent.execute, profile.*
  - [ ] Agent: agent.*, chat.read
  - [ ] Readonly: *.read
- [ ] Create default admin user (optional)
  - [ ] Username: `admin`
  - [ ] Email: `admin@procode.local`
  - [ ] Password: Generate secure password, log to console

### 1.3 Run Migration
- [ ] Test migration: `alembic upgrade head`
- [ ] Verify tables created: Check PostgreSQL
- [ ] Run seed script: `python scripts/seed_auth_data.py`
- [ ] Verify seed data: Query roles, permissions, role_permissions
- [ ] Create downgrade migration for rollback capability
- [ ] Test rollback: `alembic downgrade -1`
- [ ] Re-apply: `alembic upgrade head`

**Deliverables**:
- `alembic/versions/XXXXX_add_authentication_tables.py`
- `scripts/seed_auth_data.py`
- Updated database schema

---

## Phase 2: Core Security Components (Days 2-3)

### 2.1 Password Hashing Service
- [ ] Create [`security/password_hasher.py`](security/password_hasher.py)
- [ ] Implement `PasswordHasher` class
  - [ ] `hash_password(password: str) -> str`
    - [ ] Use bcrypt with cost factor 12
    - [ ] Return hashed password
  - [ ] `verify_password(password: str, hash: str) -> bool`
    - [ ] Use bcrypt.checkpw()
    - [ ] Return True/False
  - [ ] `is_password_strong(password: str) -> tuple[bool, list[str]]`
    - [ ] Check minimum length (8 chars)
    - [ ] Check uppercase, lowercase, digit, special char
    - [ ] Return (is_valid, error_messages)
- [ ] Add unit tests: `tests/test_password_hasher.py`
  - [ ] Test password hashing
  - [ ] Test password verification
  - [ ] Test password strength validation
  - [ ] Test bcrypt cost factor

### 2.2 JWT Handler
- [ ] Create [`security/jwt_handler.py`](security/jwt_handler.py)
- [ ] Implement `JWTHandler` class
  - [ ] `__init__(secret_key: str, algorithm: str = "HS256")`
  - [ ] `generate_access_token(user: User, roles: list, permissions: list) -> str`
    - [ ] Create payload with user info, roles, permissions
    - [ ] Set expiry: 15 minutes
    - [ ] Set type: "access"
    - [ ] Generate unique JTI
    - [ ] Sign with secret
  - [ ] `generate_refresh_token(user: User) -> str`
    - [ ] Create minimal payload (user_id only)
    - [ ] Set expiry: 7 days
    - [ ] Set type: "refresh"
    - [ ] Generate unique JTI
    - [ ] Sign with secret
  - [ ] `verify_token(token: str, token_type: str) -> dict`
    - [ ] Decode JWT
    - [ ] Verify signature
    - [ ] Check expiry
    - [ ] Validate token type
    - [ ] Return payload
  - [ ] `decode_token(token: str) -> dict`
    - [ ] Decode without verification (for debugging)
- [ ] Add custom exceptions:
  - [ ] `TokenExpiredError`
  - [ ] `TokenInvalidError`
  - [ ] `TokenTypeError`
- [ ] Add unit tests: `tests/test_jwt_handler.py`
  - [ ] Test access token generation
  - [ ] Test refresh token generation
  - [ ] Test token verification
  - [ ] Test expired token handling
  - [ ] Test invalid signature handling
  - [ ] Test token type validation

### 2.3 Database Repositories
- [ ] Enhance [`database/repositories/user_repository.py`](database/repositories/user_repository.py)
  - [ ] `get_by_email(email: str) -> Optional[User]`
  - [ ] `get_by_username(username: str) -> Optional[User]`
  - [ ] `create_user(username, email, password_hash, full_name) -> User`
  - [ ] `update_last_login(user_id: UUID) -> None`
  - [ ] `increment_failed_attempts(user_id: UUID) -> int`
  - [ ] `reset_failed_attempts(user_id: UUID) -> None`
  - [ ] `lock_account(user_id: UUID, duration_minutes: int) -> None`
  - [ ] `is_account_locked(user_id: UUID) -> bool`
  - [ ] `update_password(user_id: UUID, password_hash: str) -> None`

- [ ] Create [`database/repositories/role_repository.py`](database/repositories/role_repository.py)
  - [ ] `get_by_id(role_id: UUID) -> Optional[Role]`
  - [ ] `get_by_name(name: str) -> Optional[Role]`
  - [ ] `get_all() -> list[Role]`
  - [ ] `create_role(name: str, description: str) -> Role`
  - [ ] `get_user_roles(user_id: UUID) -> list[Role]`
  - [ ] `assign_role_to_user(user_id: UUID, role_id: UUID, assigned_by: UUID) -> None`
  - [ ] `remove_role_from_user(user_id: UUID, role_id: UUID) -> None`
  - [ ] `get_role_permissions(role_id: UUID) -> list[Permission]`

- [ ] Create [`database/repositories/permission_repository.py`](database/repositories/permission_repository.py)
  - [ ] `get_by_id(permission_id: UUID) -> Optional[Permission]`
  - [ ] `get_by_name(name: str) -> Optional[Permission]`
  - [ ] `get_all() -> list[Permission]`
  - [ ] `create_permission(name, resource, action, description) -> Permission`
  - [ ] `get_user_permissions(user_id: UUID) -> list[Permission]`
  - [ ] `assign_permission_to_role(role_id: UUID, permission_id: UUID) -> None`
  - [ ] `remove_permission_from_role(role_id: UUID, permission_id: UUID) -> None`

- [ ] Create [`database/repositories/token_repository.py`](database/repositories/token_repository.py)
  - [ ] `store_refresh_token(user_id, token_hash, expires_at, device_info, ip) -> UUID`
  - [ ] `get_by_token_hash(token_hash: str) -> Optional[RefreshToken]`
  - [ ] `is_token_revoked(token_hash: str) -> bool`
  - [ ] `revoke_token(token_hash: str) -> None`
  - [ ] `revoke_all_user_tokens(user_id: UUID) -> int`
  - [ ] `cleanup_expired_tokens() -> int`
  - [ ] `get_user_active_tokens(user_id: UUID) -> list[RefreshToken]`

- [ ] Update [`database/models.py`](database/models.py)
  - [ ] Add `Role` model
  - [ ] Add `Permission` model
  - [ ] Add `UserRole` model
  - [ ] Add `RolePermission` model
  - [ ] Add `RefreshToken` model
  - [ ] Add relationships to `User` model

- [ ] Add repository tests:
  - [ ] `tests/test_user_repository.py`
  - [ ] `tests/test_role_repository.py`
  - [ ] `tests/test_permission_repository.py`
  - [ ] `tests/test_token_repository.py`

**Deliverables**:
- `security/password_hasher.py`
- `security/jwt_handler.py`
- Enhanced `database/repositories/user_repository.py`
- `database/repositories/role_repository.py`
- `database/repositories/permission_repository.py`
- `database/repositories/token_repository.py`
- Updated `database/models.py`
- Comprehensive unit tests

---

## Phase 3: Authentication Service (Day 4)

### 3.1 Auth Service Implementation
- [ ] Create [`security/auth_service.py`](security/auth_service.py)
- [ ] Implement `AuthService` class
  - [ ] `__init__(user_repo, role_repo, token_repo, jwt_handler, password_hasher, audit_logger)`
  - [ ] `register_user(username, email, password, full_name) -> User`
    - [ ] Validate input data
    - [ ] Check password strength
    - [ ] Check email/username uniqueness
    - [ ] Hash password
    - [ ] Create user
    - [ ] Assign default "user" role
    - [ ] Log audit event
    - [ ] Return user object
  - [ ] `authenticate(email, password, device_info, ip_address) -> dict`
    - [ ] Get user by email
    - [ ] Check account locked
    - [ ] Verify password
    - [ ] Reset failed attempts on success
    - [ ] Increment failed attempts on failure
    - [ ] Lock account after 5 failures
    - [ ] Get user roles and permissions
    - [ ] Generate access token
    - [ ] Generate refresh token
    - [ ] Store refresh token
    - [ ] Update last login
    - [ ] Log audit event
    - [ ] Return tokens and user info
  - [ ] `refresh_access_token(refresh_token) -> dict`
    - [ ] Verify refresh token
    - [ ] Check token not revoked
    - [ ] Get user
    - [ ] Check user active
    - [ ] Get user roles and permissions
    - [ ] Generate new access token
    - [ ] Log audit event
    - [ ] Return new access token
  - [ ] `logout(user_id, refresh_token) -> None`
    - [ ] Decode refresh token
    - [ ] Revoke token
    - [ ] Log audit event
  - [ ] `verify_access_token(token) -> dict`
    - [ ] Verify token with JWT handler
    - [ ] Return user context
  - [ ] `change_password(user_id, old_password, new_password) -> None`
    - [ ] Get user
    - [ ] Verify old password
    - [ ] Check new password strength
    - [ ] Hash new password
    - [ ] Update password
    - [ ] Revoke all refresh tokens
    - [ ] Log audit event

### 3.2 Input Validation
- [ ] Create [`security/validators.py`](security/validators.py)
- [ ] Implement validation functions:
  - [ ] `validate_email(email: str) -> bool`
  - [ ] `validate_username(username: str) -> bool`
  - [ ] `validate_password_strength(password: str) -> tuple[bool, list[str]]`
  - [ ] `sanitize_input(text: str) -> str`

### 3.3 Custom Exceptions
- [ ] Create [`security/exceptions.py`](security/exceptions.py)
- [ ] Define custom exceptions:
  - [ ] `AuthenticationError` (base)
  - [ ] `InvalidCredentialsError`
  - [ ] `AccountLockedError`
  - [ ] `EmailAlreadyExistsError`
  - [ ] `UsernameAlreadyExistsError`
  - [ ] `WeakPasswordError`
  - [ ] `TokenExpiredError`
  - [ ] `TokenInvalidError`
  - [ ] `TokenRevokedError`
  - [ ] `PermissionDeniedError`

### 3.4 Tests
- [ ] Create `tests/test_auth_service.py`
  - [ ] Test user registration (happy path)
  - [ ] Test registration with existing email
  - [ ] Test registration with weak password
  - [ ] Test login (happy path)
  - [ ] Test login with wrong password
  - [ ] Test account lockout after 5 failures
  - [ ] Test login during lockout period
  - [ ] Test token refresh
  - [ ] Test logout
  - [ ] Test password change

**Deliverables**:
- `security/auth_service.py`
- `security/validators.py`
- `security/exceptions.py`
- Comprehensive integration tests

---

## Phase 4: RBAC Service (Day 5)

### 4.1 Permission Checker
- [ ] Create [`security/rbac_service.py`](security/rbac_service.py)
- [ ] Implement `RBACService` class
  - [ ] `__init__(permission_repo, cache_ttl=300)`
  - [ ] `check_permission(user_id, required_permission) -> bool`
    - [ ] Get user permissions (with caching)
    - [ ] Check exact match
    - [ ] Check resource wildcard (e.g., admin.*)
    - [ ] Check full wildcard (*.*)
    - [ ] Return True/False
  - [ ] `get_user_permissions(user_id) -> list[str]`
    - [ ] Check cache first
    - [ ] Query database if cache miss
    - [ ] Cache result
    - [ ] Return permission names
  - [ ] `has_role(user_id, role_name) -> bool`
    - [ ] Get user roles
    - [ ] Check if role exists
  - [ ] `has_any_role(user_id, role_names) -> bool`
    - [ ] Check if user has any of the specified roles
  - [ ] `has_all_roles(user_id, role_names) -> bool`
    - [ ] Check if user has all specified roles
  - [ ] `clear_cache(user_id) -> None`
    - [ ] Clear cached permissions for user

### 4.2 Permission Cache
- [ ] Implement in-memory cache with TTL
- [ ] Use `cachetools` library or custom implementation
- [ ] Cache key: `f"user_permissions:{user_id}"`
- [ ] TTL: 5 minutes (configurable)
- [ ] Invalidate on role/permission changes

### 4.3 Admin Service
- [ ] Create [`security/admin_service.py`](security/admin_service.py)
- [ ] Implement `AdminService` class
  - [ ] `assign_role_to_user(admin_id, user_id, role_name) -> None`
    - [ ] Check admin has permission
    - [ ] Get role by name
    - [ ] Assign role
    - [ ] Clear user permission cache
    - [ ] Log audit event
  - [ ] `remove_role_from_user(admin_id, user_id, role_name) -> None`
  - [ ] `create_role(admin_id, name, description) -> Role`
  - [ ] `create_permission(admin_id, name, resource, action, description) -> Permission`
  - [ ] `assign_permission_to_role(admin_id, role_name, permission_name) -> None`
  - [ ] `remove_permission_from_role(admin_id, role_name, permission_name) -> None`

### 4.4 Tests
- [ ] Create `tests/test_rbac_service.py`
  - [ ] Test exact permission match
  - [ ] Test resource wildcard
  - [ ] Test full wildcard
  - [ ] Test permission caching
  - [ ] Test cache invalidation
  - [ ] Test role checking
- [ ] Create `tests/test_admin_service.py`
  - [ ] Test role assignment
  - [ ] Test role removal
  - [ ] Test permission assignment

**Deliverables**:
- `security/rbac_service.py`
- `security/admin_service.py`
- Unit and integration tests

---

## Phase 5: FastAPI Middleware & Endpoints (Days 6-7)

### 5.1 Authentication Middleware
- [ ] Create [`core/auth_middleware.py`](core/auth_middleware.py)
- [ ] Implement `AuthMiddleware` class
  - [ ] `__init__(app, auth_service, rbac_service, public_paths)`
  - [ ] `async def __call__(request, call_next)`
    - [ ] Check if path is public (skip auth)
    - [ ] Extract token from Authorization header
    - [ ] Verify access token
    - [ ] Create user context
    - [ ] Inject into `request.state.user`
    - [ ] Call next middleware
    - [ ] Handle exceptions (401, 403)
  - [ ] `extract_token(request) -> Optional[str]`
    - [ ] Get Authorization header
    - [ ] Extract Bearer token
  - [ ] `create_user_context(token_payload) -> UserContext`
    - [ ] Extract user_id, roles, permissions
    - [ ] Create context object

### 5.2 Permission Decorator
- [ ] Create [`core/auth_decorators.py`](core/auth_decorators.py)
- [ ] Implement decorators:
  - [ ] `@require_auth` - Require valid authentication
  - [ ] `@require_permission(permission: str)` - Require specific permission
  - [ ] `@require_role(role: str)` - Require specific role
  - [ ] `@require_any_role(*roles)` - Require any of the roles
  - [ ] `@require_all_roles(*roles)` - Require all roles

### 5.3 Authentication Endpoints
- [ ] Create [`api/auth_routes.py`](api/auth_routes.py) (or add to existing routes)
- [ ] Implement endpoints:
  - [ ] `POST /auth/register`
    - [ ] Request: `{username, email, password, full_name}`
    - [ ] Validate input
    - [ ] Call auth_service.register_user()
    - [ ] Return 201 with user info
    - [ ] Handle errors (409 for duplicates)
  - [ ] `POST /auth/login`
    - [ ] Request: `{email, password}`
    - [ ] Get device info from User-Agent
    - [ ] Get IP from request
    - [ ] Call auth_service.authenticate()
    - [ ] Return 200 with tokens
    - [ ] Handle errors (401, 423)
  - [ ] `POST /auth/refresh`
    - [ ] Request: `{refresh_token}`
    - [ ] Call auth_service.refresh_access_token()
    - [ ] Return 200 with new access token
    - [ ] Handle errors (401)
  - [ ] `POST /auth/logout`
    - [ ] Require authentication
    - [ ] Request: `{refresh_token}`
    - [ ] Call auth_service.logout()
    - [ ] Return 200
  - [ ] `GET /auth/me`
    - [ ] Require authentication
    - [ ] Get user from request.state.user
    - [ ] Return user info with roles and permissions
  - [ ] `POST /auth/change-password`
    - [ ] Require authentication
    - [ ] Request: `{old_password, new_password}`
    - [ ] Call auth_service.change_password()
    - [ ] Return 200

### 5.4 Admin Endpoints
- [ ] Create [`api/admin_routes.py`](api/admin_routes.py)
- [ ] Implement endpoints:
  - [ ] `GET /admin/users` - List users (paginated)
  - [ ] `GET /admin/users/{user_id}` - Get user details
  - [ ] `POST /admin/users/{user_id}/roles` - Assign role
  - [ ] `DELETE /admin/users/{user_id}/roles/{role_id}` - Remove role
  - [ ] `GET /admin/roles` - List roles
  - [ ] `POST /admin/roles` - Create role
  - [ ] `GET /admin/permissions` - List permissions
  - [ ] `POST /admin/permissions` - Create permission
  - [ ] `POST /admin/roles/{role_id}/permissions` - Assign permission to role
- [ ] All endpoints require `@require_permission("admin.*")` or specific admin permissions

### 5.5 Update Main App
- [ ] Update [`__main__.py`](../__main__.py) or main FastAPI app
- [ ] Add AuthMiddleware to app
- [ ] Register auth routes
- [ ] Register admin routes
- [ ] Configure public paths (e.g., /auth/register, /auth/login, /docs)
- [ ] Add exception handlers for auth errors

### 5.6 Tests
- [ ] Create `tests/test_auth_middleware.py`
  - [ ] Test token extraction
  - [ ] Test user context injection
  - [ ] Test public path bypass
  - [ ] Test 401 on missing token
  - [ ] Test 401 on invalid token
- [ ] Create `tests/test_auth_endpoints.py`
  - [ ] Test registration endpoint
  - [ ] Test login endpoint
  - [ ] Test refresh endpoint
  - [ ] Test logout endpoint
  - [ ] Test /auth/me endpoint
- [ ] Create `tests/test_admin_endpoints.py`
  - [ ] Test user listing
  - [ ] Test role assignment
  - [ ] Test permission denied for non-admin

**Deliverables**:
- `core/auth_middleware.py`
- `core/auth_decorators.py`
- `api/auth_routes.py`
- `api/admin_routes.py`
- Updated main app with middleware
- Comprehensive API tests

---

## Phase 6: Integration with Existing Components (Day 8)

### 6.1 Update Agent Router
- [ ] Update [`core/agent_router.py`](core/agent_router.py)
- [ ] Modify `execute()` method:
  - [ ] Accept `user_context` parameter
  - [ ] Pass user_id to agents
  - [ ] Log user_id with agent executions
- [ ] Modify `execute_streaming()` method:
  - [ ] Same changes as execute()
- [ ] Update agent invocations to include user context

### 6.2 Update Conversation Memory
- [ ] Update [`core/conversation_memory.py`](core/conversation_memory.py)
- [ ] Add user_id to conversation storage
- [ ] Filter conversations by user_id
- [ ] Implement ownership checks
- [ ] Update methods:
  - [ ] `add_message(conversation_id, role, content, user_id)`
  - [ ] `get_conversation_history(conversation_id, user_id)`
  - [ ] `list_user_conversations(user_id)`

### 6.3 Update Database Repositories
- [ ] Update [`database/repositories/conversation_repository.py`](database/repositories/conversation_repository.py)
  - [ ] Add user_id column to conversations table (migration)
  - [ ] Filter queries by user_id
  - [ ] Add ownership validation
- [ ] Update [`database/repositories/message_repository.py`](database/repositories/message_repository.py)
  - [ ] Associate messages with user_id
  - [ ] Filter by user_id

### 6.4 Update Audit Logger
- [ ] Update [`security/audit_logger.py`](security/audit_logger.py)
- [ ] Add user_id to all audit log entries
- [ ] Add new event types:
  - [ ] `user_registered`
  - [ ] `login_success`
  - [ ] `login_failed`
  - [ ] `account_locked`
  - [ ] `token_refreshed`
  - [ ] `user_logout`
  - [ ] `permission_denied`
  - [ ] `role_assigned`
  - [ ] `password_changed`

### 6.5 Update Centralized Logger
- [ ] Update [`observability/centralized_logger.py`](observability/centralized_logger.py)
- [ ] Add user_id to log context
- [ ] Add authentication-specific log methods:
  - [ ] `log_auth_event(event_type, user_id, success, details)`
  - [ ] `log_permission_check(user_id, permission, granted)`

### 6.6 Tests
- [ ] Create `tests/test_agent_router_auth.py`
  - [ ] Test agent execution with user context
  - [ ] Test user_id logging
- [ ] Create `tests/test_conversation_auth.py`
  - [ ] Test conversation ownership
  - [ ] Test user filtering
  - [ ] Test unauthorized access prevention

**Deliverables**:
- Updated agent router with user context
- Updated conversation memory with ownership
- Updated repositories with user filtering
- Enhanced audit logging
- Integration tests

---

## Phase 7: Frontend Integration (Days 9-10)

### 7.1 Auth Context (React)
- [ ] Create `frontend/contexts/AuthContext.tsx`
- [ ] Implement AuthProvider:
  - [ ] State: user, accessToken, isAuthenticated, isLoading
  - [ ] Methods: login, logout, register, refreshToken
  - [ ] Auto-refresh token before expiry
  - [ ] Store refresh token in HTTP-only cookie (backend sets)
  - [ ] Store access token in memory (not localStorage)

### 7.2 Auth API Client
- [ ] Create `frontend/lib/authApi.ts`
- [ ] Implement API functions:
  - [ ] `register(username, email, password, fullName)`
  - [ ] `login(email, password)`
  - [ ] `logout(refreshToken)`
  - [ ] `refreshAccessToken(refreshToken)`
  - [ ] `getCurrentUser()`
  - [ ] `changePassword(oldPassword, newPassword)`

### 7.3 HTTP Interceptor
- [ ] Create `frontend/lib/httpClient.ts`
- [ ] Implement axios interceptor:
  - [ ] Add Authorization header with access token
  - [ ] Handle 401 responses (token expired)
  - [ ] Auto-refresh token and retry request
  - [ ] Redirect to login on refresh failure

### 7.4 Auth Pages
- [ ] Create `frontend/app/auth/login/page.tsx`
  - [ ] Email and password fields
  - [ ] Remember me checkbox
  - [ ] Login button
  - [ ] Link to register page
  - [ ] Error handling
- [ ] Create `frontend/app/auth/register/page.tsx`
  - [ ] Username, email, password, full name fields
  - [ ] Password strength indicator
  - [ ] Register button
  - [ ] Link to login page
  - [ ] Error handling
- [ ] Create `frontend/app/auth/profile/page.tsx`
  - [ ] Display user info
  - [ ] Change password form
  - [ ] Active sessions list
  - [ ] Logout button

### 7.5 Protected Routes
- [ ] Create `frontend/components/ProtectedRoute.tsx`
- [ ] Implement route protection:
  - [ ] Check authentication status
  - [ ] Redirect to login if not authenticated
  - [ ] Show loading state during check
- [ ] Wrap protected pages with ProtectedRoute

### 7.6 Permission-Based UI
- [ ] Create `frontend/hooks/usePermission.ts`
- [ ] Implement permission checking:
  - [ ] `hasPermission(permission: string): boolean`
  - [ ] `hasRole(role: string): boolean`
- [ ] Create `frontend/components/PermissionGate.tsx`
  - [ ] Show/hide UI elements based on permissions
  - [ ] Example: Hide admin menu for non-admins

### 7.7 Update Existing Components
- [ ] Update `frontend/components/AgentDashboard.tsx`
  - [ ] Add user info display
  - [ ] Add logout button
  - [ ] Show user's conversations only
- [ ] Update chat interface
  - [ ] Include access token in API calls
  - [ ] Handle 401/403 errors gracefully

### 7.8 Tests
- [ ] Create `frontend/__tests__/auth/AuthContext.test.tsx`
- [ ] Create `frontend/__tests__/auth/login.test.tsx`
- [ ] Create `frontend/__tests__/auth/register.test.tsx`
- [ ] Test protected route behavior
- [ ] Test permission-based UI rendering

**Deliverables**:
- Complete auth context and provider
- Login and registration pages
- Protected route component
- Permission-based UI components
- Updated existing components
- Frontend tests

---

## Phase 8: Testing & Quality Assurance (Days 11-12)

### 8.1 Unit Tests
- [ ] Ensure all components have unit tests
- [ ] Achieve >80% code coverage
- [ ] Run: `make test-coverage`
- [ ] Fix any failing tests

### 8.2 Integration Tests
- [ ] Create `tests/integration/test_auth_flow.py`
  - [ ] Test complete registration → login → API call → logout flow
  - [ ] Test token refresh flow
  - [ ] Test permission enforcement
  - [ ] Test account lockout flow
- [ ] Create `tests/integration/test_multi_user.py`
  - [ ] Test multiple users with different roles
  - [ ] Test conversation isolation
  - [ ] Test permission boundaries

### 8.3 Security Tests
- [ ] Create `tests/security/test_auth_security.py`
  - [ ] Test SQL injection attempts
  - [ ] Test JWT tampering
  - [ ] Test brute force protection
  - [ ] Test token expiry enforcement
  - [ ] Test permission bypass attempts
  - [ ] Test XSS prevention
  - [ ] Test CSRF protection
- [ ] Run security scanner: `bandit -r security/`

### 8.4 Performance Tests
- [ ] Create `tests/performance/