# Development Rules & Workflow

## HYPERVELOCITY PRINCIPLES

This project follows **hypervelocity development** principles - rapid, closed-loop development where all commands, tests, and logs are available on the CLI. The system continuously executes, measures, and corrects itself through automated feedback loops.

### Core Principles:
1. **Closed-Loop Development** - Automated testing provides immediate feedback
2. **Self-Directed Iteration** - Tests run automatically on every change
3. **Total Machine Observability** - All test results, logs, and metrics are visible
4. **Verification Defines Correctness** - Automated tests are the source of truth
5. **CLI-First Everything** - All operations available via command line
6. **Makefile-First** - Always use Makefile commands for consistency

## CRITICAL RULES - NEVER VIOLATE

### 0. Always Use Makefile Commands 🔴 CRITICAL
**NEVER run commands directly - ALWAYS use Makefile**

✅ **DO THIS**:
```bash
make test-auto          # Run tests
make start              # Start application
make docker-build       # Build Docker images
./push-to-dockerhub.sh  # Push to Docker Hub
make test-daemon        # Start continuous testing
```

❌ **NOT THIS**:
```bash
python test.py          # ❌ Use make test-auto
python __main__.py      # ❌ Use make start
docker build .          # ❌ Use make docker-build
docker push image       # ❌ Use ./push-to-dockerhub.sh
```

**Why Makefile-First?**
- ✅ Ensures consistent environment setup
- ✅ Handles dependencies automatically
- ✅ Uses correct parameters and flags
- ✅ Provides colored output and error handling
- ✅ Self-documenting (`make help`)
- ✅ Agent-friendly (predictable interface)

**Exception**: Only use direct commands when:
- Explicitly documented in guides
- Debugging specific issues
- Creating new Makefile targets

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
- [ ] Run `make test-auto` - verify all tests pass
- [ ] Check test status: `curl http://localhost:9999/test-status`
- [ ] Commit and push code
- [ ] Rebuild affected Docker images
- [ ] Push images to Docker Hub
- [ ] Pull images on production server
- [ ] Restart containers
- [ ] Verify in production
- [ ] Check production test status

### 7. Common Mistakes to Avoid
- ❌ Committing before testing
- ❌ Using direct commands instead of Makefile
- ❌ Using `docker push` instead of `./push-to-dockerhub.sh`
- ❌ Forgetting to rebuild images after code changes
- ❌ Building frontend with wrong API key
- ❌ Not verifying production deployment
- ❌ Not checking test status before deploying

### 8. Testing Checklist
Before committing ANY change:
- ❗ **NEW**: Test the enhanced rules system after implementation
- [ ] Code compiles/runs without errors
- [ ] Feature works as expected
- [ ] No regressions in existing features
- [ ] Logs show expected behavior
- [ ] Frontend and backend communicate correctly
- [ ] `make test-auto` passes
- [ ] Test status shows passing: `curl http://localhost:9999/test-status`

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

**Option 1: Continuous Testing (Recommended for Hypervelocity)** 🚀
```bash
# Start test daemon - runs tests every 30 seconds
make test-daemon

# Check daemon status
make test-daemon-status

# View live logs
make test-daemon-logs

# Stop daemon
make test-daemon-stop

# Query test status via API
curl http://localhost:9999/test-status
```

**Option 2: Auto-run on file changes**
```bash
# Watch mode - tests run automatically when you save files
make test-watch

# Keep this running in a terminal while you code
# Provides immediate feedback on every change
```

**Option 3: Manual test runs**
```bash
# Run all tests with detailed reporting
make test-auto

# Run tests with coverage analysis
make test-coverage

# Run specific test file
python3 test_greetings.py
```

**Option 4: Pre-commit hooks (Automatic)**
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
- Accessible via `/test-status` endpoint

