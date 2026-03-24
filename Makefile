SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV_DIR := backend/.venv
PIP := $(VENV_DIR)/bin/pip

.PHONY: help all-init all-build all-test all-lint all-format all-typecheck all-run all-clean \
	worktree-start local-env-start local-env-stop local-env-status local-env-teardown \
	backend-init backend-test-unit backend-test-e2e backend-lint backend-format backend-format-check backend-typecheck backend-run backend-stop backend-status backend-clean \
	extension-init extension-build extension-build-worktree extension-test-unit extension-test-e2e extension-test-a11y extension-lint extension-format extension-format-check extension-typecheck extension-clean \
	all-verify backend-verify extension-verify

# Show available commands
help:
	@echo "Project Makefile Targets"
	@echo "========================"
	@echo ""
	@echo "Backend development targets:"
	@echo "  make backend-init              - Install backend dependencies in backend/.venv"
	@echo "  make backend-test-unit         - Run backend non-E2E tests (worktree-aware)"
	@echo "  make backend-test-e2e          - Run backend browser E2E tests (Playwright, opt-in)"
	@echo "  make backend-lint              - Run backend lint checks (ruff)"
	@echo "  make backend-format            - Format backend source (black)"
	@echo "  make backend-format-check      - Check backend formatting compliance (black --check)"
	@echo "  make backend-typecheck         - Run backend type checks (mypy)"
	@echo "  make backend-run               - Start backend server for current worktree"
	@echo "  make backend-stop              - Stop backend server for current worktree"
	@echo "  make backend-status            - Check backend server status/url for current worktree"
	@echo "  make backend-clean             - Remove backend cache artifacts"
	@echo "  make backend-verify            - Run all backend releasability checks"
	@echo ""
	@echo "Extension development targets:"
	@echo "  make extension-init            - Install extension dependencies"
	@echo "  make extension-build           - Build extension artifacts"
	@echo "  make extension-build-worktree  - Build extension for current worktree runtime"
	@echo "  make extension-test-unit       - Run extension unit tests"
	@echo "  make extension-test-e2e        - Run extension end-to-end tests"
	@echo "  make extension-test-a11y       - Run extension/frontend accessibility audits (WCAG 2.1 A/AA)"
	@echo "  make extension-lint            - Run extension lint checks (eslint)"
	@echo "  make extension-format          - Format extension source (prettier)"
	@echo "  make extension-format-check    - Check extension formatting compliance (prettier --check)"
	@echo "  make extension-typecheck       - Run extension type checks (tsc --noEmit)"
	@echo "  make extension-clean           - Remove extension build/worktree artifacts"
	@echo "  make extension-verify          - Run all extension releasability checks"
	@echo ""
	@echo "Project targets:"
	@echo "  make all-init                  - Install dependencies/hooks for all sub-projects"
	@echo "  make all-build                 - Build artifacts for all sub-projects"
	@echo "  make all-test                  - Run backend + extension test suites"
	@echo "  make all-lint                  - Run lint checks across backend and extension"
	@echo "  make all-format                - Format backend and extension source"
	@echo "  make all-typecheck             - Run type checks across backend and extension"
	@echo "  make all-run                   - Start local worktree stack (backend + extension build)"
	@echo "  make all-clean                 - Remove local build and cache artifacts"
	@echo "  make all-verify                - Run all checks (test, lint, typecheck, format)"
	@echo "  make worktree-start            - Create a feature worktree (slug required)"
	@echo "  make local-env-start           - Start worktree-scoped local Docker services"
	@echo "  make local-env-stop            - Stop worktree-scoped local Docker services"
	@echo "  make local-env-status          - Show worktree-scoped local Docker service status"
	@echo "  make local-env-teardown        - Remove worktree-scoped local Docker services and volumes"

# Install dependencies/hooks for all sub-projects
all-init:
	@./scripts/setup-git-hooks.sh
	@$(MAKE) backend-init
	@$(MAKE) extension-init

# Build artifacts for all sub-projects
all-build:
	@$(MAKE) extension-build

# Run backend + extension test suites
all-test:
	@./scripts/test_worktree.sh

# Run lint checks across backend and extension
all-lint:
	@./scripts/lint.sh

# Format backend and extension source
all-format:
	@./scripts/format.sh

