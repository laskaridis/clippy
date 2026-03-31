# Multi-Instance Local Docker Sandbox Environment

This plan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

After this change, a developer can start one or more isolated local coding sandboxes with `make sandbox-start name=<id>`, connect to each sandbox through SSH or VS Code Remote-SSH, open the sandboxed web app in the host browser, and load the sandbox-built Chrome extension from a host-visible directory. Each sandbox keeps its own cloned repository, PostgreSQL data, backend port, SSH port, and extension export path so multiple sandboxes can run in parallel without colliding.

The sandbox is the execution surface for coding, testing, and local runtime work. The host remains the operator surface for Docker, SSH, VS Code, Chrome, and manual validation. The observable result is that a developer can boot `alpha` and `beta`, browse each backend on a different localhost port, and load each unpacked extension from a different host directory while source editing stays inside the sandbox.

## Progress

- [x] (2026-03-31 10:15Z) Reviewed repository workflow, toolchain pins, Makefile targets, backend bootstrap scripts, and CI to derive the real sandbox requirements.
- [x] (2026-03-31 10:31Z) Aligned the design on self-contained multi-instance sandboxes with in-container PostgreSQL, only GitHub/OpenAI host secrets, host browser access for the web app, and host-visible unpacked extension exports.
- [x] (2026-03-31 10:40Z) Removed the mistaken `feature/align-sandbox-spec` worktree and branch created in error.
- [x] (2026-03-31 13:49Z) Restored workflow compliance on this task branch and created the initial `infra/sandbox/` scaffold (`Dockerfile`, `entrypoint.sh`, `.env.example`, `README.md`) required for the next implementation steps.
- [ ] Implement sandbox assets under `infra/sandbox/` and the new Make targets in the root `Makefile`.
- [ ] Add the sandbox README/env template and document the exact user-facing start, access, and destroy flows.
- [ ] Validate that at least two named sandboxes can run in parallel with distinct SSH ports, web ports, database volumes, and extension export directories.

## Surprises & Discoveries

- Observation: The repository source of truth for tool versions is `.tool-versions`, not the current backend README or GitHub Actions workflow.
  Evidence: `.tool-versions` pins Python `3.13.5`, Node.js `22.21.0`, and pnpm `9.15.1`, while the current CI still uses Python `3.12` and Node `20`.

- Observation: The current backend bootstrap already supports a non-Docker database path cleanly when `DATABASE_URL` is set.
  Evidence: `backend/scripts/bootsrap.sh` documents Docker-managed Postgres only as the fallback when `DATABASE_URL` is unset, so a sandbox-local PostgreSQL service can become the default without reworking the runtime contract.

- Observation: The existing worktree for this feature is on branch `development-sandbox-env`, which does not satisfy the repository preflight rule requiring `feature/<slug>`.
  Evidence: Running `./scripts/agent-preflight.sh` in `.worktrees/development-sandbox-env` fails with `branch 'development-sandbox-env' must match feature/<slug>`.

## Decision Log

- Decision: Use one named sandbox per `make sandbox-start name=<id>` invocation instead of a single implicit sandbox.
  Rationale: The user wants multiple sandboxes in parallel and stable Make targets. A required `name=<id>` parameter makes container names, host ports, volumes, and export directories deterministic and easy to reason about.
  Date/Author: 2026-03-31 / Codex

- Decision: Install PostgreSQL inside the sandbox container and export a default `DATABASE_URL` automatically.
  Rationale: The user wants a self-contained sandbox and does not want to provide database-related host environment variables. This also avoids mounting the host Docker socket into the sandbox.
  Date/Author: 2026-03-31 / Codex

- Decision: Use the host browser as the inspection surface for the web app and the Chrome extension.
  Rationale: This is the simplest multi-instance model. Each sandbox only needs a published host web port and a host-visible unpacked extension directory, while source editing remains inside the sandbox via SSH or VS Code Remote-SSH.
  Date/Author: 2026-03-31 / Codex

- Decision: Treat `.tool-versions` as the source of truth for Python, Node.js, and pnpm in the sandbox.
  Rationale: The user explicitly called out version drift, and `.tool-versions` is the repository artifact intended to track these tool versions.
  Date/Author: 2026-03-31 / Codex

