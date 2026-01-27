.PHONY: help install dev start stop restart console demo test test-llm test-streaming test-a2a test-all test-auto test-watch test-coverage pre-commit-install pre-commit-run clean lint format check-env push frontend-install frontend-dev frontend-build frontend-start frontend-clean streamlit-app

# Default target
.DEFAULT_GOAL := help

# Export all environment variables to sub-processes
.EXPORT_ALL_VARIABLES:

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Procode Agent Framework - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies in virtual environment
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@if [ ! -d ".venv" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		python3 -m venv .venv; \
	fi
	@echo "$(GREEN)Activating virtual environment and installing packages...$(NC)"
	@. .venv/bin/activate && pip install --upgrade pip && pip install -e .
	@echo "$(GREEN)✓ Installation complete!$(NC)"

dev: install ## Setup development environment (install + check)
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@. .venv/bin/activate && pip install pytest pytest-asyncio
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Don't forget to set your environment variables:$(NC)"
	@echo "  - ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
	@echo "  - GITHUB_TOKEN and GITHUB_REPO (for real tools)"
	@echo ""

start: ## Start the agent server
	@echo "$(BLUE)Starting agent server on http://localhost:9998...$(NC)"
	@if lsof -ti:9998 > /dev/null 2>&1; then \
		echo "$(YELLOW)Warning: Port 9998 is already in use. Run 'make stop' first.$(NC)"; \
		exit 1; \
	fi
	@. .venv/bin/activate && python __main__.py

stop: ## Stop the agent server
	@echo "$(BLUE)Stopping agent server...$(NC)"
	@if lsof -ti:9998 > /dev/null 2>&1; then \
		lsof -ti:9998 | xargs kill -9 && \
		echo "$(GREEN)✓ Agent server stopped$(NC)"; \
	else \
		echo "$(YELLOW)No agent server running on port 9998$(NC)"; \
	fi

restart: stop ## Restart the agent server
	@sleep 1
	@$(MAKE) start

console: ## Run interactive console app
	@echo "$(BLUE)Starting interactive console...$(NC)"
	@. .venv/bin/activate && python console_app.py

demo: ## Run console demo (non-interactive)
	@echo "$(BLUE)Running console demo...$(NC)"
	@. .venv/bin/activate && python demo_console.py

test-quick: ## Quick test of agent functionality
	@echo "$(BLUE)Running quick test...$(NC)"
	@. .venv/bin/activate && python test_console.py

test: ## Run main test suite
	@echo "$(BLUE)Running main test suite...$(NC)"
	@. .venv/bin/activate && python tests/tests.py

test-llm: ## Run LLM integration tests (requires API key)
	@echo "$(BLUE)Running LLM tests...$(NC)"
	@. .venv/bin/activate && python tests/test_llm.py

test-streaming: ## Run streaming tests
	@echo "$(BLUE)Running streaming tests...$(NC)"
	@. .venv/bin/activate && python tests/test_streaming.py

test-a2a: ## Run agent-to-agent communication tests
	@echo "$(BLUE)Running A2A communication tests...$(NC)"
	@. .venv/bin/activate && python tests/test_agent_communication.py

test-all: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@. .venv/bin/activate && \
		python tests/tests.py && \
		python tests/test_streaming.py && \
		python tests/test_agent_communication.py
	@echo "$(GREEN)✓ All tests completed!$(NC)"

test-auto: ## Run automated test suite with reporting (hypervelocity mode)
	@echo "$(BLUE)Running automated test suite...$(NC)"
	@if [ ! -f scripts/run-tests.sh ]; then \
		echo "$(RED)Error: scripts/run-tests.sh not found$(NC)"; \
		exit 1; \
	fi
	@./scripts/run-tests.sh

test-watch: ## Watch for changes and auto-run tests (requires entr)
	@echo "$(BLUE)Watching for changes... (Ctrl+C to stop)$(NC)"
	@echo "$(YELLOW)Install entr if not available: brew install entr$(NC)"
	@find . -name "*.py" -not -path "./.venv/*" | entr -c make test-auto

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@. .venv/bin/activate && \
		pip install coverage pytest pytest-cov 2>/dev/null && \
		coverage run -m pytest tests/ && \
		coverage report -m && \
		coverage html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

test-integration: ## Run integration tests with real tools (requires GITHUB_TOKEN)
	@echo "$(BLUE)Running integration tests...$(NC)"
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "$(RED)Error: GITHUB_TOKEN not set$(NC)"; \
		exit 1; \
	fi
	@. .venv/bin/activate && \
		export RUN_INTEGRATION_TESTS=true && \
		export USE_REAL_TOOLS=true && \
		python tests/tests.py

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

clean-all: clean ## Clean everything including virtual environment
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	@rm -rf .venv
	@echo "$(GREEN)✓ Full cleanup complete!$(NC)"

lint: ## Run linting checks (requires pylint)
	@echo "$(BLUE)Running linting...$(NC)"
	@. .venv/bin/activate && \
		pip install pylint 2>/dev/null && \
		pylint core/ tasks/ a2a_comm/ security/ streaming/ || true

format: ## Format code with black (requires black)
	@echo "$(BLUE)Formatting code...$(NC)"
	@. .venv/bin/activate && \
		pip install black 2>/dev/null && \
		black . --exclude='.venv|__pycache__|.pytest_cache'
	@echo "$(GREEN)✓ Code formatted!$(NC)"

check-env: ## Check environment variables
	@echo "$(BLUE)Checking environment variables...$(NC)"
	@echo ""
	@echo "$(YELLOW)LLM Providers:$(NC)"
	@if [ -n "$$ANTHROPIC_API_KEY" ]; then echo "  $(GREEN)✓$(NC) ANTHROPIC_API_KEY is set"; else echo "  $(RED)✗$(NC) ANTHROPIC_API_KEY not set"; fi
	@if [ -n "$$OPENAI_API_KEY" ]; then echo "  $(GREEN)✓$(NC) OPENAI_API_KEY is set"; else echo "  $(RED)✗$(NC) OPENAI_API_KEY not set"; fi
	@if [ -n "$$GOOGLE_API_KEY" ]; then echo "  $(GREEN)✓$(NC) GOOGLE_API_KEY is set"; else echo "  $(RED)✗$(NC) GOOGLE_API_KEY not set"; fi
	@echo ""
	@echo "$(YELLOW)Tool Configuration:$(NC)"
	@if [ -n "$$GITHUB_TOKEN" ]; then echo "  $(GREEN)✓$(NC) GITHUB_TOKEN is set"; else echo "  $(RED)✗$(NC) GITHUB_TOKEN not set"; fi
	@if [ -n "$$GITHUB_REPO" ]; then echo "  $(GREEN)✓$(NC) GITHUB_REPO is set"; else echo "  $(RED)✗$(NC) GITHUB_REPO not set"; fi
	@echo ""
	@echo "$(YELLOW)Optional Settings:$(NC)"
	@echo "  USE_LLM_INTENT: $${USE_LLM_INTENT:-not set (defaults to true)}"
	@echo "  USE_REAL_TOOLS: $${USE_REAL_TOOLS:-not set (defaults to false)}"
	@echo "  AGENT_URL: $${AGENT_URL:-not set (defaults to http://localhost:9998)}"
	@echo ""

git-status: ## Show git status
	@git status

git-add: ## Add all changes to git
	@echo "$(BLUE)Adding all changes...$(NC)"
	@git add .
	@git status

git-commit: ## Commit changes (use: make git-commit MSG="your message")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please provide a commit message$(NC)"; \
		echo "Usage: make git-commit MSG=\"your commit message\""; \
		exit 1; \
	fi
	@echo "$(BLUE)Committing changes...$(NC)"
	@git commit -m "$(MSG)"
	@echo "$(GREEN)✓ Changes committed!$(NC)"

push: ## Push to GitHub
	@echo "$(BLUE)Pushing to GitHub...$(NC)"
	@git push origin master
	@echo "$(GREEN)✓ Pushed to GitHub!$(NC)"

git-sync: git-add ## Add, commit, and push (use: make git-sync MSG="your message")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please provide a commit message$(NC)"; \
		echo "Usage: make git-sync MSG=\"your commit message\""; \
		exit 1; \
	fi
	@echo "$(BLUE)Committing changes...$(NC)"
	@git commit -m "$(MSG)"
	@echo "$(BLUE)Pushing to GitHub...$(NC)"
	@git push origin master
	@echo "$(GREEN)✓ Synced with GitHub!$(NC)"

logs: ## Show recent agent logs
	@if [ -f "agent.log" ]; then \
		echo "$(BLUE)Recent agent logs:$(NC)"; \
		tail -n 50 agent.log; \
	else \
		echo "$(YELLOW)No agent.log file found$(NC)"; \
	fi

health: ## Check if agent is running
	@echo "$(BLUE)Checking agent health...$(NC)"
	@curl -s http://localhost:9998/ > /dev/null && \
		echo "$(GREEN)✓ Agent is running on http://localhost:9998$(NC)" || \
		echo "$(RED)✗ Agent is not running$(NC)"

docs: ## Show documentation files
	@echo "$(BLUE)Available documentation:$(NC)"
	@echo "  - $(GREEN)README.md$(NC) - Project overview"
	@echo "  - $(GREEN)QUICKSTART.md$(NC) - Quick start guide"
	@echo "  - $(GREEN)docs/STRUCTURE.md$(NC) - Project structure"
	@echo "  - $(GREEN)docs/CONSOLE_APP.md$(NC) - Console app usage"
	@echo "  - $(GREEN)docs/A2A_COMMUNICATION.md$(NC) - A2A features"
	@echo "  - $(GREEN)docs/DEVELOPMENT_HISTORY.md$(NC) - Development context"
	@echo "  - $(GREEN)docs/COST_OPTIMIZATION_SUMMARY.md$(NC) - Cost optimization guide"
	@echo "  - $(GREEN)docs/MULTI_LLM_STRATEGY.md$(NC) - Multi-LLM strategy details"
	@echo "  - $(GREEN)docs/IMPLEMENTATION_GUIDE.md$(NC) - Implementation guide"
	@echo "  - $(GREEN)docs/UX_ENHANCEMENT_PROPOSAL.md$(NC) - UX enhancement proposal"
	@echo ""

# ============================================================================
# Frontend Commands
# ============================================================================

frontend-install: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed!$(NC)"

frontend-dev: ## Start frontend development server
	@echo "$(BLUE)Starting frontend development server on http://localhost:3000...$(NC)"
	@if lsof -ti:3000 > /dev/null 2>&1; then \
		echo "$(YELLOW)Warning: Port 3000 is already in use. Run 'make frontend-stop' first.$(NC)"; \
		exit 1; \
	fi
	@cd frontend && npm run dev

frontend-build: ## Build frontend for production
	@echo "$(BLUE)Building frontend for production...$(NC)"
	@cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built successfully!$(NC)"

frontend-start: ## Start frontend production server
	@echo "$(BLUE)Starting frontend production server...$(NC)"
	@cd frontend && npm start

frontend-stop: ## Stop frontend server
	@echo "$(BLUE)Stopping frontend server...$(NC)"
	@if lsof -ti:3000 > /dev/null 2>&1; then \
		lsof -ti:3000 | xargs kill -9 && \
		echo "$(GREEN)✓ Frontend server stopped$(NC)"; \
	else \
		echo "$(YELLOW)No frontend server running on port 3000$(NC)"; \
	fi

frontend-clean: ## Clean frontend build artifacts
	@echo "$(BLUE)Cleaning frontend build artifacts...$(NC)"
	@cd frontend && rm -rf .next node_modules
	@echo "$(GREEN)✓ Frontend cleaned!$(NC)"

frontend-lint: ## Run frontend linting
	@echo "$(BLUE)Running frontend linting...$(NC)"
	@cd frontend && npm run lint

# ============================================================================
# Full Stack Commands
# ============================================================================

fullstack-install: install frontend-install ## Install both backend and frontend dependencies
	@echo "$(GREEN)✓ Full stack dependencies installed!$(NC)"

fullstack-dev: ## Start both backend and frontend in development mode
	@echo "$(BLUE)Starting full stack in development mode...$(NC)"
	@echo "$(YELLOW)Starting backend on port 9998...$(NC)"
	@. .venv/bin/activate && python __main__.py & \
	sleep 3 && \
	echo "$(YELLOW)Starting frontend on port 3000...$(NC)" && \
	cd frontend && npm run dev

fullstack-stop: stop frontend-stop ## Stop both backend and frontend
	@echo "$(GREEN)✓ Full stack stopped!$(NC)"

fullstack-clean: clean frontend-clean ## Clean both backend and frontend
	@echo "$(GREEN)✓ Full stack cleaned!$(NC)"

# ============================================================================
# Cost Optimization Commands
# ============================================================================

test-multi-llm: ## Test multi-LLM cost optimization
	@echo "$(BLUE)Testing multi-LLM classifier...$(NC)"
	@. .venv/bin/activate && python test_multi_llm.py

cost-metrics: ## Show cost optimization metrics
	@echo "$(BLUE)Cost Optimization Metrics:$(NC)"
	@echo ""
	@echo "$(YELLOW)Documentation:$(NC)"
	@echo "  - docs/COST_OPTIMIZATION_SUMMARY.md"
	@echo "  - docs/MULTI_LLM_STRATEGY.md"
	@echo "  - docs/IMPLEMENTATION_GUIDE.md"
	@echo ""
	@echo "$(YELLOW)Run tests to see savings:$(NC)"
	@echo "  make test-multi-llm"
	@echo ""

# ============================================================================
# Test Automation & Pre-commit Hooks (Hypervelocity)
# ============================================================================

pre-commit-install: ## Install pre-commit hooks for automated testing
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	@. .venv/bin/activate && pip install pre-commit 2>/dev/null
	@. .venv/bin/activate && pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed!$(NC)"
	@echo "$(YELLOW)Hooks will run automatically on git commit$(NC)"

pre-commit-run: ## Run pre-commit hooks manually on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	@. .venv/bin/activate && pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	@. .venv/bin/activate && pre-commit autoupdate

pre-commit-uninstall: ## Uninstall pre-commit hooks
	@echo "$(BLUE)Uninstalling pre-commit hooks...$(NC)"
	@. .venv/bin/activate && pre-commit uninstall
	@echo "$(GREEN)✓ Pre-commit hooks uninstalled$(NC)"

hypervelocity-setup: install pre-commit-install ## Complete hypervelocity development setup
	@echo "$(GREEN)✓ Hypervelocity development environment ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  make test-auto        - Run all tests with reporting"
	@echo "  make test-watch       - Auto-run tests on file changes"
	@echo "  make test-coverage    - Generate coverage report"
	@echo "  make pre-commit-run   - Run all pre-commit checks"
	@echo "  make logs-search      - Search structured logs"
	@echo "  make logs-tail        - Tail recent logs"
	@echo "  make logs-errors      - Show recent errors"
	@echo ""

# ============================================================================
# Centralized Logging Commands
# ============================================================================

logs-search: ## Search logs (use: make logs-search QUERY="your search")
	@echo "$(BLUE)Searching logs...$(NC)"
	@if [ -n "$(QUERY)" ]; then \
		python3 scripts/search-logs.py --query "$(QUERY)"; \
	else \
		python3 scripts/search-logs.py --help; \
	fi

logs-tail: ## Show last 50 log entries
	@echo "$(BLUE)Showing recent logs...$(NC)"
	@python3 scripts/search-logs.py --tail --limit 50 --format compact

logs-errors: ## Show recent errors
	@echo "$(BLUE)Showing recent errors...$(NC)"
	@python3 scripts/search-logs.py --level error --tail --limit 20

logs-agent: ## Show agent execution logs
	@echo "$(BLUE)Showing agent execution logs...$(NC)"
	@python3 scripts/search-logs.py --event-type agent_execution --tail --limit 30

logs-requests: ## Show HTTP request logs
	@echo "$(BLUE)Showing HTTP request logs...$(NC)"
	@python3 scripts/search-logs.py --event-type http_request --tail --limit 30

logs-since: ## Show logs since time (use: make logs-since TIME="1h")
	@if [ -z "$(TIME)" ]; then \
		echo "$(RED)Error: Please specify TIME (e.g., make logs-since TIME=\"1h\")$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Showing logs since $(TIME)...$(NC)"
	@python3 scripts/search-logs.py --since "$(TIME)" --format compact

logs-clean: ## Clean old log files (keeps last 7 days)
	@echo "$(BLUE)Cleaning old logs...$(NC)"
	@find logs/structured -name "*.jsonl*" -mtime +7 -delete 2>/dev/null || true
	@find logs/audit -name "*.jsonl" -mtime +7 -delete 2>/dev/null || true
	@find test-reports -name "*.txt" -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Old logs cleaned$(NC)"

logs-stats: ## Show log statistics
	@echo "$(BLUE)Log Statistics:$(NC)"
	@echo ""
	@echo "$(YELLOW)Structured Logs:$(NC)"
	@if [ -d "logs/structured" ]; then \
		find logs/structured -name "*.jsonl" -exec wc -l {} + | tail -1 | awk '{print "  Total entries: " $$1}'; \
		du -sh logs/structured | awk '{print "  Disk usage:    " $$1}'; \
	else \
		echo "  No structured logs found"; \
	fi
	@echo ""
	@echo "$(YELLOW)Test Reports:$(NC)"
	@if [ -d "test-reports" ]; then \
		ls -1 test-reports/*.txt 2>/dev/null | wc -l | awk '{print "  Total reports: " $$1}'; \
		du -sh test-reports 2>/dev/null | awk '{print "  Disk usage:    " $$1}'; \
	else \
		echo "  No test reports found"; \
	fi
	@echo ""

# ============================================================================
# Streamlit Web UI (Simple Alternative)
# ============================================================================

streamlit-app: ## Start Streamlit web UI (simple, working alternative to Next.js)
	@echo "$(BLUE)Starting Streamlit web UI...$(NC)"
	@echo "$(YELLOW)Make sure backend is running: make start$(NC)"
	@. .venv/bin/activate && pip install streamlit requests 2>/dev/null && streamlit run streamlit_app.py

# ============================================================================
# Docker Build & Push Commands
# ============================================================================

docker-build: ## Build Docker images (backend only)
	@echo "$(BLUE)Building backend Docker image...$(NC)"
	@docker-compose build agent
	@echo "$(GREEN)✓ Backend image built!$(NC)"

docker-build-frontend: ## Build frontend Docker image with production env vars
	@echo "$(BLUE)Building frontend Docker image with production env vars...$(NC)"
	@if [ -z "$$BACKEND_URL" ] || [ -z "$$API_KEY" ]; then \
		echo "$(YELLOW)Using default production credentials...$(NC)"; \
		BACKEND_URL=https://apiproagent.harjadi.com \
		API_KEY=Th3zcM61GGDHMqKuYgfgZVTJF \
		./build-frontend.sh; \
	else \
		./build-frontend.sh; \
	fi
	@echo "$(GREEN)✓ Frontend image built!$(NC)"

docker-build-all: docker-build docker-build-frontend ## Build all Docker images (backend + frontend)
	@echo "$(GREEN)✓ All Docker images built!$(NC)"

docker-push: ## Push Docker images to Docker Hub
	@echo "$(BLUE)Pushing Docker images to Docker Hub...$(NC)"
	@./push-to-dockerhub.sh
	@echo "$(GREEN)✓ Images pushed to Docker Hub!$(NC)"

docker-buildpush: docker-build-all docker-push ## Build all images and push to Docker Hub
	@echo "$(GREEN)✓ Build and push complete!$(NC)"

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Containers started!$(NC)"

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Containers stopped!$(NC)"

docker-logs: ## Show Docker container logs
	@echo "$(BLUE)Showing Docker logs...$(NC)"
	@docker-compose logs -f

docker-logs-agent: ## Show agent container logs
	@echo "$(BLUE)Showing agent logs...$(NC)"
	@docker-compose logs -f agent

docker-logs-frontend: ## Show frontend container logs
	@echo "$(BLUE)Showing frontend logs...$(NC)"
	@docker-compose logs -f frontend
