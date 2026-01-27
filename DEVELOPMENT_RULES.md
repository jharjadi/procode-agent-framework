# Development Rules & Workflow

## HYPERVELOCITY PRINCIPLES

This project follows **hypervelocity development** principles - rapid, closed-loop development where all commands, tests, and logs are available on the CLI. The system continuously executes, measures, and corrects itself through automated feedback loops.

### Core Principles:
1. **Closed-Loop Development** - Automated testing provides immediate feedback
2. **Self-Directed Iteration** - Tests run automatically on every change
3. **Total Machine Observability** - All test results, logs, and metrics are visible
4. **Verification Defines Correctness** - Automated tests are the source of truth
5. **CLI-First Everything** - All operations available via command line

## CRITICAL RULES - NEVER VIOLATE

### 1. Testing Before Committing
**ALWAYS test changes before committing to git**
- Run the application locally or in Docker
- Verify the fix actually works
- Test edge cases
- Only commit after confirming everything works

### 2. Docker Image Pushing
**ALWAYS use the provided scripts**
- Use `./push-to-dockerhub.sh` - NEVER use `docker push` directly
- Use `./build-frontend.sh` for frontend builds with proper env vars
- Scripts ensure consistency and proper configuration

### 3. Build Order & Dependencies
**Frontend builds require correct environment variables**
- Frontend: `BACKEND_URL` and `API_KEY` are baked into build at BUILD TIME
- Backend: Environment variables are read at RUNTIME
- Always match production credentials when building for production

### 4. Git Workflow
**Standard workflow**
1. Make changes
2. **TEST THOROUGHLY** (local or Docker)
3. Verify fix works
4. Commit with descriptive message
5. Push to master
6. Rebuild Docker images if needed
7. Push images to Docker Hub
8. Deploy to production

### 5. Environment Variables
**Critical environment variables**
- `ANTHROPIC_API_KEY` - For LLM intent classification
- `USE_LLM_INTENT=true` - Enable LLM classification
- `ALLOWED_ORIGINS` - CORS allowed origins (production domain)
- `DEMO_API_KEY` - API key for authentication
- `ENABLE_API_SECURITY=true` - Enable security middleware
- `NEXT_PUBLIC_BACKEND_URL` - Frontend backend URL (BUILD TIME)
- `NEXT_PUBLIC_API_KEY` - Frontend API key (BUILD TIME)

### 6. Production Deployment Checklist
- [ ] Test changes locally
- [ ] Commit and push code
- [ ] Rebuild affected Docker images
- [ ] Push images to Docker Hub
- [ ] Pull images on production server
- [ ] Restart containers
- [ ] Verify in production

### 7. Common Mistakes to Avoid
- ❌ Committing before testing
- ❌ Using `docker push` instead of `./push-to-dockerhub.sh`
- ❌ Forgetting to rebuild images after code changes
- ❌ Building frontend with wrong API key
- ❌ Not verifying production deployment

### 8. Testing Checklist
Before committing ANY change:
- [ ] Code compiles/runs without errors
- [ ] Feature works as expected
- [ ] No regressions in existing features
- [ ] Logs show expected behavior
- [ ] Frontend and backend communicate correctly

## Hypervelocity Test Automation

### Setup (One-time)
```bash
# Install hypervelocity development environment
make hypervelocity-setup

# This installs:
# - Pre-commit hooks (auto-run tests before commit)
# - Test automation tools
# - Code formatters and linters
```

### Automated Testing Workflow

**Option 1: Auto-run on file changes (Recommended)**
```bash
# Watch mode - tests run automatically when you save files
make test-watch

# Keep this running in a terminal while you code
# Provides immediate feedback on every change
```

**Option 2: Manual test runs**
```bash
# Run all tests with detailed reporting
make test-auto

# Run tests with coverage analysis
make test-coverage

# Run specific test file
python3 test_greetings.py
```

**Option 3: Pre-commit hooks (Automatic)**
```bash
# Hooks run automatically on git commit
git commit -m "your message"

# Or run manually without committing
make pre-commit-run
```

### Test Reports
- Reports saved to `test-reports/` directory
- Each run creates timestamped report
- Shows pass/fail status for each test
- Includes error details for failed tests

### Closed-Loop Development Cycle
1. **Write code** → Save file
2. **Tests auto-run** → Immediate feedback (if using test-watch)
3. **Fix issues** → Tests re-run automatically
4. **Commit** → Pre-commit hooks verify everything passes
5. **Push** → CI/CD runs full test suite (future)

## Quick Reference

### Test Locally
```bash
# Start Docker containers
docker-compose up -d

# Check logs
docker-compose logs -f agent
docker-compose logs -f frontend

# Test in browser
open http://localhost:3000
```

### Build & Deploy
```bash
# 1. Test first!
docker-compose up -d
# Verify it works...

# 2. Commit
git add .
git commit -m "descriptive message"
git push origin master

# 3. Rebuild images (if code changed)
docker-compose build

# 4. Push to Docker Hub
./push-to-dockerhub.sh

# 5. Deploy to production
# On production server:
docker-compose pull
docker-compose up -d
```