### Test Status Monitoring (Phase 1) 🆕
```bash
# Check test status via HTTP
curl http://localhost:9999/test-status

# Get detailed test results
curl http://localhost:9999/test-status?detailed=true

# View test metrics in Prometheus
curl http://localhost:9999/metrics | grep test_

# Check if tests are healthy
curl http://localhost:9999/test-status | jq '.healthy'
```

**Available Test Metrics**:
- `test_pass_rate` - Pass rate percentage (0-100)
- `test_total_count` - Total number of tests
- `test_passed_count` - Number of tests passed
- `test_failed_count` - Number of tests failed
- `test_duration_seconds` - Total test execution time
- `test_last_run_timestamp` - Last test run timestamp
- `test_status` - Status code (1=passing, 0=failing, -1=no_tests, -2=error)

### Closed-Loop Development Cycle
1. **Write code** → Save file
2. **Tests auto-run** → Immediate feedback (test-daemon or test-watch)
3. **Check status** → `curl http://localhost:9999/test-status`
4. **Fix issues** → Tests re-run automatically
5. **Commit** → Pre-commit hooks verify everything passes
6. **Push** → CI/CD runs full test suite (future)
7. **Deploy** → Production test status monitored

## Database (PostgreSQL)

### Local Development Setup
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Seed default data
python scripts/seed_api_keys.py

# Connect to database
docker-compose exec postgres psql -U procode_user -d procode
```

### Database Commands
```bash
# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

### Why PostgreSQL Everywhere?
- ✅ **Production Parity**: Same database in dev and prod
- ✅ **No Surprises**: What works locally works in production
- ✅ **Full Features**: Use PostgreSQL-specific features (JSONB, UUID, arrays)
- ✅ **Simpler Code**: No conditional logic for different databases
- ✅ **Better Testing**: Catch PostgreSQL-specific issues early

See [`docs/database/POSTGRESQL_SETUP.md`](docs/database/POSTGRESQL_SETUP.md) for detailed documentation.

## Quick Reference

### Test Locally
```bash
# Start all services (PostgreSQL + Agent + Frontend)
docker-compose up -d

# Or start individually
docker-compose up -d postgres  # Database only
docker-compose up -d agent     # Backend only
docker-compose up -d frontend  # Frontend only

# Check logs
docker-compose logs -f agent
docker-compose logs -f frontend
docker-compose logs -f postgres

# Test in browser
open http://localhost:3000
```

### Build & Deploy
```bash
# 1. Test first!
make test-auto
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

### 1. Always Use Makefile Commands
```bash
# ✅ GOOD - Consistent, documented, reliable
make test-auto
make start
make docker-build
make test-daemon

# ❌ BAD - Inconsistent, error-prone
python test.py
python __main__.py
docker build -t image .
```

### 2. Always Use Structured Logging
```python
# ✅ GOOD - Structured, searchable
from observability.centralized_logger import get_logger
logger = get_logger(__name__)
logger.info("User action", action="login", user_id="123", success=True)

# ❌ BAD - Unstructured string
print(f"User 123 logged in successfully")
```

### 3. Log Performance Metrics
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

### 4. Use Event Types for Filtering
```python
# Makes logs easily searchable by event type
logger.log_request(method="POST", path="/api", status_code=200, duration_ms=45)
logger.log_agent_execution(agent_name="tickets", intent="create", success=True, duration_ms=123)
logger.log_test_result(test_name="test_greetings", passed=True, duration_ms=56)
```

### 5. Search Logs Before Debugging
```bash
# Before diving into code, search logs first
make logs-errors              # What errors occurred?
make logs-agent               # How are agents performing?
make logs-since TIME="1h"     # What happened recently?
make logs-search QUERY="text" # Find specific events
```

### 6. Run Tests Continuously
```bash
# Start test daemon for continuous testing (Hypervelocity Phase 1)
make test-daemon

# Or use watch mode for file-change based testing
make test-watch

# Provides immediate feedback on every save
# Catches issues before commit
```

### 7. Let Pre-commit Hooks Work
```bash
# Install once, forget about it
make hypervelocity-setup

