# Database Integration Guide

## Overview

Step 10 of the Production Roadmap implements database integration and persistence for the Procode Agent Framework. This provides long-term storage for conversations, messages, audit logs, and user data.

## Architecture

### Database Support

The framework supports two database backends:

1. **SQLite** (Development)
   - File-based database: `data/procode.db`
   - No additional setup required
   - Perfect for local development and testing

2. **PostgreSQL** (Production)
   - Scalable, production-ready database
   - Supports connection pooling
   - Recommended for production deployments

### Database Models

Located in [`database/models.py`](../database/models.py):

#### User Model
- **Purpose**: Store user accounts and authentication
- **Fields**: email, username, hashed_password, role, api_key, timestamps
- **Indexes**: email, username, api_key for fast lookups
- **Note**: Full implementation in Step 11 (Authentication)

#### Conversation Model
- **Purpose**: Track conversation sessions
- **Fields**: user_id, title, intent, status, timestamps
- **Relationships**: One-to-many with Messages
- **Indexes**: user_id, status for efficient queries

#### Message Model
- **Purpose**: Store individual messages in conversations
- **Fields**: conversation_id, role, content, intent, model_used, cost, extra_metadata
- **Relationships**: Many-to-one with Conversation
- **Indexes**: conversation_id, role, created_at for fast retrieval

#### AuditLog Model
- **Purpose**: Compliance and security audit trail
- **Fields**: user_id, event_type, event_category, severity, description, extra_metadata
- **Indexes**: Multiple composite indexes for efficient querying
- **Categories**: security, compliance, access, system, general

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Database Configuration
DATABASE_URL=sqlite:///data/procode.db  # SQLite (development)
# DATABASE_URL=postgresql://user:password@localhost:5432/procode  # PostgreSQL (production)

# Optional: Enable database persistence
USE_DATABASE=false  # Set to 'true' to enable

# PostgreSQL Connection Pooling (if using PostgreSQL)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
SQL_ECHO=false  # Set to 'true' for SQL query logging
```

### Database Selection

The framework automatically detects the database type from `DATABASE_URL`:
- Starts with `sqlite:` → SQLite mode
- Starts with `postgresql:` → PostgreSQL mode

## Repository Pattern

The framework uses the Repository pattern for data access, providing a clean abstraction layer.

### Available Repositories

Located in [`database/repositories/`](../database/repositories/):

#### ConversationRepository
```python
from database.repositories.conversation_repository import ConversationRepository

# Create conversation
conversation = repo.create_conversation(
    user_id=1,
    title="Customer Support Chat",
    intent="support"
)

# Add message
repo.add_message(
    conversation_id=conversation.id,
    role="user",
    content="Hello, I need help",
    intent="greeting",
    model_used="gpt-4",
    cost=0.002
)

# Get messages
messages = repo.get_conversation_messages(conversation.id)

# Get conversation cost
total_cost = repo.get_conversation_cost(conversation.id)
```

#### AuditRepository
```python
from database.repositories.audit_repository import AuditRepository

# Create audit log
repo.create_audit_log(
    user_id=1,
    event_type="blocked_content",
    event_category="security",
    severity="warning",
    description="PII detected in user input",
    extra_metadata={"pii_types": ["email", "phone"]}
)

# Query logs
logs = repo.get_user_audit_logs(user_id=1, limit=50)
security_logs = repo.get_logs_by_type("blocked_content")
```

## Integration with Existing Components

### ConversationMemory

The [`ConversationMemory`](../core/conversation_memory.py) class now supports optional database persistence:

```python
from core.conversation_memory import ConversationMemory

# With database persistence
memory = ConversationMemory(use_database=True)

# Add message (automatically persists to DB if enabled)
memory.add_message(
    conversation_id="conv_123",
    role="user",
    content="Hello",
    user_id=1,  # Required for DB persistence
    intent="greeting",
    model_used="gpt-4",
    cost=0.001
)

# Load from database
history = memory.get_history("conv_123", from_database=True)
```

**Features:**
- In-memory caching for fast access
- Optional database persistence via `USE_DATABASE` env var
- Backward compatible (works without database)
- Automatic conversation creation on first message

### AuditLogger

The [`AuditLogger`](../security/audit_logger.py) class now supports database persistence:

```python
from security.audit_logger import AuditLogger

# With database persistence
logger = AuditLogger(use_database=True)

# Log event (writes to file AND database if enabled)
logger.log_event(
    event_type="blocked_content",
    details={"reason": "PII detected"},
    user_id="1",
    severity="warning"
)
```

**Features:**
- Dual logging: JSON files + database
- Automatic event categorization
- User ID conversion (string → int for DB)
- Graceful fallback if database unavailable

## Database Migrations

### Using Alembic

The framework uses Alembic for database schema migrations.

#### Initial Setup

Already completed in Step 10:
```bash
# Initialize Alembic (already done)
alembic init alembic

