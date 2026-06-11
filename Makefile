# Radar Intelligence System - Development Makefile

.PHONY: install install-dev test lint update-deps clean help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.lock

install-dev: install  ## Install development dependencies
	pip install -r requirements.txt
	pip install pip-tools

test:  ## Run tests
	python -m pytest tests/ -v

test-watch:  ## Run tests in watch mode (requires pytest-xvfb)
	python -m pytest tests/ -v --maxfail=1 -x

lint:  ## Run basic linting (when available)
	@echo "Linting not configured yet - will add in CI setup"

update-deps:  ## Update dependency lockfile
	pip-compile --output-file requirements.lock requirements.txt

clean:  ## Clean up temporary files
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf radar-engine/__pycache__/
	rm -rf .pytest_cache/
	find . -name "*.pyc" -delete

# Development workflow
dev-setup: install-dev  ## Complete development setup
	@echo "Development environment ready!"
	@echo "Run 'make test' to verify everything works"

# Test autonomous system manually
test-fetch:  ## Test source fetching
	python -m radar-engine run

test-autonomous:  ## Test autonomous engine (when implemented)
	python -m radar-engine run