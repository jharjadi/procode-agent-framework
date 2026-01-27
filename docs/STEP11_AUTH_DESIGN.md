# Step 11: Authentication & Authorization - Design Document

## 1. Overview

This document outlines the design and architecture for implementing JWT-based authentication and role-based access control (RBAC) in the ProCode Agent Framework.

### 1.1 Goals
- Secure user authentication with JWT tokens
- Role-based access control for API endpoints
- Session management and token refresh
- Audit logging for security events
- Integration with existing database layer
- Backward compatibility with existing agents

### 1.2 Non-Goals
- OAuth2/Social login (future enhancement)
- Multi-factor authentication (future enhancement)
- Password reset via email (future enhancement)

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Login Form   │  │ Register Form│  │ Auth Context │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTP + JWT Token
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Authentication Middleware                   │   │
│  │  - Token validation                                   │   │
│  │  - User context injection                             │   │
│  │  - Rate limiting                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────┴──────────────────────────┐    │
│  │                                                      │    │
│  ▼                                                      ▼    │
│  ┌──────────────────┐                    ┌──────────────────┐
│  │  Auth Endpoints  │                    │  Protected APIs  │
│  │  /auth/register  │                    │  /chat           │
│  │  /auth/login     │                    │  /agents/*       │
│  │  /auth/refresh   │                    │  /admin/*        │
│  │  /auth/logout    │                    │                  │
│  └──────────────────┘                    └──────────────────┘
│           │                                       │           │
│           ▼                                       ▼           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Security Layer                           │   │
│  │  - Password hashing (bcrypt)                          │   │
│  │  - JWT token generation/validation                    │   │
│  │  - Permission checking                                │   │
│  │  - Audit logging                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Database Layer                           │   │
│  │  - UserRepository                                     │   │
│  │  - RoleRepository                                     │   │
│  │  - PermissionRepository                               │   │
│  │  - AuditRepository (existing)                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  users   │  │  roles   │  │permissions│  │user_roles│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │role_perms│  │  tokens  │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## 3. Database Schema

### 3.1 Users Table (Enhanced)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

### 3.2 Roles Table
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'Full system access'),
    ('user', 'Standard user access'),
    ('agent', 'Agent-to-agent communication'),
    ('readonly', 'Read-only access');
```

### 3.3 Permissions Table
```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example permissions
INSERT INTO permissions (name, resource, action, description) VALUES
    ('chat.create', 'chat', 'create', 'Create chat conversations'),
    ('chat.read', 'chat', 'read', 'Read chat conversations'),
    ('agent.execute', 'agent', 'execute', 'Execute agent tasks'),
    ('admin.users', 'admin', 'manage_users', 'Manage users'),
    ('admin.roles', 'admin', 'manage_roles', 'Manage roles');
```

### 3.4 User-Role Association
```sql
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
```

### 3.5 Role-Permission Association
```sql
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
```

### 3.6 Refresh Tokens Table
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    device_info TEXT,
    ip_address VARCHAR(45)
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

## 4. Authentication Flow

### 4.1 User Registration Sequence

```
┌──────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│Client│          │  FastAPI │          │  Auth    │          │ Database │
│      │          │          │          │ Service  │          │          │
└──┬───┘          └────┬─────┘          └────┬─────┘          └────┬─────┘
   │                   │                     │                     │
   │ POST /auth/register                     │                     │
   │ {username, email, password}             │                     │
   ├──────────────────>│                     │                     │
   │                   │                     │                     │
   │                   │ validate_input()    │                     │
   │                   ├────────────────────>│                     │
   │                   │                     │                     │
   │                   │                     │ check_existing_user()
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ user not found      │
   │                   │                     │                     │
   │                   │                     │ hash_password()     │
   │                   │                     │ (bcrypt)            │
   │                   │                     │                     │
   │                   │                     │ create_user()       │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ user_id             │
   │                   │                     │                     │
   │                   │                     │ assign_default_role()
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │ log_audit_event()   │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │<────────────────────┤                     │
   │                   │ user_created        │                     │
   │                   │                     │                     │
   │<──────────────────┤                     │                     │
   │ 201 Created       │                     │                     │
   │ {user_id, email}  │                     │                     │
   │                   │                     │                     │
```

### 4.2 User Login Sequence

```
┌──────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│Client│          │  FastAPI │          │  Auth    │          │ Database │
│      │          │          │          │ Service  │          │          │
└──┬───┘          └────┬─────┘          └────┬─────┘          └────┬─────┘
   │                   │                     │                     │
   │ POST /auth/login  │                     │                     │
   │ {email, password} │                     │                     │
   ├──────────────────>│                     │                     │
   │                   │                     │                     │
   │                   │ authenticate()      │                     │
   │                   ├────────────────────>│                     │
   │                   │                     │                     │
   │                   │                     │ get_user_by_email() │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ user_data           │
   │                   │                     │                     │
   │                   │                     │ verify_password()   │
   │                   │                     │ (bcrypt.verify)     │
   │                   │                     │                     │
   │                   │                     │ check_account_locked()
   │                   │                     │                     │
   │                   │                     │ get_user_roles()    │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ roles & permissions │
   │                   │                     │                     │
   │                   │                     │ generate_access_token()
   │                   │                     │ (JWT, 15min expiry) │
   │                   │                     │                     │
   │                   │                     │ generate_refresh_token()
   │                   │                     │ (JWT, 7day expiry)  │
   │                   │                     │                     │
   │                   │                     │ store_refresh_token()
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │ update_last_login() │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │ log_audit_event()   │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │<────────────────────┤                     │
   │                   │ tokens              │                     │
   │                   │                     │                     │
   │<──────────────────┤                     │                     │
   │ 200 OK            │                     │                     │
   │ {access_token,    │                     │                     │
   │  refresh_token,   │                     │                     │
   │  user_info}       │                     │                     │
   │                   │                     │                     │
```

### 4.3 Protected Request Sequence

```
┌──────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│Client│          │  FastAPI │          │  Auth    │          │ Agent    │
│      │          │Middleware│          │ Service  │          │ Router   │
└──┬───┘          └────┬─────┘          └────┬─────┘          └────┬─────┘
   │                   │                     │                     │
   │ POST /chat        │                     │                     │
   │ Authorization: Bearer <token>           │                     │
   ├──────────────────>│                     │                     │
   │                   │                     │                     │
   │                   │ extract_token()     │                     │
   │                   │                     │                     │
   │                   │ verify_token()      │                     │
   │                   ├────────────────────>│                     │
   │                   │                     │                     │
   │                   │                     │ decode_jwt()        │
   │                   │                     │ validate_signature()│
   │                   │                     │ check_expiry()      │
   │                   │                     │                     │
   │                   │<────────────────────┤                     │
   │                   │ user_context        │                     │
   │                   │ {user_id, roles,    │                     │
   │                   │  permissions}       │                     │
   │                   │                     │                     │
   │                   │ check_permission()  │                     │
   │                   ├────────────────────>│                     │
   │                   │ "chat.create"       │                     │
   │                   │                     │                     │
   │                   │<────────────────────┤                     │
   │                   │ authorized          │                     │
   │                   │                     │                     │
   │                   │ inject_user_context()                     │
   │                   │ request.state.user = user_context         │
   │                   │                     │                     │
   │                   │ forward_request()   │                     │
   │                   ├─────────────────────────────────────────>│
   │                   │                     │                     │
   │                   │                     │                     │
   │                   │<─────────────────────────────────────────┤
   │                   │ response            │                     │
   │                   │                     │                     │
   │<──────────────────┤                     │                     │
   │ 200 OK            │                     │                     │
   │ {response_data}   │                     │                     │
   │                   │                     │                     │
```

### 4.4 Token Refresh Sequence

```
┌──────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│Client│          │  FastAPI │          │  Auth    │          │ Database │
│      │          │          │          │ Service  │          │          │
└──┬───┘          └────┬─────┘          └────┬─────┘          └────┬─────┘
   │                   │                     │                     │
   │ POST /auth/refresh                      │                     │
   │ {refresh_token}   │                     │                     │
   ├──────────────────>│                     │                     │
   │                   │                     │                     │
   │                   │ refresh_access_token()                    │
   │                   ├────────────────────>│                     │
   │                   │                     │                     │
   │                   │                     │ verify_refresh_token()
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │                     │<────────────────────┤
   │                   │                     │ token_valid         │
   │                   │                     │                     │
   │                   │                     │ generate_new_access_token()
   │                   │                     │ (JWT, 15min expiry) │
   │                   │                     │                     │
   │                   │                     │ log_audit_event()   │
   │                   │                     ├────────────────────>│
   │                   │                     │                     │
   │                   │<────────────────────┤                     │
   │                   │ new_access_token    │                     │
   │                   │                     │                     │
   │<──────────────────┤                     │                     │
   │ 200 OK            │                     │                     │
   │ {access_token}    │                     │                     │
   │                   │                     │                     │
```

## 5. JWT Token Structure

### 5.1 Access Token Payload
```json
{
  "sub": "user_id_uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "roles": ["user"],
  "permissions": ["chat.create", "chat.read", "agent.execute"],
  "type": "access",
  "iat": 1706000000,
  "exp": 1706000900,
  "jti": "unique_token_id"
}
```

**Expiry**: 15 minutes

### 5.2 Refresh Token Payload
```json
{
  "sub": "user_id_uuid",
  "type": "refresh",
  "iat": 1706000000,
  "exp": 1706604800,
  "jti": "unique_token_id"
}
```

**Expiry**: 7 days

## 6. Authorization Model (RBAC)

### 6.1 Permission Format
```
<resource>.<action>
```

Examples:
- `chat.create` - Create chat conversations
- `chat.read` - Read chat conversations
- `agent.execute` - Execute agent tasks
- `admin.users` - Manage users
- `admin.roles` - Manage roles

### 6.2 Default Role Permissions

**Admin Role**:
- `*.*` (all permissions)

**User Role**:
- `chat.create`
- `chat.read`
- `chat.update`
- `chat.delete` (own conversations only)
- `agent.execute`
- `profile.read`
- `profile.update`

**Agent Role** (for A2A communication):
- `agent.execute`
- `agent.communicate`
- `chat.read`

**Readonly Role**:
- `chat.read`
- `profile.read`

### 6.3 Permission Checking Logic

```python
def check_permission(user: User, permission: str) -> bool:
    """
    Check if user has the required permission.
    
    Logic:
    1. Get all user's roles
    2. Get all permissions for those roles
    3. Check if required permission exists
    4. Support wildcard permissions (admin.* or *.*)
    """
    user_permissions = get_user_permissions(user.id)
    
    # Check exact match
    if permission in user_permissions:
        return True
    
    # Check wildcard matches
    resource, action = permission.split('.')
    
    # Check resource wildcard (e.g., admin.*)
    if f"{resource}.*" in user_permissions:
        return True
    
    # Check full wildcard (e.g., *.*)
    if "*.*" in user_permissions:
        return True
    
    return False
```

## 7. Security Considerations

### 7.1 Password Security
- **Hashing**: bcrypt with cost factor 12
- **Minimum length**: 8 characters
- **Complexity**: Require uppercase, lowercase, number, special char
- **Storage**: Never store plaintext passwords

### 7.2 Token Security
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Secret**: Strong random secret (256-bit minimum)
- **Rotation**: Support secret rotation without downtime
- **Revocation**: Store refresh tokens for revocation capability

### 7.3 Rate Limiting
- **Login attempts**: 5 attempts per 15 minutes per IP
- **Account lockout**: Lock account for 30 minutes after 5 failed attempts
- **Token refresh**: 10 requests per hour per user
- **API calls**: 100 requests per minute per user

### 7.4 Audit Logging
Log all security events:
- User registration
- Login attempts (success/failure)
- Token refresh
- Permission denied
- Account lockout
- Password changes
- Role/permission changes

### 7.5 HTTPS Only
- All authentication endpoints must use HTTPS
- Set secure cookie flags
- Implement HSTS headers

## 8. API Endpoints

### 8.1 Authentication Endpoints

#### POST /auth/register
```json
Request:
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}

Response (201):
{
  "user_id": "uuid",
  "username": "johndoe",
  "email": "john@example.com",
  "created_at": "2026-01-27T00:00:00Z"
}
```

#### POST /auth/login
```json
Request:
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}

Response (200):
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "username": "johndoe",
    "email": "john@example.com",
    "roles": ["user"]
  }
}
```

#### POST /auth/refresh
```json
Request:
{
  "refresh_token": "eyJhbGc..."
}

Response (200):
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### POST /auth/logout
```json
Request:
Headers: Authorization: Bearer <access_token>
{
  "refresh_token": "eyJhbGc..."
}

Response (200):
{
  "message": "Successfully logged out"
}
```

#### GET /auth/me
```json
Request:
Headers: Authorization: Bearer <access_token>

Response (200):
{
  "id": "uuid",
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "roles": ["user"],
  "permissions": ["chat.create", "chat.read", "agent.execute"],
  "created_at": "2026-01-27T00:00:00Z",
  "last_login_at": "2026-01-27T01:00:00Z"
}
```

### 8.2 Admin Endpoints (Require admin role)

#### GET /admin/users
List all users with pagination

#### POST /admin/users/{user_id}/roles
Assign roles to user

#### DELETE /admin/users/{user_id}/roles/{role_id}
Remove role from user

#### GET /admin/roles
List all roles

#### POST /admin/roles
Create new role

#### GET /admin/permissions
List all permissions

## 9. Integration Points

### 9.1 Existing Components

**Agent Router** ([`core/agent_router.py`](core/agent_router.py)):
- Add user context to agent execution
- Log user_id with agent actions
- Check permissions before agent execution

**Conversation Memory** ([`core/conversation_memory.py`](core/conversation_memory.py)):
- Associate conversations with user_id
- Filter conversations by user
- Implement conversation ownership checks

**Audit Logger** ([`security/audit_logger.py`](security/audit_logger.py)):
- Already exists, enhance with auth events
- Add user_id to all audit logs

**Database Repositories** ([`database/repositories/`](database/repositories/)):
- UserRepository already exists, enhance with auth methods
- Create RoleRepository
- Create PermissionRepository

### 9.2 New Components to Create

1. **`security/auth_service.py`**
   - User registration
   - Login/logout
   - Token generation/validation
   - Password hashing/verification

2. **`security/jwt_handler.py`**
   - JWT token creation
   - Token validation
   - Token refresh logic

3. **`security/rbac_service.py`**
   - Permission checking
   - Role management
   - Permission management

4. **`core/auth_middleware.py`**
   - FastAPI middleware for token validation
   - User context injection
   - Permission checking decorator

5. **`database/repositories/role_repository.py`**
   - CRUD operations for roles
   - Role-permission associations

6. **`database/repositories/permission_repository.py`**
   - CRUD operations for permissions
   - Permission queries

7. **`database/repositories/token_repository.py`**
   - Refresh token storage
   - Token revocation

## 10. Migration Strategy

### 10.1 Database Migrations
1. Create Alembic migration for new tables
2. Seed default roles and permissions
3. Create default admin user
4. Migrate existing users (if any)

### 10.2 Backward Compatibility
- Make authentication optional initially (feature flag)
- Provide anonymous user context for unauthenticated requests
- Gradually enforce authentication on endpoints

### 10.3 Rollout Plan
1. **Phase 1**: Database schema + repositories
2. **Phase 2**: Auth service + JWT handler
3. **Phase 3**: Middleware + protected endpoints
4. **Phase 4**: Frontend integration
5. **Phase 5**: Enable enforcement + monitoring

## 11. Testing Strategy

### 11.1 Unit Tests
- Password hashing/verification
- JWT token generation/validation
- Permission checking logic
- Repository methods

### 11.2 Integration Tests
- Registration flow
- Login flow
- Token refresh flow
- Protected endpoint access
- Permission denied scenarios

### 11.3 Security Tests
- SQL injection attempts
- JWT tampering
- Brute force protection
- Token expiry enforcement
- Permission bypass attempts

## 12. Monitoring & Metrics

### 12.1 Key Metrics
- Login success/failure rate
- Token refresh rate
- Permission denied count
- Account lockout count
- Average token lifetime

### 12.2 Alerts
- High login failure rate (potential attack)
- Unusual token refresh patterns
- Permission denied spikes
- Account lockout threshold exceeded

## 13. Configuration

### 13.1 Environment Variables
```bash
# JWT Configuration
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true

# Rate Limiting
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW_MINUTES=15
ACCOUNT_LOCKOUT_DURATION_MINUTES=30

# Security
BCRYPT_COST_FACTOR=12
ENABLE_AUTH=true
ALLOW_ANONYMOUS=false
```

## 14. Documentation Requirements

### 14.1 User Documentation
- How to register/login
- Token management
- API authentication guide

### 14.2 Developer Documentation
- Authentication flow diagrams
- Permission system guide
- Integration examples
- Testing guide

### 14.3 Admin Documentation
- User management
- Role/permission management
- Security monitoring
- Troubleshooting guide

## 15. Open Questions for Discussion

1. **Token Storage**: Should we use HTTP-only cookies or localStorage for frontend?
   - **Recommendation**: HTTP-only cookies for refresh tokens, memory for access tokens

2. **Password Reset**: Should we implement email-based password reset in this phase?
   - **Recommendation**: Defer to future phase, focus on core auth first

3. **Session Management**: Should we support multiple concurrent sessions per user?
   - **Recommendation**: Yes, track device_info in refresh_tokens table

4. **API Key Authentication**: Should we support API keys for programmatic access?
   - **Recommendation**: Yes, add in Phase 2 after core auth is stable

5. **Rate Limiting Storage**: Redis or in-memory for rate limiting?
   - **Recommendation**: Start with in-memory, migrate to Redis for production

## 16. Success Criteria

- [ ] Users can register and login successfully
- [ ] JWT tokens are generated and validated correctly
- [ ] Protected endpoints require valid authentication
- [ ] RBAC system enforces permissions correctly
- [ ] All security events are audit logged
- [ ] Rate limiting prevents brute force attacks
- [ ] Token refresh works seamlessly
- [ ] Frontend integrates with auth system
- [ ] All tests pass (unit + integration + security)
- [ ] Documentation is complete and accurate

## 17. Timeline Estimate

- **Database Schema & Migrations**: 1 day
- **Auth Service & JWT Handler**: 2 days
- **RBAC Service**: 1 day
- **Middleware & Decorators**: 1 day
- **API Endpoints**: 2 days
- **Frontend Integration**: 2 days
- **Testing**: 2 days
- **Documentation**: 1 day

**Total**: ~12 days (2.5 weeks)

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-27  
**Author**: ProCode Agent Framework Team  
**Status