# Hooks automatically:
# - Format code (black, isort)
# - Run linters (flake8, bandit)
# - Run tests
# - Prevent bad commits
```

### 8. Monitor System Health
```bash
# Regular health checks
make logs-stats          # Log volume and disk usage
make logs-errors         # Recent error patterns
make test-auto           # Test suite status
make test-daemon-status  # Continuous testing status

# Check test status via API
curl http://localhost:9999/test-status
curl http://localhost:9999/health
curl http://localhost:9999/metrics | grep test_
```

### 9. Clean Up Regularly
```bash
# Prevent log bloat
make logs-clean    # Removes logs >7 days old
```

## Closed-Loop Development Workflow

### The Ideal Flow (Hypervelocity)
1. **Write Code** → Save file
2. **Tests Auto-Run** → Immediate pass/fail (test-daemon or test-watch)
3. **Check Status** → `curl http://localhost:9999/test-status`
4. **Logs Generated** → Structured, searchable
5. **Search Logs** → Understand behavior instantly
6. **Fix Issues** → Tests re-run automatically
7. **Commit** → Pre-commit hooks verify quality
8. **Push** → CI/CD runs full suite (future)
9. **Deploy** → Full observability in production

### Key Metrics to Track
- **Test Pass Rate**: Should be >95% (monitored via `/test-status`)
- **Test Duration**: Track and optimize slow tests
- **Agent Performance**: Monitor duration_ms for all agents
- **Error Rate**: Track errors per hour/day
- **Log Volume**: Monitor disk usage

### When Things Go Wrong
1. **Check test status**: `curl http://localhost:9999/test-status`
2. **Check logs**: `make logs-errors`
3. **Search for patterns**: `make logs-search QUERY="error_keyword"`
4. **Check recent activity**: `make logs-since TIME="1h"`
5. **Review test results**: Check `test-reports/` directory or `/test-status?detailed=true`
6. **Run tests**: `make test-auto` to verify fixes

## Makefile Command Reference

### Essential Commands
```bash
make help                # Show all available commands
make install             # Install dependencies
make start               # Start the agent server
make stop                # Stop the agent server
make test-auto           # Run automated test suite
make test-daemon         # Start continuous testing (Phase 1)
make test-daemon-stop    # Stop continuous testing
make test-daemon-status  # Check daemon status
make docker-build        # Build Docker images
make docker-push         # Push to Docker Hub
```

### Testing Commands
```bash
make test-auto           # Run all tests with reporting
make test-watch          # Auto-run tests on file changes
make test-coverage       # Run tests with coverage
make test-daemon         # Continuous testing (every 30s)
make test-daemon-logs    # View daemon logs
make pre-commit-run      # Run pre-commit hooks manually
```

### Monitoring Commands
```bash
make logs-errors         # Show recent errors
make logs-agent          # Show agent execution logs
make logs-search         # Search logs
make logs-stats          # Log statistics
make test-daemon-status  # Test daemon status
```

### Docker Commands
```bash
make docker-build        # Build backend image
make docker-build-frontend  # Build frontend with prod env
make docker-build-all    # Build all images
make docker-push         # Push to Docker Hub
make docker-up           # Start containers
make docker-down         # Stop containers
```

## Notes

- This project uses Docker for deployment
- Frontend uses Next.js (build-time env vars)
- Backend uses Python/Starlette (runtime env vars)
- LLM intent classification uses Anthropic Claude 3 Haiku
- Production: https://proagent.harjadi.com (frontend), https://apiproagent.harjadi.com (backend)
- **Hypervelocity Mode**: Test automation + centralized logging + continuous testing enabled
- **Log Retention**: 7 days (configurable)
- **Test Reports**: Timestamped in `test-reports/` directory
- **Test Status API**: Available at `/test-status` endpoint
- **Test Metrics**: Exported to Prometheus at `/metrics`