# Create initial migration (already done)
alembic revision --autogenerate -m "Initial migration"
```

#### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

#### Create New Migration

When you modify models:
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to User model"

# Review the generated migration file in alembic/versions/
# Then apply it
alembic upgrade head
```

## Testing

### Test Database Integration

Run the test script:
```bash
python test_database.py
```

This verifies:
- ✓ Database initialization
- ✓ Table creation
- ✓ Repository operations
- ✓ CRUD functionality

### Manual Testing

```python
from database.connection import init_db, get_db
from database.repositories.conversation_repository import ConversationRepository

# Initialize database
init_db()

# Get session
db = next(get_db())

# Create repository
repo = ConversationRepository(db)

# Test operations
conversation = repo.create_conversation(user_id=1, title="Test")
print(f"Created conversation: {conversation.id}")

# Clean up
db.close()
```

## Production Deployment

### PostgreSQL Setup

1. **Install PostgreSQL**
   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql
   
   # Ubuntu
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Create Database**
   ```bash
   psql postgres
   CREATE DATABASE procode;
   CREATE USER procode_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE procode TO procode_user;
   \q
   ```

3. **Update Environment**
   ```bash
   DATABASE_URL=postgresql://procode_user:secure_password@localhost:5432/procode
   USE_DATABASE=true
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   ```

4. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

### Connection Pooling

PostgreSQL mode automatically enables connection pooling:
- **Pool Size**: Number of persistent connections (default: 5)
- **Max Overflow**: Additional connections when pool is full (default: 10)
- **Total Capacity**: pool_size + max_overflow = 15 connections

Configure via environment variables:
```bash
DB_POOL_SIZE=10        # Persistent connections
DB_MAX_OVERFLOW=20     # Burst capacity
```

## Performance Considerations

### Indexes

All models include strategic indexes for common queries:
- **User**: email, username, api_key
- **Conversation**: user_id, status, (user_id, updated_at)
- **Message**: conversation_id, (conversation_id, created_at)
- **AuditLog**: user_id, event_type, severity, created_at

### Query Optimization

```python
# Good: Use indexes
messages = repo.get_conversation_messages(conversation_id)

# Good: Limit results
recent_logs = repo.get_user_audit_logs(user_id, limit=100)

# Good: Filter by indexed fields
security_logs = repo.get_logs_by_type("blocked_content")
```

### Caching Strategy

- **ConversationMemory**: In-memory cache with database fallback
- **Load from DB**: Only when cache miss or explicitly requested
- **Write-through**: Updates both cache and database

## Troubleshooting

### Common Issues

#### 1. "No module named 'sqlalchemy'"
```bash
# Install dependencies
make install
# or
pip install sqlalchemy alembic psycopg2-binary
```

#### 2. "Database connection failed"
```bash
# Check DATABASE_URL in .env
# Verify database is running
# Test connection:
psql $DATABASE_URL
```

#### 3. "Table does not exist"
```bash
# Run migrations
alembic upgrade head
```

#### 4. "Reserved word 'metadata'"
Fixed in Step 10 - we use `extra_metadata` instead.

### Debug Mode

Enable SQL query logging:
```bash
SQL_ECHO=true
```

This prints all SQL queries to console for debugging.

## Next Steps

### Step 11: Authentication & Authorization

The database foundation is ready for:
- User registration and login
- Password hashing (bcrypt)
- API key generation
- Role-based access control (RBAC)
- Session management

### Future Enhancements

- **Read Replicas**: For scaling read operations
- **Sharding**: For horizontal scaling
- **Caching Layer**: Redis for frequently accessed data
- **Full-text Search**: PostgreSQL FTS or Elasticsearch
- **Time-series Data**: For metrics and analytics

## File Structure

```
procode-agent-framework/
├── database/
│   ├── __init__.py              # Package exports
│   ├── connection.py            # Database connection & session management
│   ├── models.py                # SQLAlchemy models
│   └── repositories/
│       ├── __init__.py
│       ├── conversation_repository.py
│       ├── user_repository.py
│       ├── message_repository.py
│       └── audit_repository.py
├── alembic/
│   ├── env.py                   # Alembic configuration
│   ├── script.py.mako           # Migration template
│   └── versions/                # Migration files
│       └── 5c6758e838d3_initial_migration.py
├── alembic.ini                  # Alembic settings
├── test_database.py             # Database integration tests
└── docs/
    └── DATABASE_INTEGRATION.md  # This file
```

## Summary

Step 10 successfully implements:

✅ **Database Models**: User, Conversation, Message, AuditLog  
✅ **Dual Database Support**: SQLite (dev) + PostgreSQL (prod)  
✅ **Repository Pattern**: Clean data access layer  
✅ **Migration System**: Alembic for schema management  
✅ **Integration**: ConversationMemory + AuditLogger persistence  
✅ **Testing**: Comprehensive test suite  
✅ **Documentation**: Complete setup and usage guide  

The framework now has a solid persistence layer ready for production use!
