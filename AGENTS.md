# AGENTS.md

Guidelines for coding agents working in this repository.

## Context-Specific Guides

Before doing any work read the `docs/README.md` first to learn about any context-specific documentation available in this project in case you need to access it later.

## Canonical task entrypoints

When working with the codebase prefer `Makefile` as the primary surface of stable tasks for local workflow and automation such as testing, launching servers, initializing environments, running guardrail checks, etc:

- For the live command list, run `make help`.
- `make all-*` targets are the canonical cross-project entrypoints.
- `make backend-*` and `make extension-*` targets are project-scoped entrypoints.
- Backend script wrappers should assume the devcontainer is already prepared and call project commands directly from `backend/` rather than re-running runtime bootstrap helpers.

If you need to do something **ALWAYS** check first if there is a Makefile target that you could use to complete your task. If you can't find one, consider creating one.

For local-development docs, keep the narrative in the devcontainer-first order: worktree, sandbox env inputs/defaults, Dev Containers, `dev-sandbox`, then `make backend-run` when a live backend is needed. Avoid reintroducing host-side bootstrap stories in living docs.
When `.devcontainer/bootstrap.sh` delegates to `make extension-init`, keep the devcontainer image responsible for providing the pinned `pnpm` toolchain up front; do not rely on post-create steps to install the package manager itself.
Host-side devcontainer preflight scripts should reject dirty trees, require explicit sandbox inputs, and validate that `SANDBOX_REPO_URL` is either provided or derivable from the current checkout's `origin` remote. Do not make Compose startup depend on a preflight-generated `.env` file.
The `dev-sandbox` compose service must pass `SANDBOX_REPO_URL`, `GIT_AUTH_TOKEN`, and `SANDBOX_ID` into the container environment, and should carry checked-in defaults inline for non-secret Django/Postgres settings. The image-baked workspace init script reads those values at startup and may derive `SANDBOX_REPO_URL` from the launcher checkout when needed.
When Git credentials must keep working after workspace initialization, bake a reusable askpass helper into the image and point Git's system config at it; do not depend on a one-shot shell wrapper that disappears after the clone step.

## Project Directory Outline

```
├── .codex/      # codex agent specific configuration (i.e. skills, etc)
├── .local/      # artifacts specific to the local environment
├── .specify/    # spec-kit specific files
├── .worktrees/  # required location for all project git worktrees
├── backend/     # backend application (api and web app)
├── docs/        # project's documentation artifacts
├── extension/   # browser app extensions (currently only for chrome)
├── infra/       # infrastructure related artifacts
├── ralph/       # standalone Ralph CLI package and feature-specific harness assets
└── specs/       # feature specifications and implementation plans
```

Ralph agent backends should implement `ralph.agents.base.Agent` and return `AgentResult`; keep lifecycle code backend-agnostic and avoid raw subprocess coupling.
Resolve concrete agent backends through `ralph.agents.factory.resolve_agent()` instead of importing adapters directly from lifecycle code.
Codex-backed adapters should treat the `-o` tempfile as the authoritative result payload and preserve subprocess stderr in `AgentResult.metadata` for diagnostics.
Keep `ralph/ralph.sh` as a compatibility shim that only translates legacy flags into the Python CLI entrypoints and never reimplements feature validation, prompt loading, or orchestration logic.
Ralph session persistence should live behind `ralph.session.RunSessionStore`; write each run to `.ralph/sessions/<session-id>.json` and keep `.ralph/sessions/current.json` pointed at the current incomplete session or the latest terminal session.
For fresh run entrypoints, validate the current-session pointer and lock state before creating a new session, then keep lock ownership, session creation, and the phase loop inside one `finally`-protected block so a failed run cannot strand active ownership.
Keep stale-lock inspection conservative: only the local host can prove the recorded PID is dead, and remote-host locks should remain active until higher-level recovery decides whether to reclaim them.
Keep lock cleanup best-effort and ownership-aware so `finally` blocks never mask the original run or resume failure when the current lock is absent, unreadable, or already belongs to another session.
Phase-local status parsers should normalize CRLF before exact first-line comparisons and preserve the remaining response body for diagnostics.

## Front-end development

Before writing any code that includes any kind of **front-end** changes **ALLWAYS** read `docs/frontend.md` to learn about the core principles, rules and guidelines followed in this project.

For the browser extension shared config, keep the precedence order explicit: runtime config first, manifest host_permissions second, and the hard-coded localhost fallback last. When updating `extension/chrome/manifest.json`, keep localhost wildcard permissions before any non-local example host so the manifest fallback stays deterministic.
Extension Playwright helpers should load the checked-in `extension/chrome` directory directly and, when they need to self-start the backend, do so with `make backend-run` from the repository root instead of any generated worktree runtime file or deleted bootstrap script.
When removing obsolete helper scripts, delete any thin wrappers that still invoke them and scrub live README references before running repo-wide reference audits.
When superseding an ADR, add a new numbered ADR with an explicit supersession statement rather than rewriting the earlier record as if history changed.