- Decision: Require only GitHub/OpenAI-related secrets from the host environment.
  Rationale: This keeps the startup path simple. SSH public key lookup should use standard local defaults, and database configuration should be internal to the sandbox bootstrap.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

The implementation has not been started yet. The main outcome of this revision is a decision-complete plan that corrects the previous design drift. The earlier draft assumed Docker would remain external to the sandbox and that host-side worktrees would be replaced wholesale. The aligned design instead keeps the sandbox self-contained, preserves host browser access, and scopes the first iteration to two explicit lifecycle targets plus the minimum host integration needed for manual testing.

The main remaining risk is workflow compliance. The existing feature worktree branch name does not satisfy `docs/DEVELOPMENT_WORKFLOW.md`, so implementation should either rename the branch or get explicit user approval to continue under this branch despite the preflight failure.

## Context and Orientation

This repository currently has two application surfaces. The backend lives under `backend/` and is a Django application. The browser extension lives under `extension/` and is built with Node.js and pnpm. The root `Makefile` is the canonical entrypoint for local workflows and already exposes backend, extension, and cross-project verification commands such as `make all-test` and `make all-verify`.

The existing backend runtime contract is defined by `backend/scripts/bootsrap.sh`. That script computes stable per-worktree environment files and runtime metadata, and it only starts Docker-managed PostgreSQL when `DATABASE_URL` is not already set. This matters because the sandbox can remain compatible with the current backend startup scripts by exporting a sandbox-local `DATABASE_URL` and letting the existing scripts continue unchanged.

The extension build contract is defined by `extension/package.json` and `extension/scripts/prepare-worktree-extension.mjs`. `pnpm run build:worktree` produces an unpacked extension directory and runtime metadata. The Chrome browser only needs a filesystem path to the unpacked extension. That means the sandbox does not need to run Chrome itself if it can copy or mirror the unpacked extension to a host-visible path.

The repository already uses `.tool-versions` to pin Python, Node.js, and pnpm. Any sandbox implementation that hardcodes other versions will drift from the repo. The current docs and CI still mention older versions in places, so the sandbox work must document the mismatch and standardize on `.tool-versions`.

The agreed operating model for this feature is narrow on purpose. A sandbox is one Docker container with a non-root developer user, an SSH server, a cloned copy of this repository, all required local development tools, PostgreSQL running inside the same container, and outbound network access for GitHub, package registries, and OpenAI APIs. The host starts and destroys sandboxes with Docker-backed Make targets, then uses SSH, VS Code Remote-SSH, the host browser, and host Chrome for interaction.

## Plan of Work

Start by adding a new `infra/sandbox/` directory. Put the container build and bootstrap assets there: a `Dockerfile`, an `entrypoint.sh`, a small shared shell helper if the entrypoint would otherwise become monolithic, a `.env.example`, and a focused README. The `Dockerfile` should build an Ubuntu LTS image, create a non-root `agent` user with passwordless `sudo`, install OpenSSH server/client, Git, Make, curl, wget, PostgreSQL server/client packages, and the common shell utilities used in this repository. It must also install the versions pinned in `.tool-versions`: Python `3.13.5`, Node.js `22.21.0`, and pnpm `9.15.1`. Install GitHub CLI and the Codex CLI package `@openai/codex`. Install Playwright CLI plus the Chromium system dependencies needed for headless browser use inside the container.

Implement the `entrypoint.sh` so it is idempotent. On every start it should ensure the `agent` user exists, configure `sshd`, initialize PostgreSQL if the data directory is empty, start PostgreSQL, create the sandbox-local application database and role if missing, export a default `DATABASE_URL`, and make the OpenAI environment variables available in login shells. On first start only, it should clone the repository into `/workspace/webclippings` from the current origin URL `https://github.com/laskaridis/clippy.git`, authenticate `gh` using `GH_TOKEN`, and prepare a host-visible export directory for extension artifacts. On later starts it must reuse the existing home, workspace, and database state without resetting the clone or dropping data.

