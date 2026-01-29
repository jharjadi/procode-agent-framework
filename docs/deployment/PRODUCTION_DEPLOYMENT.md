# Production Deployment Guide

## 🚀 Step-by-Step Production Deployment

### Prerequisites ✅
- [x] Code committed to git (commit a0318a2)
- [x] All tests passing (6/6)
- [x] Monitoring system implemented
- [ ] Docker Desktop running
- [ ] Docker Hub account (username: tempolong)

---

## Step 1: Start Docker Desktop

**macOS:**
```bash
# Open Docker Desktop
open -a Docker

# Wait for Docker to start (30-60 seconds)
# Check if Docker is running:
docker ps
```

**Alternative:**
- Open Docker Desktop from Applications folder
- Wait for the whale icon in menu bar to show "Docker Desktop is running"

---

## Step 2: Build and Push to Docker Hub (One Command!)

Once Docker is running, use this single command:

```bash
make docker-buildpush
```

This will:
1. ✅ Build backend Docker image
2. ✅ Build frontend Docker image  
3. ✅ Tag images for Docker Hub
4. ✅ Push to tempolong/procode-agent:latest
5. ✅ Push to tempolong/procode-frontend:latest

**Expected output:**
```
🔨 Building backend Docker image...
✓ Backend image built!

🔨 Building frontend Docker image...
✓ Frontend image built!

📦 Tagging and pushing agent image...
✅ Agent image pushed: tempolong/procode-agent:latest

📦 Tagging and pushing frontend image...
✅ Frontend image pushed: tempolong/procode-frontend:latest

🎉 All images pushed successfully!
```

---

## Step 3: Update Production Server

### Option A: Using Docker Compose (Recommended)

**On your production server:**

1. **Create docker-compose.production.yml:**
```yaml
version: '3.8'

services:
  agent:
    image: tempolong/procode-agent:latest
    ports:
      - "9998:9998"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENABLE_SENTRY=true
      - SENTRY_DSN=${SENTRY_DSN}
      - ENABLE_METRICS=true
      - ENABLE_HEALTH_CHECKS=true
      - SENTRY_ENVIRONMENT=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:9998/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: tempolong/procode-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_BACKEND_URL=https://apiproagent.harjadi.com
      - NEXT_PUBLIC_API_KEY=${API_KEY}
    restart: unless-stopped
    depends_on:
      - agent

  # Optional: Monitoring stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    restart: unless-stopped
```

2. **Pull and start:**
```bash
# Pull latest images
docker-compose -f docker-compose.production.yml pull

# Start services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f agent
```

### Option B: Using Docker Run

```bash
# Pull latest image
docker pull tempolong/procode-agent:latest

# Stop old container
docker stop procode-agent || true
docker rm procode-agent || true

# Run new container
docker run -d \
  --name procode-agent \
  --restart unless-stopped \
  -p 9998:9998 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ENABLE_SENTRY=true \
  -e SENTRY_DSN=$SENTRY_DSN \
  -e ENABLE_METRICS=true \
  -e SENTRY_ENVIRONMENT=production \
  tempolong/procode-agent:latest
```

---

## Step 4: Verify Deployment

### Health Checks

```bash
# Check health endpoint
curl https://apiproagent.harjadi.com/health

# Check readiness
curl https://apiproagent.harjadi.com/ready

# Check metrics
curl https://apiproagent.harjadi.com/metrics
```

### Expected responses:

**Health:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T...",
  "version": "0.1.0",
  "uptime_seconds": 120,
  "checks": {
    "database": {"status": "healthy"},
    "llm_provider": {"status": "healthy"},
    "memory": {"status": "healthy"}
  }
}
```

**Metrics:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health",status="200"} 5.0
```

---

## Step 5: Monitor Production

### Sentry Dashboard
https://sentry.io/organizations/o4510789455249408/

**What to monitor:**
- Error rates
- Response times
- User sessions
- Performance metrics

### Prometheus + Grafana (Optional)

If you deployed the monitoring stack:

```bash
# Access Grafana
open http://your-server:3001

# Default credentials:
# Username: admin
# Password: (set in GRAFANA_PASSWORD env var)
```