### Complete Rebuild & Push Workflow
**IMPORTANT: When rebuilding for production deployment**

The frontend MUST be rebuilt with production environment variables BEFORE pushing to Docker Hub:

```bash
# Step 1: Rebuild backend (if backend code changed)
docker-compose build agent

# Step 2: Rebuild frontend with production env vars (CRITICAL!)
BACKEND_URL=https://apiproagent.harjadi.com \
API_KEY=Th3zcM61GGDHMqKuYgfgZVTJF \
./build-frontend.sh

# Step 3: Push both images to Docker Hub
./push-to-dockerhub.sh

# Step 4: Deploy on production server
# SSH to production server, then:
docker-compose pull
docker-compose up -d
```

**Why this order matters:**
- `docker-compose build` rebuilds backend but uses cached frontend layers
- Frontend needs production credentials baked in at BUILD TIME
- `./build-frontend.sh` rebuilds frontend with correct env vars
- `./push-to-dockerhub.sh` pushes both images to Docker Hub
- Production server pulls the correctly configured images

### Build Frontend for Production
```bash
# Use correct production credentials
BACKEND_URL=https://apiproagent.harjadi.com \
API_KEY=Th3zcM61GGDHMqKuYgfgZVTJF \
./build-frontend.sh
```

## Context Retention Strategy

This file serves as a persistent reference for development rules. When starting a new session or task:

1. Read this file first
2. Follow the rules strictly
3. Update this file if new patterns emerge
4. Reference this file before committing, building, or deploying

## Hypervelocity Best Practices

### 1. Always Use Structured Logging
```python
# ✅ GOOD - Structured, searchable
from observability.centralized_logger import get_logger
logger = get_logger(__name__)
logger.info("User action", action="login", user_id="123", success=True)

# ❌ BAD - Unstructured string
print(f"User 123 logged in successfully")
```

### 2. Log Performance Metrics
```python
# Always track duration for performance analysis
start_time = time.time()
result = await agent.invoke(context)
duration_ms = (time.time() - start_time) * 1000

logger.log_agent_execution(
    agent_name="tickets",
    intent="create_ticket",
    success=True,
    duration_ms=duration_ms  # Critical for optimization!
)
```

### 3. Use Event Types for Filtering
```python
# Makes logs easily searchable by event type
logger.log_request(method="POST", path="/api", status_code=200, duration_ms=45)
logger.log_agent_execution(agent_name="tickets", intent="create", success=True, duration_ms=123)
logger.log_test_result(test_name="test_greetings", passed=True, duration_ms=56)
```

### 4. Search Logs Before Debugging
```bash
# Before diving into code, search logs first
make logs-errors              # What errors occurred?
make logs-agent               # How are agents performing?
make logs-since TIME="1h"     # What happened recently?
make logs-search QUERY="text" # Find specific events
```

### 5. Run Tests Continuously
```bash
# Keep test-watch running while coding
make test-watch

# Provides immediate feedback on every save
# Catches issues before commit
```

### 6. Let Pre-commit Hooks Work
```bash
# Install once, forget about it
make hypervelocity-setup

# Hooks automatically:
# - Format code (black, isort)
# - Run linters (flake8, bandit)
# - Run tests
# - Prevent bad commits
```

### 7. Monitor System Health
```bash
# Regular health checks
make logs-stats    # Log volume and disk usage
make logs-errors   # Recent error patterns
make test-auto     # Test suite status
```

### 8. Clean Up Regularly
```bash
# Prevent log bloat
make logs-clean    # Removes logs >7 days old
```

## Closed-Loop Development Workflow

### The Ideal Flow
1. **Write Code** → Save file
2. **Tests Auto-Run** → Immediate pass/fail (test-watch)
3. **Logs Generated** → Structured, searchable
4. **Search Logs** → Understand behavior instantly
5. **Fix Issues** → Tests re-run automatically
6. **Commit** → Pre-commit hooks verify quality
7. **Push** → CI/CD runs full suite (future)
8. **Deploy** → Full observability in production

### Key Metrics to Track
- **Test Pass Rate**: Should be >95%
- **Test Duration**: Track and optimize slow tests
- **Agent Performance**: Monitor duration_ms for all agents
- **Error Rate**: Track errors per hour/day
- **Log Volume**: Monitor disk usage

### When Things Go Wrong
1. **Check logs first**: `make logs-errors`
2. **Search for patterns**: `make logs-search QUERY="error_keyword"`
3. **Check recent activity**: `make logs-since TIME="1h"`
4. **Review test results**: Check `test-reports/` directory
5. **Run tests**: `make test-auto` to verify fixes

## Notes

- This project uses Docker for deployment
- Frontend uses Next.js (build-time env vars)
- Backend uses Python/Starlette (runtime env vars)
- LLM intent classification uses Anthropic Claude 3 Haiku
- Production: https://proagent.harjadi.com (frontend), https://apiproagent.harjadi.com (backend)
- **Hypervelocity Mode**: Test automation + centralized logging enabled
- **Log Retention**: 7 days (configurable)
- **Test Reports**: Timestamped in `test-reports/` directory