Update the root `Makefile` to add two stable lifecycle targets only: `sandbox-start` and `sandbox-destroy`. `sandbox-start` should require `name=<id>` and compute deterministic resource names from that id: container name, workspace volume, home volume, Postgres volume, host SSH port, host web port, and host extension export directory. It should build the image if needed, create the export directory under `.local/sandboxes/<id>/exports/extension`, run the container with the required volume mounts and published ports, inject OpenAI/GitHub environment variables from the host, install the user’s SSH public key into `authorized_keys`, and print the exact connection strings and paths the user needs. `sandbox-destroy` should stop and remove only the named container and its instance-specific volumes and export directory, while leaving the image cached.

Keep web-app access simple. The container should publish one host port per sandbox for the Django app. The backend process inside the sandbox must bind to `0.0.0.0` so the host browser can reach it through `http://localhost:<web-port>`. The startup output for `sandbox-start` must print that URL explicitly.

Keep extension access simple too. Do not mirror the full repository back to the host. Instead, add a small documented mechanism so that after `pnpm run build:worktree` inside the sandbox, the resulting unpacked Chrome extension is copied or synchronized into the host-visible path `.local/sandboxes/<id>/exports/extension`. The `sandbox-start` output must print that path explicitly so the user can load it in host Chrome as an unpacked extension.

Document the expected operating model in `infra/sandbox/README.md`. That README should explain that source editing happens inside the sandbox through SSH or VS Code Remote-SSH, while the host browser opens the backend URL and host Chrome loads the exported extension directory. It should also document that only `OPENAI_API_KEY` and `GH_TOKEN` are required host secrets, with `OPENAI_BASE_URL`, `OPENAI_ORG_ID`, and `OPENAI_PROJECT_ID` remaining optional.

If the implementation reveals additional deferred cleanup, such as updating CI or repo docs that still reference older tool versions, record that explicitly in `docs/TECH_DEBT_BACKLOG.md` rather than quietly ignoring the mismatch.

## Concrete Steps

Work from the existing feature worktree:

    cd /Users/e.laskaridis/Projects/sandbox/webclippings/.worktrees/development-sandbox-env

Inspect the pinned tool versions before writing the Docker image:

    sed -n '1,40p' .tool-versions

Expected output:

    python 3.13.5
    nodejs 22.21.0
    pnpm 9.15.1

Create the sandbox assets and Makefile wiring. The exact file set at the end of this milestone should include:

    infra/sandbox/Dockerfile
    infra/sandbox/entrypoint.sh
    infra/sandbox/.env.example
    infra/sandbox/README.md

Run the new lifecycle target for one sandbox:

    make sandbox-start name=alpha

Expected output should include, at minimum, an SSH command, a web URL, and a host extension path, for example:

    ssh agent@localhost -p 2222
    VS Code Remote-SSH: agent@localhost:2222
    Web app: http://localhost:8123
    Load extension from: .local/sandboxes/alpha/exports/extension

Connect to the sandbox and verify the toolchain:

    ssh agent@localhost -p <ssh-port>
    python --version
    node --version
    pnpm --version
    gh auth status
    codex --version
    pg_isready

Inside the sandbox clone, prepare and run the app:

    cd /workspace/webclippings
    make all-init
    make all-run

Then, from the host, open the printed web URL in a browser. Inside the sandbox, build the extension and confirm the unpacked export appears on the host:

    cd /workspace/webclippings/extension
    pnpm run build:worktree

Start a second sandbox and verify parallel isolation:

    make sandbox-start name=beta

Confirm that `alpha` and `beta` report different SSH ports, different web URLs, and different extension export paths. When finished, remove them independently:

    make sandbox-destroy name=alpha
    make sandbox-destroy name=beta

## Validation and Acceptance

Acceptance is met when a developer can run `make sandbox-start name=alpha` from the repository root and receive a ready-to-use local sandbox with no required host secrets other than GitHub/OpenAI credentials. The developer must be able to SSH into that sandbox, open it through VS Code Remote-SSH, verify that the sandbox has Python `3.13.5`, Node.js `22.21.0`, pnpm `9.15.1`, `gh`, Playwright tooling, PostgreSQL, and Codex CLI installed, and confirm that `DATABASE_URL` points to the sandbox-local PostgreSQL instance without requiring extra DB configuration from the host.