**Import dashboard:**
- Use the dashboard configuration from `docs/STEP12_MONITORING_DESIGN.md`

---

## Step 6: Setup Continuous Deployment (Optional)

### Create GitHub Actions Workflow

**`.github/workflows/deploy.yml`:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [master]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push
        run: |
          docker-compose build agent frontend
          docker tag procode-agent-framework-agent:latest tempolong/procode-agent:latest
          docker tag procode-agent-framework-frontend:latest tempolong/procode-frontend:latest
          docker push tempolong/procode-agent:latest
          docker push tempolong/procode-frontend:latest
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /path/to/app
            docker-compose pull
            docker-compose up -d
```

---

## Quick Reference Commands

### Local Development
```bash
make start              # Start local server
make restart            # Restart local server
make stop               # Stop local server
make test-monitoring    # Test monitoring
```

### Docker Build & Push
```bash
make docker-build-all   # Build all images
make docker-push        # Push to Docker Hub
make docker-buildpush   # Build + Push (one command)
```

### Git Operations
```bash
make git-status         # Check git status
make git-add            # Add all changes
make push               # Push to GitHub
```

### Production Deployment
```bash
# On your local machine:
make docker-buildpush

# On production server:
docker-compose pull
docker-compose up -d
docker-compose logs -f agent
```

---

## Troubleshooting

### Docker not running
```bash
# Start Docker Desktop
open -a Docker

# Or check status
docker ps
```

### Docker Hub login required
```bash
docker login
# Username: tempolong
# Password: (your Docker Hub password)
```

### Image build fails
```bash
# Clean and rebuild
docker system prune -a
make docker-build-all
```

### Health check fails
```bash
# Check logs
docker logs procode-agent

# Check health manually
docker exec procode-agent curl http://localhost:9998/health
```

### Port already in use
```bash
# Find and kill process
lsof -ti:9998 | xargs kill -9
```

---

## Environment Variables for Production

Create a `.env` file on your production server:

```bash
# LLM Providers
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Monitoring
ENABLE_SENTRY=true
SENTRY_DSN=https://f184e400fb0f19ea28bafde3c40314d2@o4510789455249408.ingest.de.sentry.io/4510789464883280
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

ENABLE_METRICS=true
ENABLE_HEALTH_CHECKS=true

# API Security (optional)
ENABLE_API_KEY_AUTH=true
DEMO_API_KEY=your_production_key

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

## Post-Deployment Checklist

- [ ] Docker images built and pushed
- [ ] Production server updated
- [ ] Health check passing (200 OK)
- [ ] Metrics endpoint accessible
- [ ] Sentry receiving events
- [ ] Frontend accessible
- [ ] API endpoints working
- [ ] Monitor for 24 hours
- [ ] Check Sentry dashboard daily
- [ ] Review metrics in Prometheus/Grafana

---

## Support & Monitoring

### Health Check URLs
- Production: https://apiproagent.harjadi.com/health
- Metrics: https://apiproagent.harjadi.com/metrics

### Dashboards
- Sentry: https://sentry.io/organizations/o4510789455249408/
- Grafana: http://your-server:3001 (if deployed)

### Logs
```bash
# View real-time logs
docker logs -f procode-agent

# Last 100 lines
docker logs --tail 100 procode-agent

# Search logs
docker logs procode-agent 2>&1 | grep ERROR
```

---

## Next Steps After Deployment

1. **Monitor for 24 hours** - Check Sentry dashboard
2. **Test all endpoints** - Verify functionality
3. **Check metrics** - Review Prometheus metrics
4. **Setup alerts** - Configure alerting rules
5. **Scale if needed** - Add more containers
6. **Backup strategy** - Setup automated backups
7. **SSL certificates** - Ensure HTTPS is configured
8. **Rate limiting** - Configure if needed

---

## Success Criteria

✅ Docker images built and pushed to Docker Hub  
✅ Production server running latest version  
✅ Health check endpoint returning 200 OK  
✅ Metrics being collected  
✅ Sentry receiving error reports  
✅ No critical errors in logs  
✅ Response time < 500ms  
✅ Uptime > 99.9%  

**You're production ready! 🚀**
