# PostgreSQL Setup Guide

## Overview

The ProCode Agent Framework uses **PostgreSQL for both development and production** to ensure production parity and eliminate database-specific bugs.

## Why PostgreSQL Everywhere?

✅ **Production Parity** - Same database engine in dev and prod  
✅ **No Surprises** - What works locally works in production  
✅ **Full Features** - Use PostgreSQL-specific features freely (JSONB, arrays, UUID, etc.)  
✅ **Simpler Code** - No conditional logic for different databases  
✅ **Better Testing** - Catch PostgreSQL-specific issues early  

## Local Development Setup

### Option 1: Docker Compose (Recommended)

The easiest way to run PostgreSQL locally is using Docker Compose.

#### 1. Start PostgreSQL

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Check if it's running
docker-compose ps postgres
```

#### 2. Configure Environment

Create a `.env` file (or copy from `.env.example`):

```bash
# Copy example
cp .env.example .env

# The default DATABASE_URL for local development
DATABASE_URL=postgresql://procode_user:changeme@localhost:5433/procode
POSTGRES_PASSWORD=changeme
```

**Note**: PostgreSQL runs on port **5433** on your host machine to avoid conflicts with any existing PostgreSQL installation on port 5432.

#### 3. Run Migrations

```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
alembic upgrade head

# Seed default data
python scripts/seed_api_keys.py
```

#### 4. Verify Setup

```bash
# Check tables
python -c "
from sqlalchemy import create_engine, inspect
from database.connection import get_database_url

engine = create_engine(get_database_url())
inspector = inspect(engine)
print('Tables:', inspector.get_table_names())
"
```

### Option 2: Local PostgreSQL Installation

If you prefer to install PostgreSQL directly on your machine:

#### macOS (Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database and user
psql postgres
CREATE DATABASE procode;
CREATE USER procode_user WITH PASSWORD 'changeme';
GRANT ALL PRIVILEGES ON DATABASE procode TO procode_user;
\q
```

#### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE procode;
CREATE USER procode_user WITH PASSWORD 'changeme';
GRANT ALL PRIVILEGES ON DATABASE procode TO procode_user;
\q
```

#### Update .env

```bash
# For local installation (default port 5432)
DATABASE_URL=postgresql://procode_user:changeme@localhost:5432/procode
```

## Production Setup

### Environment Variables

Set these environment variables in your production environment:

```bash
# Production database URL
DATABASE_URL=postgresql://user:password@prod-host:5432/procode_db

# Connection pool settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# PostgreSQL password (for docker-compose)
POSTGRES_PASSWORD=<strong-random-password>
```

### Security Best Practices

1. **Use Strong Passwords**
   ```bash
   # Generate a secure password
   openssl rand -base64 32
   ```

2. **Restrict Network Access**
   - Only allow connections from your application servers
   - Use SSL/TLS for connections
   - Configure `pg_hba.conf` properly

3. **Regular Backups**
   ```bash
   # Backup database
   pg_dump -U procode_user -h localhost procode > backup.sql
   
   # Restore database
   psql -U procode_user -h localhost procode < backup.sql
   ```

4. **Connection Pooling**
   - Use appropriate pool sizes (default: 5-10)
   - Monitor connection usage
   - Set `pool_pre_ping=True` (already configured)

## Docker Compose Configuration

The `docker-compose.yml` includes PostgreSQL with the following configuration:

```yaml
postgres:
  image: postgres:15-alpine
  container_name: procode-postgres
  environment:
    POSTGRES_DB: procode
    POSTGRES_USER: procode_user
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
  volumes:
    - postgres_data:/var/lib/postgresql/data
  ports:
    - "5433:5432"  # Host:Container
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U procode_user -d procode"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Key Features

- **Persistent Storage**: Data stored in `postgres_data` volume
- **Health Checks**: Ensures database is ready before starting app
- **Port Mapping**: 5433 on host → 5432 in container (avoids conflicts)
- **Alpine Image**: Smaller image size

## Common Commands

### Docker Compose

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Stop PostgreSQL
docker-compose stop postgres