The backend acceptance path is behavioral, not just structural. After `make all-init` and `make all-run` inside the sandbox, the host browser must be able to open the sandbox’s printed localhost URL and reach the Django app. The extension acceptance path is also behavioral. After running `pnpm run build:worktree` inside the sandbox, the host-visible directory `.local/sandboxes/<id>/exports/extension` must contain a valid unpacked extension that Chrome can load.

Parallelism is required. Running `make sandbox-start name=alpha` and `make sandbox-start name=beta` must produce two concurrently usable sandboxes with distinct container names, SSH ports, web ports, PostgreSQL volumes, and extension export directories. Destroying one sandbox must not affect the other.

Run repository verification using existing canonical entrypoints from inside one sandbox after the toolchain is installed:

    make all-test
    make all-verify

If the full verification suite is too expensive during iterative work, the minimum proof before handoff is that the sandbox can install dependencies, start the backend, and build the extension in a way that the host can manually inspect.

## Idempotence and Recovery

The sandbox bootstrap must be safe to run multiple times. Re-running `make sandbox-start name=<id>` after a successful first run should reuse the existing container or recreate it against the same named volumes without recloning the repository or reinitializing PostgreSQL data. The entrypoint must check whether the database cluster, application database, repository clone, and `authorized_keys` file already exist before trying to create them again.

If `make sandbox-start` fails after creating some but not all resources, the safe recovery path is to fix the underlying issue and rerun the same command. If the instance is irrecoverable or the developer wants a clean slate, `make sandbox-destroy name=<id>` must remove the container, the instance-specific volumes, and the host export directory for that instance only.

If the chosen host port for SSH or the web app is already in use, the command must fail with a precise message naming the conflicting port and sandbox id. It must not silently pick a random port because that would make multi-instance access harder to reason about.

## Artifacts and Notes

Important repository facts that shaped this plan:

    .tool-versions
      python 3.13.5
      nodejs 22.21.0
      pnpm 9.15.1

    backend/scripts/bootsrap.sh
      - uses Docker-managed PostgreSQL only when DATABASE_URL is not set
      - already writes runtime env/json artifacts for the backend

    extension/package.json
      - build:worktree exists already
      - Playwright-based e2e and accessibility checks already exist

Expected sandbox-start output shape:

    Sandbox: webclippings-sandbox-alpha
    SSH: ssh agent@localhost -p 2222
    VS Code Remote-SSH: agent@localhost:2222
    Web app: http://localhost:8123
    Repo: /workspace/webclippings
    Extension export: .local/sandboxes/alpha/exports/extension

## Interfaces and Dependencies

The implementation must add exactly two new user-facing Make targets in the root `Makefile`:

    sandbox-start name=<id>
    sandbox-destroy name=<id>

The sandbox image must provide these concrete tools at the end of bootstrap:

    python 3.13.5
    node 22.21.0
    pnpm 9.15.1
    gh
    make
    git
    codex
    psql
    pg_isready
    playwright

The container runtime contract must include these stable paths and concepts:

    /workspace/webclippings
      The cloned repository inside the sandbox.

    /home/agent
      The persistent home directory used by SSH and VS Code Remote-SSH.

    .local/sandboxes/<id>/exports/extension
      The host-visible unpacked Chrome extension directory for sandbox `<id>`.

The host environment contract must stay intentionally small:

    Required:
      OPENAI_API_KEY
      GH_TOKEN

    Optional:
      OPENAI_BASE_URL
      OPENAI_ORG_ID
      OPENAI_PROJECT_ID

The implementation should install the official Codex CLI from the npm package `@openai/codex`, based on the official OpenAI documentation and repository guidance current as of 2026-03-31.

Revision note: 2026-03-31. Replaced the earlier sandbox spec direction with a self-contained, multi-instance local sandbox design that uses `.tool-versions` as the toolchain source of truth, runs PostgreSQL inside the sandbox, exposes the web app on host ports, and exports only built extension artifacts to the host for Chrome loading.
