.PHONY: help install dev start console demo test test-llm test-streaming test-a2a test-all clean lint format check-env push

# Default target
.DEFAULT_GOAL := help

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
	@. .venv/bin/activate && python __main__.py

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
	@echo ""
