# Docker Deployment Guide

Complete guide for deploying the Procode Agent Framework using Docker and Docker Compose.

## Quick Start

### 1. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required for LLM functionality
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here

# Database password
POSTGRES_PASSWORD=your-secure-password

# Optional: GitHub integration
GITHUB_TOKEN=your-token
GITHUB_REPO=owner/repo
USE_REAL_TOOLS=false
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Procode Agent API (port 9998)
- Next.js Frontend (port 3000)

### 3. Run Database Migrations

```bash
docker-compose exec agent alembic upgrade head
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:9998
- **Database**: localhost:5432

## Docker Commands

### Build and Start

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f agent
docker-compose logs -f postgres
```

### Stop and Clean

```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Database Operations

```bash
# Run migrations
docker-compose exec agent alembic upgrade head

# Create new migration
docker-compose exec agent alembic revision --autogenerate -m "Description"

# Rollback migration
docker-compose exec agent alembic downgrade -1

# Access PostgreSQL
docker-compose exec postgres psql -U procode_user -d procode
```

### Application Management

```bash
# Restart agent
docker-compose restart agent

# View agent logs
docker-compose logs -f agent

# Execute command in agent container
docker-compose exec agent python test_database.py

# Access agent shell
docker-compose exec agent /bin/sh
```

## Production Deployment

### Environment Variables

For production, set these in your `.env` file:

```bash
# Database
DATABASE_URL=postgresql://procode_user:STRONG_PASSWORD@postgres:5432/procode
USE_DATABASE=true
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# LLM Configuration
ANTHROPIC_API_KEY=your-production-key
USE_LLM_INTENT=true

# Security
POSTGRES_PASSWORD=STRONG_RANDOM_PASSWORD

# Optional: Monitoring
SQL_ECHO=false
```

### Docker Compose Production Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    restart: always
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data

  agent:
    restart: always
    environment:
      DATABASE_URL: postgresql://procode_user:${POSTGRES_PASSWORD}@postgres:5432/procode
      DB_POOL_SIZE: 20
      DB_MAX_OVERFLOW: 40
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  frontend:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

Run with:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Single Container Deployment

If you only need the agent (no frontend):

```bash
# Build image
docker build -t procode-agent .

# Run with SQLite (development)
docker run -d \
  --name procode-agent \
  -p 9998:9998 \
  -e ANTHROPIC_API_KEY=your-key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  procode-agent

# Run with external PostgreSQL
docker run -d \
  --name procode-agent \
  -p 9998:9998 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e USE_DATABASE=true \
  -e ANTHROPIC_API_KEY=your-key \
  procode-agent
```

## Health Checks

The agent container includes a health check:

```bash
# Check container health
docker ps

# View health check logs
docker inspect --format='{{json .State.Health}}' procode-agent | jq
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs agent

# Common issues:
# 1. Missing API keys - check .env file
# 2. Port already in use - change ports in docker-compose.yml
# 3. Database connection failed - ensure postgres is healthy
```

### Database Connection Issues

```bash
# Check postgres health
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U procode_user

# View postgres logs
docker-compose logs postgres
```

### Migration Errors

```bash
# Check current migration version
docker-compose exec agent alembic current

# View migration history
docker-compose exec agent alembic history

# Force migration (use with caution)
docker-compose exec agent alembic stamp head
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase resources in docker-compose.yml:
services:
  agent:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

## Backup and Restore

### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U procode_user procode > backup.sql

# Or with docker-compose
docker-compose exec -T postgres pg_dump -U procode_user procode > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U procode_user procode < backup.sql
```

### Backup Volumes

```bash
# Backup data directory
tar -czf data_backup.tar.gz data/

# Backup logs
tar -czf logs_backup.tar.gz logs/
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service with timestamps
docker-compose logs -f --timestamps agent

# Last 100 lines
docker-compose logs --tail=100 agent
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Container inspection
docker inspect procode-agent
```

## Scaling

### Horizontal Scaling

To run multiple agent instances:

```bash
# Scale agent service
docker-compose up -d --scale agent=3

# Add load balancer (nginx)
# See docs/KUBERNETES_DEPLOYMENT.md for production scaling
```

## Security Best Practices

1. **Use secrets management**:
   ```bash
   # Use Docker secrets instead of environment variables
   docker secret create anthropic_key ./anthropic_key.txt
   ```

2. **Run as non-root**: Already configured in Dockerfile

3. **Limit resources**: Set CPU and memory limits

4. **Network isolation**: Use custom networks

5. **Regular updates**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [master]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build image
        run: docker build -t procode-agent:latest .
      
      - name: Run tests
        run: docker run procode-agent:latest python -m pytest
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push procode-agent:latest
```

## Next Steps

- [Kubernetes Deployment](KUBERNETES_DEPLOYMENT.md) - For production scaling
- [Monitoring Setup](MONITORING.md) - Prometheus and Grafana
- [Production Roadmap](PRODUCTION_ROADMAP.md) - Full deployment guide (Step 24)

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify environment variables: `docker-compose config`
3. Test database connection: `docker-compose exec agent python test_database.py`
4. Review [troubleshooting section](#troubleshooting)