## Phase 1 Implementation (Continuous Testing) 🆕

Phase 1 of the Hypervelocity implementation adds continuous testing capabilities:

- ✅ **Test Status Tracker**: Reads and parses test reports
- ✅ **Test Metrics**: 7 new Prometheus metrics for test monitoring
- ✅ **Background Test Runner**: Runs tests every 30 seconds
- ✅ **Test Status Endpoint**: `/test-status` API for querying test results
- ✅ **Observable Results**: Tests results visible to agents and developers

**See**: [`docs/development/PHASE1_COMPLETE.md`](docs/development/PHASE1_COMPLETE.md) for details

**Next**: Phase 2 will add log query API and SQLite indexing for fast log searches

---

## Enhanced Rules System (Phase 1) 🆕

Phase 1 of the Claude Code Creator tips implementation adds a dynamic learning system to capture and apply development insights.

### Capturing Learnings

After every mistake, discovery, or insight:
```bash
make update-rules MSG="Your learning here"
```

This will:
- ✅ Append the learning to DEVELOPMENT_RULES.md
- ✅ Create an entry in `docs/lessons-learned/`
- ✅ Update `.roo/rules-code/rules.md`
- ✅ Commit changes automatically

**Example:**
```bash
make update-rules MSG="Always run tests before committing"
make update-rules MSG="Use Makefile commands instead of direct docker" --category best_practices
```

### Project Notes

Task-specific notes are stored in `docs/project-notes/`:
- 📝 Created for major features or significant work
- 📋 Updated after every PR
- 🔗 Linked from relevant documentation
- 📊 Indexed automatically

**Create a project note:**
1. Copy template from `docs/project-notes/README.md`
2. Name it: `YYYY-MM-DD-short-description.md`
3. Document context, decisions, and learnings
4. Update after each milestone

**Update the index:**
```bash
make update-notes-index
```

### Rules Validation

Before major changes or deployments:
```bash
make validate-rules          # Quick validation
make validate-rules-verbose  # Detailed output
```

**What it checks:**
- ✅ Tests run before commits
- ✅ Makefile commands used (not direct commands)
- ✅ Logs are structured JSON
- ✅ Documentation updated recently
- ✅ Required directories exist
- ✅ DEVELOPMENT_RULES.md is complete

### Viewing Learnings

**Show recent lessons:**
```bash
make show-lessons
```

**Show recent project notes:**
```bash
make show-notes
```

### Best Practices

**Do:**
- ✅ Capture learnings immediately after discovering them
- ✅ Update project notes as you work, not after
- ✅ Run `make validate-rules` before major changes
- ✅ Review lessons learned weekly
- ✅ Keep notes concise but complete

**Don't:**
- ❌ Wait until end of project to document
- ❌ Skip capturing "obvious" learnings
- ❌ Let notes get stale
- ❌ Duplicate information across files

### Integration with Workflow

**Daily:**
- Capture learnings as they happen
- Update active project notes

**Weekly:**
- Review lessons learned
- Run `make validate-rules`
- Update project notes index

**Before Deployment:**
- Run `make validate-rules`
- Review recent lessons
- Update relevant documentation

### Available Commands

```bash
# Learning System
make update-rules MSG="learning"     # Capture a learning
make validate-rules                  # Check compliance
make validate-rules-verbose          # Detailed validation
make show-lessons                    # Show recent lessons

# Project Notes
make update-notes-index              # Regenerate index
make show-notes                      # Show recent notes
```

**See:**
- [`docs/lessons-learned/README.md`](docs/lessons-learned/README.md) - Lessons learned guide
- [`docs/project-notes/README.md`](docs/project-notes/README.md) - Project notes guide
- [`plans/CLAUDE_CODE_TIPS_IMPLEMENTATION.md`](plans/CLAUDE_CODE_TIPS_IMPLEMENTATION.md) - Full implementation plan

---
