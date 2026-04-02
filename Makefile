SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV_DIR := backend/.venv
PIP := $(VENV_DIR)/bin/pip
SANDBOX_IMAGE ?= webclippings-sandbox:local

.PHONY: help all-init all-build all-test all-lint all-format all-typecheck all-run all-clean \
	worktree-start local-env-start local-env-stop local-env-status local-env-teardown \
	sandbox-start sandbox-destroy \
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
	@echo "  make sandbox-start name=<id>   - Start or resume a named Docker sandbox"
	@echo "  make sandbox-destroy name=<id> - Remove a named Docker sandbox and its data"
	@echo ""
	@echo "Local environment targets:"
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

# Start or resume a named Docker sandbox instance
sandbox-start:
	@set -euo pipefail; \
	if [[ -z "$(strip $(name))" ]]; then \
		echo "sandbox-start requires name=<id>" >&2; \
		exit 1; \
	fi; \
	if [[ ! "$(name)" =~ ^[a-z0-9-]+$$ ]]; then \
		echo "sandbox-start name must contain only lowercase letters, numbers, and hyphens" >&2; \
		exit 1; \
	fi; \
	sandbox_id="$(name)"; \
	container_name="webclippings-sandbox-$${sandbox_id}"; \
	workspace_volume="$${container_name}-workspace"; \
	home_volume="$${container_name}-home"; \
	postgres_volume="$${container_name}-postgres"; \
	export_dir=".local/sandboxes/$${sandbox_id}/exports/extension"; \
	export_mount="$$(pwd)/$${export_dir}"; \
	hash_value="$$(printf '%s' "$${sandbox_id}" | cksum | awk '{print $$1}')"; \
	ssh_port="$$((2200 + (hash_value % 400)))"; \
	web_port="$$((8200 + (hash_value % 400)))"; \
	repo_url="$$(git config --get remote.origin.url)"; \
	repo_branch="$$(git branch --show-current)"; \
	gh_token="$${GH_TOKEN:-}"; \
	ssh_public_key=""; \
	for candidate in "$$HOME/.ssh/id_ed25519.pub" "$$HOME/.ssh/id_ecdsa.pub" "$$HOME/.ssh/id_rsa.pub"; do \
		if [[ -f "$${candidate}" ]]; then \
			ssh_public_key="$$(<"$${candidate}")"; \
			break; \
		fi; \
	done; \
	if [[ -z "$${gh_token}" ]] && command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then \
		gh_token="$$(gh auth token)"; \
	fi; \
	if ! git ls-remote --exit-code --heads origin "$${repo_branch}" >/dev/null 2>&1; then \
		repo_branch=""; \
	fi; \
	env_args=( \
		-e SANDBOX_REPO_URL="$${repo_url}" \
		-e SANDBOX_EXPORT_DIR="/exports/extension" \
		-e SANDBOX_SSH_PORT="22" \
		-e SANDBOX_WEB_PORT="$${web_port}" \
	); \
	if [[ -n "$${repo_branch}" ]]; then env_args+=( -e SANDBOX_REPO_BRANCH="$${repo_branch}" ); fi; \
	if [[ -n "$${ssh_public_key}" ]]; then env_args+=( -e SANDBOX_SSH_PUBLIC_KEY="$${ssh_public_key}" ); fi; \
	if [[ -n "$${gh_token}" ]]; then env_args+=( -e GH_TOKEN="$${gh_token}" ); fi; \
	if [[ -n "$${OPENAI_API_KEY:-}" ]]; then env_args+=( -e OPENAI_API_KEY="$${OPENAI_API_KEY}" ); fi; \
	if [[ -n "$${OPENAI_BASE_URL:-}" ]]; then env_args+=( -e OPENAI_BASE_URL="$${OPENAI_BASE_URL}" ); fi; \
	if [[ -n "$${OPENAI_ORG_ID:-}" ]]; then env_args+=( -e OPENAI_ORG_ID="$${OPENAI_ORG_ID}" ); fi; \
	if [[ -n "$${OPENAI_PROJECT_ID:-}" ]]; then env_args+=( -e OPENAI_PROJECT_ID="$${OPENAI_PROJECT_ID}" ); fi; \
	check_port() { \
		local port="$$1"; \
		local label="$$2"; \
		if ! python3 -c 'import socket, sys; sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); sock.bind(("127.0.0.1", int(sys.argv[1]))); sock.close()' "$${port}" >/dev/null 2>&1; then \
			echo "sandbox '$${sandbox_id}' cannot start because $${label} port $${port} is already in use" >&2; \
			exit 1; \
		fi; \
	}; \
	docker build -t "$(SANDBOX_IMAGE)" -f infra/sandbox/Dockerfile .; \
	mkdir -p "$${export_mount}"; \
	if docker container inspect "$${container_name}" >/dev/null 2>&1; then \
		if [[ "$$(docker inspect -f '{{.State.Running}}' "$${container_name}")" != "true" ]]; then \
			check_port "$${ssh_port}" "SSH"; \
			check_port "$${web_port}" "web"; \
			docker start "$${container_name}" >/dev/null; \
		fi; \
	else \
		check_port "$${ssh_port}" "SSH"; \
		check_port "$${web_port}" "web"; \
		docker volume create "$${workspace_volume}" >/dev/null; \
		docker volume create "$${home_volume}" >/dev/null; \
		docker volume create "$${postgres_volume}" >/dev/null; \
		docker run -d \
			--name "$${container_name}" \
			-p "$${ssh_port}:22" \
			-p "$${web_port}:$${web_port}" \
			-v "$${workspace_volume}:/workspace" \
			-v "$${home_volume}:/home/agent" \
			-v "$${postgres_volume}:/var/lib/postgresql/data" \
			-v "$${export_mount}:/exports/extension" \
			"$${env_args[@]}" \
			"$(SANDBOX_IMAGE)" >/dev/null; \
	fi; \
	echo "Sandbox: $${container_name}"; \
	echo "SSH: ssh agent@localhost -p $${ssh_port}"; \
	echo "VS Code Remote-SSH: agent@localhost:$${ssh_port}"; \
	echo "Web app: http://localhost:$${web_port}"; \
	echo "Repo: /workspace/webclippings"; \
	echo "Extension export: $${export_dir}"

# Remove a named Docker sandbox instance and its persistent resources
sandbox-destroy:
	@set -euo pipefail; \
	if [[ -z "$(strip $(name))" ]]; then \
		echo "sandbox-destroy requires name=<id>" >&2; \
		exit 1; \
	fi; \
	if [[ ! "$(name)" =~ ^[a-z0-9-]+$$ ]]; then \
		echo "sandbox-destroy name must contain only lowercase letters, numbers, and hyphens" >&2; \
		exit 1; \
	fi; \
	sandbox_id="$(name)"; \
	container_name="webclippings-sandbox-$${sandbox_id}"; \
	workspace_volume="$${container_name}-workspace"; \
	home_volume="$${container_name}-home"; \
	postgres_volume="$${container_name}-postgres"; \
	export_dir=".local/sandboxes/$${sandbox_id}"; \
	if docker container inspect "$${container_name}" >/dev/null 2>&1; then \
		docker rm -f "$${container_name}" >/dev/null; \
	fi; \
	docker volume rm -f "$${workspace_volume}" "$${home_volume}" "$${postgres_volume}" >/dev/null 2>&1 || true; \
	rm -rf "$${export_dir}"; \
	echo "Destroyed sandbox: $${container_name}"

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
