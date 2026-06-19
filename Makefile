# Radar Intelligence System

.PHONY: install install-dev test lint update-deps clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.lock

install-dev: install ## Install development dependencies
	pip install -r requirements.txt
	pip install pip-tools

test: ## Run tests
	python -m pytest tests/ -v

lint: ## Run basic linting
	@echo "Linting not configured yet"

update-deps: ## Update dependency lockfile
	pip-compile --output-file requirements.lock requirements.txt

clean: ## Clean up temporary files
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf radar-engine/__pycache__/
	rm -rf radar-engine/**/__pycache__/
	rm -rf .pytest_cache/
	find . -name "*.pyc" -delete

dev-setup: install-dev ## Complete development setup
	@echo "Development environment ready!"

fetch: ## Fetch from all sources
	python -m radar-engine run