# Run type checks across backend and extension
all-typecheck:
	@./scripts/typecheck.sh

# Start local worktree stack (backend + extension build)
all-run:
	@./scripts/run_worktree_stack.sh

# Remove local build and cache artifacts
all-clean:
	@$(MAKE) backend-clean
	@$(MAKE) extension-clean
	@find backend extension -type d -name '__pycache__' -prune -exec rm -rf {} +

# Runs all checks (test, lint, typecheck, format) to verify that the project is releasable.
all-verify:
	@$(MAKE) backend-verify
	@$(MAKE) extension-verify

# Create a feature worktree without GitHub issue integration (slug required)
worktree-start:
	@./scripts/start-worktree-task.sh $(slug) $(base)

# Start worktree-scoped local Docker services
local-env-start:
	@./infra/local/scripts/manage-worktree-compose.sh start

# Stop worktree-scoped local Docker services
local-env-stop:
	@./infra/local/scripts/manage-worktree-compose.sh stop

# Show worktree-scoped local Docker service status
local-env-status:
	@./infra/local/scripts/manage-worktree-compose.sh status

# Remove worktree-scoped local Docker services and volumes
local-env-teardown:
	@./infra/local/scripts/manage-worktree-compose.sh teardown

# Runs all backend checks (test, lint, typecheck, format) to verify that the backend is releasable.
backend-verify:
	@$(MAKE) backend-test-unit
	@$(MAKE) backend-test-e2e
	@$(MAKE) backend-lint
	@$(MAKE) backend-typecheck
	@$(MAKE) backend-format-check

# Install backend dependencies in backend/.venv
backend-init:
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(PIP) install -r backend/requirements-dev.txt

# Run backend non-E2E tests (worktree-aware)
backend-test-unit:
	@cd backend && ./scripts/test.sh

# Run backend browser E2E tests (Playwright, opt-in)
backend-test-e2e:
	@cd backend && ./scripts/test-e2e.sh

# Run backend lint checks (ruff)
backend-lint:
	@cd backend && python -m ruff check .

# Format backend source (black)
backend-format:
	@cd backend && python -m black .

# Check backend formatting compliance (black --check)
backend-format-check:
	@cd backend && python -m black --check .

# Run backend type checks (mypy)
backend-typecheck:
	@cd backend && python -m mypy .

# Start backend server for current worktree
backend-run:
	@cd backend && ./scripts/start-server.sh

# Stop backend server for current worktree
backend-stop:
	@cd backend && ./scripts/stop-server.sh

# Check backend server status/url for current worktree
backend-status:
	@cd backend && ./scripts/check-server.sh

# Remove backend cache artifacts
backend-clean:
	@rm -rf backend/.mypy_cache backend/.pytest_cache

# Install extension dependencies
extension-init:
	@cd extension && pnpm install --frozen-lockfile

# Build extension artifacts
extension-build:
	@cd extension && pnpm run build

# Build extension for current worktree runtime
extension-build-worktree:
	@cd extension && pnpm run build:worktree

# Runs all extension checks (test, lint, typecheck, format) to verify that the extension is releasable.
extension-verify:
	@$(MAKE) extension-test-unit
	@$(MAKE) extension-lint
	@$(MAKE) extension-typecheck
	@$(MAKE) extension-format-check
	@$(MAKE) extension-test-a11y
	@$(MAKE) extension-test-e2e

# Run extension unit tests
extension-test-unit:
	@cd extension && pnpm test

# Run extension end-to-end tests
extension-test-e2e:
	@cd extension && pnpm run test:e2e

# Run extension/frontend accessibility audits (WCAG 2.1 A/AA)
extension-test-a11y:
	@cd extension && pnpm run test:a11y

# Run extension lint checks (eslint)
extension-lint:
	@cd extension && pnpm run lint

# Format extension source (prettier)
extension-format:
	@cd extension && pnpm run format

# Check extension formatting compliance (prettier --check)
extension-format-check:
	@cd extension && pnpm run format:check

# Run extension type checks (tsc --noEmit)
extension-typecheck:
	@cd extension && pnpm run typecheck

# Remove extension build/worktree artifacts
extension-clean:
	@rm -rf extension/chrome/dist
	@rm -rf extension/.local/worktrees
