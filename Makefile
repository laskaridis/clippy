SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV_DIR := backend/.venv
PIP := $(VENV_DIR)/bin/pip

.PHONY: help init build test lint format typecheck run clean check

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Install local development dependencies and hooks
	@./scripts/setup-git-hooks.sh
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(PIP) install -r backend/requirements.txt
	@cd extension && pnpm install --frozen-lockfile

build: ## Build the extension artifacts
	@cd extension && pnpm run build

test: ## Run backend + extension test suites
	@./scripts/test_worktree.sh

lint: ## Run lint checks across backend and extension
	@./scripts/lint.sh

format: ## Format backend and extension source
	@./scripts/format.sh

typecheck: ## Run type checks across backend and extension
	@./scripts/typecheck.sh

run: ## Start local worktree stack (backend + extension build)
	@./scripts/run_worktree_stack.sh

clean: ## Remove local build and cache artifacts
	@rm -rf extension/chrome/dist
	@rm -rf extension/.local/worktrees
	@rm -rf backend/.mypy_cache backend/.pytest_cache
	@find backend extension -type d -name '__pycache__' -prune -exec rm -rf {} +

check: ## Run lint, typecheck, and test suites
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) test