# View logs
docker-compose logs -f postgres

# Restart PostgreSQL
docker-compose restart postgres

# Remove PostgreSQL (keeps data)
docker-compose down

# Remove PostgreSQL and data
docker-compose down -v
```

### Database Management

```bash
# Connect to PostgreSQL (Docker)
docker-compose exec postgres psql -U procode_user -d procode

# Connect to PostgreSQL (local)
psql -U procode_user -h localhost -p 5433 -d procode

# List databases
\l

# List tables
\dt

# Describe table
\d table_name

# Run SQL query
SELECT * FROM organizations;

# Exit
\q
```

### Migrations

```bash
# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

## Troubleshooting

### Connection Refused

**Problem**: `psql: error: connection to server at "localhost" (::1), port 5433 failed: Connection refused`

**Solutions**:
1. Check if PostgreSQL is running: `docker-compose ps postgres`
2. Start PostgreSQL: `docker-compose up -d postgres`
3. Check port mapping: `docker-compose port postgres 5432`

### Authentication Failed

**Problem**: `psql: error: FATAL: password authentication failed for user "procode_user"`

**Solutions**:
1. Check `.env` file has correct password
2. Verify `POSTGRES_PASSWORD` environment variable
3. Recreate container: `docker-compose down && docker-compose up -d postgres`

### Database Does Not Exist

**Problem**: `psql: error: FATAL: database "procode" does not exist`

**Solutions**:
1. Check `POSTGRES_DB` in docker-compose.yml
2. Recreate container: `docker-compose down -v && docker-compose up -d postgres`

### Port Already in Use

**Problem**: `Error starting userland proxy: listen tcp4 0.0.0.0:5433: bind: address already in use`

**Solutions**:
1. Change port in docker-compose.yml: `"5434:5432"`
2. Update DATABASE_URL: `postgresql://procode_user:changeme@localhost:5434/procode`
3. Or stop the conflicting service

### Migration Fails

**Problem**: `sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable)`

**Solutions**:
1. Ensure PostgreSQL is running
2. Check DATABASE_URL is correct
3. Run migrations: `alembic upgrade head`
4. Check migration files in `alembic/versions/`

## Performance Tuning

### Connection Pool Settings

```bash
# For development (low traffic)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# For production (high traffic)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### PostgreSQL Configuration

For production, consider tuning these PostgreSQL settings:

```sql
-- Increase shared buffers (25% of RAM)
shared_buffers = 2GB

-- Increase work memory
work_mem = 64MB

-- Increase maintenance work memory
maintenance_work_mem = 512MB

-- Increase effective cache size (50-75% of RAM)
effective_cache_size = 6GB

-- Enable query planning
random_page_cost = 1.1
```

## Monitoring

### Check Database Size

```sql
SELECT pg_size_pretty(pg_database_size('procode'));
```

### Check Table Sizes

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check Active Connections

```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'procode';
```

### Check Slow Queries

```sql
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Backup and Restore

### Automated Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U procode_user procode > $BACKUP_DIR/procode_$DATE.sql
echo "Backup created: $BACKUP_DIR/procode_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "procode_*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup.sh
```

### Manual Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U procode_user procode > backup.sql

# Restore
docker-compose exec -T postgres psql -U procode_user procode < backup.sql
```

## Migration from SQLite

If you have existing SQLite data:

### 1. Export SQLite Data

```bash
# Dump SQLite data
sqlite3 data/procode.db .dump > sqlite_dump.sql
```

### 2. Convert to PostgreSQL

```bash
# Install pgloader (macOS)
brew install pgloader

# Convert and load
pgloader sqlite://data/procode.db postgresql://procode_user:changeme@localhost:5433/procode
```

### 3. Verify Data

```bash
# Check row counts
psql -U procode_user -h localhost -p 5433 -d procode -c "
SELECT 'users' as table, COUNT(*) FROM users
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'messages', COUNT(*) FROM messages;
"
```

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Docker PostgreSQL Image](https://hub.docker.com/_/postgres)

---

**Need Help?** Check the troubleshooting section or open an issue on GitHub.
