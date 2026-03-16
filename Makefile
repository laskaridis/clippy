SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV_DIR := backend/.venv
PIP := $(VENV_DIR)/bin/pip

.PHONY: help all-init all-build all-test all-lint all-format all-typecheck all-run all-clean \
	init build test lint format typecheck run clean verify \
	worktree-start \
	backend-init backend-test backend-lint backend-format backend-format-check backend-typecheck backend-run backend-stop backend-status backend-clean \
	extension-init extension-build extension-build-worktree extension-test extension-test-e2e extension-test-a11y extension-lint extension-format extension-format-check extension-typecheck extension-clean \
	all-verify backend-verify extension-verify

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

all-init: ## Install dependencies/hooks for all sub-projects
	@./scripts/setup-git-hooks.sh
	@$(MAKE) backend-init
	@$(MAKE) extension-init

init: ## DEPRECATED: Use all-init instead, kept for backward compatibility
	@$(MAKE) all-init

all-build: ## Build artifacts for all sub-projects
	@$(MAKE) extension-build

build: ## DEPRECATED: Use all-build instead, kept for backward compatibility
	@$(MAKE) all-build

all-test: ## Run backend + extension test suites
	@./scripts/test_worktree.sh

test: ## DEPRECATED: Use all-test instead, kept for backward compatibility
	@$(MAKE) all-test

all-lint: ## Run lint checks across backend and extension
	@./scripts/lint.sh

lint: ## DEPRECATED: Use all-lint instead, kept for backward compatibility
	@$(MAKE) all-lint

all-format: ## Format backend and extension source
	@./scripts/format.sh

format: ## DEPRECATED: Use all-format instead, kept for backward compatibility
	@$(MAKE) all-format

all-typecheck: ## Run type checks across backend and extension
	@./scripts/typecheck.sh

typecheck: ## DEPRECATED: Use all-typecheck instead, kept for backward compatibility
	@$(MAKE) all-typecheck

all-run: ## Start local worktree stack (backend + extension build)
	@./scripts/run_worktree_stack.sh

run: ## DEPRECATED: Use all-run instead, kept for backward compatibility
	@$(MAKE) all-run

all-clean: ## Remove local build and cache artifacts
	@$(MAKE) backend-clean
	@$(MAKE) extension-clean
	@find backend extension -type d -name '__pycache__' -prune -exec rm -rf {} +

clean: ## DEPRECATED: Use all-clean instead, kept for backward compatibility
	@$(MAKE) all-clean

all-verify: ## Runs all checks (test, lint, typecheck, format) to verify that the project is releasable.
	@$(MAKE) backend-verify
	@$(MAKE) extension-verify

verify: ## DEPRECATED: Use all-verify instead, kept for backward compatibility
	@$(MAKE) all-verify

worktree-start: ## Create a feature worktree without GitHub issue integration (slug required)
	@./scripts/start-worktree-task.sh $(slug) $(base)

backend-verify: ## Runs all backend checks (test, lint, typecheck, format) to verify that the backend is releasable.
	@$(MAKE) backend-test
	@$(MAKE) backend-lint
	@$(MAKE) backend-typecheck
	@$(MAKE) backend-format-check

backend-init: ## Install backend dependencies in backend/.venv
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(PIP) install -r backend/requirements.txt
	@$(PIP) install -r backend/requirements-dev.txt

backend-test: ## Run backend tests (worktree-aware)
	@cd backend && ./scripts/test.sh

backend-lint: ## Run backend lint checks (ruff)
	@cd backend && python -m ruff check .

backend-format: ## Format backend source (black)
	@cd backend && python -m black .

backend-format-check: ## Check backend formatting compliance (black --check)
	@cd backend && python -m black --check .

backend-typecheck: ## Run backend type checks (mypy)
	@cd backend && python -m mypy .

backend-run: ## Start backend server for current worktree
	@cd backend && ./scripts/start-server.sh

backend-stop: ## Stop backend server for current worktree
	@cd backend && ./scripts/stop-server.sh

backend-status: ## Check backend server status/url for current worktree
	@cd backend && ./scripts/check-server.sh

backend-clean: ## Remove backend cache artifacts
	@rm -rf backend/.mypy_cache backend/.pytest_cache

extension-init: ## Install extension dependencies
	@cd extension && pnpm install --frozen-lockfile

extension-build: ## Build extension artifacts
	@cd extension && pnpm run build

extension-build-worktree: ## Build extension for current worktree runtime
	@cd extension && pnpm run build:worktree

extension-verify: ## Runs all extension checks (test, lint, typecheck, format) to verify that the extension is releasable.
	@$(MAKE) extension-test
	@$(MAKE) extension-lint
	@$(MAKE) extension-typecheck
	@$(MAKE) extension-format-check
	@$(MAKE) extension-test-a11y
	@$(MAKE) extension-test-e2e

extension-test: ## Run extension unit tests
	@cd extension && pnpm test

extension-test-e2e: ## Run extension end-to-end tests
	@cd extension && pnpm run test:e2e

extension-test-a11y: ## Run extension/frontend accessibility audits (WCAG 2.1 A/AA)
	@cd extension && pnpm run test:a11y

extension-lint: ## Run extension lint checks (eslint)
	@cd extension && pnpm run lint

extension-format: ## Format extension source (prettier)
	@cd extension && pnpm run format

extension-format-check: ## Check extension formatting compliance (prettier --check)
	@cd extension && pnpm run format:check

extension-typecheck: ## Run extension type checks (tsc --noEmit)
	@cd extension && pnpm run typecheck

extension-clean: ## Remove extension build/worktree artifacts
	@rm -rf extension/chrome/dist
	@rm -rf extension/.local/worktrees
