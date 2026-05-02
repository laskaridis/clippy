# Devcontainer-First Worktree Runtime Simplification

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [docs/PLANS.md](docs/PLANS.md).

## Purpose / Big Picture

After this change, a developer will still create feature branches in `.worktrees/`, but local runtime isolation will come from one devcontainer per worktree instead of from a large set of host-side bootstrap scripts. The devcontainer `dev-sandbox` service is the intended development sandbox for implementation work, especially when coding agents are modifying the checkout. It is not a backend container; it is an idle sandbox machine that stays alive with `sleep infinity` so a human developer or coding agent can decide when to run Django, Chromium, tests, or any other project command. The developer experience becomes: create the worktree, set the worktree's local devcontainer values, start the devcontainer, perform implementation work inside the `dev-sandbox` container, manually launch the backend only when verification or troubleshooting requires it, verify the feature from the host browser against `http://localhost:<port>`, and ship.

Today the repository carries a second isolation system on top of git worktrees: deterministic per-worktree hostnames, per-worktree PostgreSQL ports, backend runtime JSON and env artifacts, PID and lock files, worktree-specific extension output directories, and helper scripts that start and stop Docker services on the host. That system is spread across Make targets, backend scripts, extension scripts, infra scripts, docs, and local agent skills. The goal of this change is to remove that entire runtime-management layer and replace it with a much smaller contract centered on `.devcontainer/docker-compose.yml` plus one untracked `.devcontainer/.env` file per worktree. In the new world, source isolation comes from separate git worktrees, devcontainer lifecycle is managed only through Dev Containers tooling, compose-managed resource isolation comes from that startup path, and host-visible runtime isolation comes from unique `DJANGO_DEV_PORT` values when two worktrees run in parallel.

The observable success condition is simple. In two separate worktrees, two separate devcontainers can be started through Dev Containers tooling with different `DJANGO_DEV_PORT` values. When the developer or coding agent starts Django manually inside each sandbox, each backend is reachable from the host browser at its own `http://localhost:<port>` origin, the Chrome extension can talk to the correct backend without generating worktree runtime artifacts, and no living docs or commands still direct users to the removed worktree bootstrap flow.

## Progress

- [x] (2026-05-01 19:05Z) Audited the repository surfaces tied to the current worktree runtime model, including Make targets, backend scripts, extension build scripts, infra helpers, skills, and living docs.
- [x] (2026-05-01 19:15Z) Chosen replacement model: keep git worktrees, use one devcontainer per worktree, expose backend to the host on a per-worktree port, and remove the legacy runtime-management layer with a hard cutover.
- [x] (2026-05-01 19:25Z) Authored this ExecPlan at `docs/plans/devcontainers/spec.md`.
- [x] (2026-05-02 11:31Z) Reworked the devcontainer bootstrap path to use repository Make targets and the active container Python for backend dependency installation.
- [x] (2026-05-02 12:18Z) Updated `.devcontainer/` to be the only local runtime orchestration surface and documented the new per-worktree `.env` contract.
- [x] (2026-05-02 12:18Z) Removed host-side runtime orchestration from `Makefile`, `backend/scripts/`, `infra/local/scripts/`, `scripts/`, and `extension/package.json`.
- [x] (2026-05-02 12:18Z) Simplified extension local runtime configuration so Chrome loads directly from `extension/chrome` while targeting the correct backend origin.
- [x] (2026-05-02 12:18Z) Removed or updated agent skills and workflow gates that depended on worktree runtime artifacts or bootstrap scripts.
- [x] (2026-05-02 12:18Z) Updated living documentation and added an ADR that supersedes the local runtime decision captured in `docs/adrs/0003-worktree-backend-entrypoint-and-env-contract.md`.
- [x] (2026-05-02 09:27Z) Ran `make help`, `make backend-test-unit`, `make backend-test-e2e`, `make extension-test-unit`, `make extension-test-e2e`, `make extension-test-a11y`, and `make all-verify` from the repository root; all passed when run with devcontainer-equivalent env overrides and `DATABASE_URL=postgres://webclippings:password@localhost:15518/webclippings`.
- [ ] Run the manual parallel devcontainer check across two worktrees.

## Surprises & Discoveries

- Observation: the current runtime-management layer is larger than it first appears. It is not only `backend/scripts/bootsrap.sh`; it also includes PID and lock lifecycle scripts, infra compose wrappers, extension packaging, Make targets, tests, and agent skills.
  Evidence: `wc -l` across the directly affected scripts shows more than 2,200 lines tied to the legacy runtime flow, including `backend/scripts/bootsrap.sh` at 487 lines and `infra/local/scripts/manage-worktree-compose.sh` at 202 lines.

- Observation: the extension can be simplified more aggressively than the backend because it already supports a runtime URL override through `runtime-config.js`.
  Evidence: `extension/chrome/src/shared/config.ts` prefers `globalThis.WEBCLIPPINGS_RUNTIME_CONFIG.apiBaseUrl` before falling back to `manifest.json` host permissions.

- Observation: the workflow rules around `.worktrees/` and `feature/<slug>` branches remain useful even after the runtime cleanup.
  Evidence: `scripts/start-worktree-task.sh`, `scripts/agent-preflight.sh`, `.agents/skills/worktree-task-start/`, `.agents/skills/worktree-cleanup/`, and `.agents/skills/workflow-audit/` are about repository hygiene, not backend or Docker orchestration.

- Observation: separate git worktree mounts do not by themselves prevent runtime conflicts between parallel devcontainers.
  Evidence: each worktree has its own checkout path, but host-visible port bindings still collide if both sandboxes publish the same backend port. Compose-managed resource isolation still depends on starting each worktree through the supported Dev Containers flow.

- Observation: the extension's local development contract depends on both backend-origin selection and extension host permissions.
  Evidence: `extension/scripts/prepare-worktree-extension.mjs` currently rewrites `manifest.json` host permissions and `runtime-config.js`, while `extension/chrome/src/shared/config.ts` only reads the runtime URL override and does not grant new permissions by itself.

## Decision Log

- Decision: keep git worktrees as the branching and task-isolation mechanism.
  Rationale: the user's desired workflow still starts by creating a worktree under `.worktrees/`, and the current worktree naming, cleanup, and audit helpers remain useful without carrying the old runtime complexity.
  Date/Author: 2026-05-01 / Codex

- Decision: move runtime isolation fully into devcontainers and remove the host-side worktree bootstrap layer with a hard cutover.
  Rationale: the user explicitly wants the project simplified around "devcontainers + worktrees" and prefers deletion over compatibility wrappers.
  Date/Author: 2026-05-01 / Codex

- Decision: standardize host-visible backend access on per-worktree `localhost` ports rather than per-worktree hostnames such as `clippy-<hash>.localhost`.
  Rationale: this preserves parallel browser verification from the host while removing the deterministic hostname and runtime-artifact machinery that exists mainly to support the old system.
  Date/Author: 2026-05-01 / Codex

- Decision: keep PostgreSQL internal to the devcontainer compose network and stop publishing it on a host port.
  Rationale: the new workflow only requires host-visible access to the backend for browser and extension verification. Exposing PostgreSQL from every worktree is unnecessary and makes collisions more likely.
  Date/Author: 2026-05-01 / Codex

- Decision: keep the `dev-sandbox` service as an idle sandbox container rather than auto-starting Django or any other project process.
  Rationale: the user wants the devcontainer to act as a development machine, not as a backend runtime container. Human developers and coding agents should decide when to launch Django, Chromium, tests, or debugging tools from inside that sandbox.
  Date/Author: 2026-05-01 / Codex

- Decision: support Dev Containers startup as the only local sandbox lifecycle entrypoint and require only `DJANGO_DEV_PORT` to differ between parallel worktrees.
  Rationale: the intended workflow always starts the sandbox through Dev Containers tooling rather than raw `docker compose`. In that model, compose-managed resource isolation comes from the devcontainer startup semantics, while a unique backend port still isolates host-browser access.
  Date/Author: 2026-05-01 / Codex

- Decision: optimize the local extension workflow for one active worktree at a time on a developer workstation.
  Rationale: the user does not need to test multiple extension variants at once locally, so the simplest acceptable contract is to load `extension/chrome` directly, keep host permissions broad enough for localhost development, and rewrite `runtime-config.js` locally per worktree even if that leaves the worktree dirty.
  Date/Author: 2026-05-01 / Codex

- Decision: treat `docs/plans/` as ExecPlan territory, not spec-kit territory.
  Rationale: `docs/PLANS.md` defines a stricter format for executable plan documents than `.specify/templates/spec-template.md`, and this file must be directly implementable from the `docs/plans/` tree.
  Date/Author: 2026-05-01 / Codex

## Outcomes & Retrospective

As of 2026-05-02 09:27Z, the automated handoff gate is green. `make help`, `make backend-test-unit`, `make backend-test-e2e`, `make extension-test-unit`, `make extension-test-e2e`, `make extension-test-a11y`, and `make all-verify` all passed from the repository root when supplied the equivalent devcontainer env, including `DJANGO_DEV_PORT=8794`, localhost-only `ALLOWED_HOSTS`, and `DATABASE_URL=postgres://webclippings:password@localhost:15518/webclippings`.

The reference audit command `rg -n "bootsrap.sh|worktree-runtime-|worktree-env-|local-env-|build:worktree|start-server.sh|stop-server.sh|check-server.sh" .` now reports only intentional historical matches in `docs/plans/**` and the superseded ADR `docs/adrs/0003-worktree-backend-entrypoint-and-env-contract.md`. No live code or living-document matches remain outside those preserved historical records.

The remaining risk is operational rather than code-level: the manual two-worktree Dev Containers smoke check is still pending as task 21. This ExecPlan now demonstrates one coherent local-development story at the automated-validation layer, but final closure still depends on recording the real parallel-worktree browser check rather than assuming it passed.

## Context and Orientation

This repository has three different concerns that must not be confused.

First, git worktrees are separate checkouts under `.worktrees/` used to isolate branches and task context. That concern lives mainly in `scripts/start-worktree-task.sh`, `scripts/agent-preflight.sh`, and the related skills under `.agents/skills/worktree-task-start/`, `.agents/skills/worktree-cleanup/`, and `.agents/skills/workflow-audit/`.

Second, the current local runtime system is a custom "bootable worktree" layer. In this repository, that means host-side scripts derive a worktree identifier from the checkout path, allocate deterministic ports and hostnames, start PostgreSQL with a worktree-specific Docker Compose project, generate `backend/.local/worktree-env-<id>.env` and `backend/.local/worktree-runtime-<id>.json`, and then coordinate backend startup and extension packaging around those files. The core entrypoint is `backend/scripts/bootsrap.sh`, and the rest of the system hangs off it.

Third, the repository already contains the beginnings of the replacement model in `.devcontainer/`. `devcontainer.json` points at `.devcontainer/docker-compose.yml` and runs `.devcontainer/bootstrap.sh` after container creation. In the target design, the `dev-sandbox` service defined there is not a backend service; it is an idle development sandbox where implementation work happens. It stays alive so a developer or coding agent can run backend commands, browser tooling, tests, or ad hoc debugging commands from inside the same isolated environment. That matters because the repository should stop assuming that coding agents or developers are driving backend bootstrap directly from the host shell. The goal of this ExecPlan is to make `.devcontainer/` the only local runtime orchestration surface and delete the second concern entirely.

The main files and directories affected are as follows.

`Makefile` currently exposes both project-level quality commands and runtime-management commands such as `all-run`, `local-env-start`, `backend-run`, `backend-stop`, `backend-status`, and `extension-build-worktree`.

`backend/scripts/bootsrap.sh`, `backend/scripts/env.sh`, `backend/scripts/start-server.sh`, `backend/scripts/stop-server.sh`, and `backend/scripts/check-server.sh` implement the current worktree-aware backend runtime contract. `backend/scripts/test.sh` and `backend/scripts/test-e2e.sh` depend on the same contract through `infra/local/scripts/ensure-worktree-runtime.sh`.

`infra/local/scripts/manage-worktree-compose.sh` and `infra/local/scripts/ensure-worktree-runtime.sh` manage host-side Docker Compose services using runtime metadata derived from `bootsrap.sh`.

`extension/scripts/prepare-worktree-extension.mjs` creates worktree-specific unpacked extension directories under `extension/.local/worktrees/<worktree-id>/chrome` and generates runtime metadata and `runtime-config.js` files based on backend runtime JSON.

`.agents/skills/worktree-bootstrap/` and `.agents/skills/feature-delivery-gate/` still assume the old runtime model. The `worktree-bootstrap` skill exists solely to run the old flow, while the feature-delivery gate still reaches for `scripts/test_worktree.sh` and `.local/worktree-env-*.env`.

The living docs that currently teach the old system include `backend/README.md`, `extension/README.md`, `infra/docker/README.md`, `docs/DEVELOPMENT_WORKFLOW.md`, and feature quickstarts under `specs/` that still instruct users to run `bootsrap.sh` or `make backend-run` under the old semantics.

## Plan of Work

The work begins in `.devcontainer/`. Update `.devcontainer/docker-compose.yml` so it expresses the new local contract directly. Rename the current `app` service to `dev-sandbox` so the service name reflects its purpose. The `dev-sandbox` container must mount the repository, stay alive as an idle sandbox, receive the required backend environment variables, and publish the backend's `DJANGO_DEV_PORT` from container to host without auto-starting Django. The supported lifecycle entrypoint for that sandbox must be Dev Containers tooling, not raw `docker compose` commands in user-facing workflow docs. The postgres service must remain reachable from the `dev-sandbox` container by service name, but it must no longer bind `5432` on the host. Update `.devcontainer/.env.example` so it documents the minimum required local values, especially `DJANGO_DEV_PORT`, `ALLOWED_HOSTS`, and the PostgreSQL connection settings expected inside the container network. Add whatever `.gitignore` exception is necessary so `.devcontainer/.env.example` remains tracked even though `.env.*` files are generally ignored. Replace `.devcontainer/bootstrap.sh` so it prepares both backend and extension dependencies through the repository's own workflow entrypoints instead of only running `pip install` inside `backend/`, and make the resulting contract explicit: the devcontainer image/bootstrap provides the backend and extension tooling on `PATH`, and the container-first flow does not rely on `backend/.venv`.

Then simplify `Makefile` so it no longer presents two overlapping runtime stories. Remove `all-run`, `local-env-start`, `local-env-stop`, `local-env-status`, `local-env-teardown`, `backend-stop`, `backend-status`, and `extension-build-worktree`. Keep the stable quality-oriented targets. Redefine `backend-run` as the single backend start command for use inside the devcontainer when a developer or coding agent wants a live backend. It should perform the local bootstrap work that still matters in the new world: run Django migrations, ensure the local admin user exists using `apps.accounts.bootstrap.ensure_admin_user_from_env`, and start `python manage.py runserver 0.0.0.0:${DJANGO_DEV_PORT}`. Because the Docker Compose service now owns only container lifecycle and not Django lifecycle, there is no need for PID files, lock files, or host-side "stop" and "status" wrappers. The surviving Make targets should read naturally as commands that a developer or agent executes from inside the `dev-sandbox` container.

After that, remove the legacy backend runtime scripts and the infra wrappers that exist only to support them. Delete `backend/scripts/bootsrap.sh`, `backend/scripts/env.sh`, `backend/scripts/start-server.sh`, `backend/scripts/stop-server.sh`, `backend/scripts/check-server.sh`, `infra/local/scripts/manage-worktree-compose.sh`, `infra/local/scripts/ensure-worktree-runtime.sh`, `scripts/run_worktree_stack.sh`, and `scripts/test_worktree.sh`. Update `backend/scripts/test.sh` and `backend/scripts/test-e2e.sh` so they assume the devcontainer environment is already valid and run directly against that environment without generating or sourcing worktree env artifacts.

Next, simplify the extension build and E2E flow. Remove `extension/scripts/prepare-worktree-extension.mjs` and the `prepare:worktree` and `build:worktree` package scripts. The new local extension contract is intentionally optimized for one active worktree at a time on a developer workstation. The normal build writes compiled assets to `extension/chrome/dist`, and a lightweight runtime-config generation step updates `extension/chrome/runtime-config.js` in place from environment values already available inside the devcontainer. Chrome should load the unpacked extension directly from `extension/chrome`, not from a generated worktree-specific directory under `extension/.local/`. Because `runtime-config.js` only chooses the backend origin and does not grant extension permissions, update `extension/chrome/manifest.json` so the local-development host permissions cover localhost development across arbitrary backend ports rather than a single fixed port. The acceptable tradeoff is that rewriting `runtime-config.js` locally per worktree may leave that worktree dirty. Update the Playwright support code under `extension/chrome/e2e/support/runtime.ts` to read configuration from environment rather than from `extension/.local/worktree-runtime-<id>.json`.

Then clean up the workflow and agent layer. Delete `.agents/skills/worktree-bootstrap/` because its only purpose is to validate the old runtime scheme. Update `.agents/skills/feature-delivery-gate/` so its default checks are the worktree hygiene gate, relevant project verification targets, and PR presence. Keep the skills that remain aligned with the new workflow: worktree creation, cleanup, and audit.

Finally, update the living documents and architecture record. Rewrite `docs/DEVELOPMENT_WORKFLOW.md` around the user's desired sequence: create a worktree, start a devcontainer for that worktree, create the spec and tasks, run the implementation loop, verify, and ship. Update `backend/README.md`, `extension/README.md`, `infra/docker/README.md`, and `docs/TESTING.md` so every example command reflects the new model. Do not rewrite `docs/adrs/0003-worktree-backend-entrypoint-and-env-contract.md` as if history changed; instead, add a new ADR that explicitly supersedes it for local development and records the move to devcontainer-first orchestration plus per-worktree host ports.

## Concrete Steps

Perform the work from the repository root unless a step explicitly says otherwise.

Start by confirming the current command surface and locating all references to the old runtime contract.

    make help
    rg -n "bootsrap.sh|worktree-runtime-|worktree-env-|local-env-|build:worktree|start-server.sh|stop-server.sh|check-server.sh" .

Update `.devcontainer/` first, then validate the Dev Containers configuration before touching downstream tooling.

    Open the worktree in Dev Containers and confirm the sandbox starts successfully with the local `.devcontainer/.env` values.

After simplifying the backend and Make targets, verify that the remaining commands still describe a coherent workflow.

    make help
    make backend-test-unit
    make backend-test-e2e
    make extension-test-unit
    make extension-test-e2e
    make extension-test-a11y
    make all-verify

Validate the new parallel workflow manually with two worktrees. In each worktree, create or edit `.devcontainer/.env` so the sandbox uses a different `DJANGO_DEV_PORT`, then start the corresponding devcontainer through Dev Containers tooling. After both sandboxes are running, start Django manually inside each `dev-sandbox` container and use a host browser to confirm both backends are reachable simultaneously.

    # In worktree A
    Open the worktree in Dev Containers
    make backend-run

    # In worktree B
    Open the worktree in Dev Containers
    make backend-run

The expected result is that `http://localhost:<port-a>/accounts/login/` and `http://localhost:<port-b>/accounts/login/` both load successfully from the host, while there are no generated `backend/.local/worktree-env-*`, `backend/.local/worktree-runtime-*`, or `extension/.local/worktree-runtime-*` files involved in the workflow.

## Validation and Acceptance

The change is accepted only when the repository has one clear local-development story and that story works in practice.

For documentation and command-surface acceptance, `make help` must no longer advertise `all-run`, any `local-env-*` targets, `backend-stop`, `backend-status`, or `extension-build-worktree`. A repository-wide search must show no remaining living-code or living-doc references to `bootsrap.sh`, `worktree-env-`, `worktree-runtime-`, `local-env-`, or `build:worktree`, except for historical records that are intentionally preserved under `docs/plans/` or superseded ADRs.

For backend acceptance, starting the devcontainer alone must not imply that Django is running. Running `make backend-run` inside the `dev-sandbox` devcontainer must migrate the database, ensure the local admin user exists, and start Django on `0.0.0.0:${DJANGO_DEV_PORT}`. From the host machine, visiting `http://localhost:<DJANGO_DEV_PORT>/accounts/login/` must load the Django login page for that worktree.

For extension acceptance, `make extension-build` or the new equivalent local build command must leave `extension/chrome` loadable as an unpacked Chrome extension. The extension must derive the backend API origin from a simple runtime config plus localhost-friendly manifest-permission contract that does not depend on generated worktree runtime JSON. The Playwright extension tests and accessibility tests must pass without generating worktree-specific extension output directories. The local workflow may rewrite `extension/chrome/runtime-config.js` in place for the active worktree.

For workflow acceptance, two worktrees must be able to run in parallel through Dev Containers tooling with different `DJANGO_DEV_PORT` values. In each worktree, the `dev-sandbox` devcontainer must be the assumed sandbox for implementation and verification commands, but Django must start only when the developer or agent explicitly runs `make backend-run`. Both backends must be reachable from the host browser at the same time, and the Chrome extension must be able to target the active worktree by loading that checkout's `extension/chrome` directory.

For regression acceptance, the full verification pass must succeed:

    make all-verify

If `make all-verify` is too expensive during iteration, targeted commands may be used temporarily, but final handoff requires the full pass plus the two-worktree manual check.

## Idempotence and Recovery

This migration should be performed in small, reversible steps. Updating `.devcontainer/`, simplifying Make targets, deleting runtime helpers, and rewriting docs are each safe to do in separate commits as long as the remaining command surface stays coherent after each commit.

All new runtime setup steps must be idempotent. Running `make backend-run` multiple times should be safe because Django migrations are repeatable and `ensure_admin_user_from_env` already updates or creates the local admin user without duplicating it. Rebuilding the extension must overwrite runtime configuration deterministically in place. Starting the devcontainer multiple times with the same `.devcontainer/.env` values must reconcile to the same running services. Running two worktrees in parallel is safe only when their `DJANGO_DEV_PORT` values differ and the worktrees are started through the supported Dev Containers flow.

If a partial migration leaves the repo in a broken intermediate state, recovery means either restoring the last coherent commit or temporarily reintroducing the smallest missing piece needed to keep a single clear local workflow. Do not leave the repository in a mixed state where both the devcontainer flow and the worktree bootstrap flow are half-supported.

## Artifacts and Notes

The current removal scope can be demonstrated with these concise repo facts.

    backend/scripts/bootsrap.sh                  487 lines
    backend/scripts/check-server.sh              155 lines
    backend/scripts/env.sh                       158 lines
    backend/scripts/start-server.sh              144 lines
    backend/scripts/stop-server.sh               138 lines
    infra/local/scripts/manage-worktree-compose.sh 202 lines
    extension/scripts/prepare-worktree-extension.mjs 175 lines
    .agents/skills/worktree-bootstrap/scripts/bootstrap.sh 176 lines

The old command surface currently advertised by `make help` includes the runtime-management commands that this plan removes.

    make all-run
    make local-env-start
    make local-env-stop
    make local-env-status
    make local-env-teardown
    make backend-stop
    make backend-status
    make extension-build-worktree

## Interfaces and Dependencies

The stable interfaces that must exist after implementation are these.

In `Makefile`, keep `worktree-start`, `backend-run`, the existing test and verification targets, and the project-wide quality targets. Remove the targets that exist only to manage host-side worktree runtime state.

In `.devcontainer/docker-compose.yml`, define the `dev-sandbox` and postgres services as the sole local runtime services. The `dev-sandbox` service must serve as the default development sandbox for implementation work, must remain idle until a developer or coding agent launches project processes inside it, must publish the backend port declared by `DJANGO_DEV_PORT`, and must contain the dependencies needed for the project's normal edit, build, and test workflow. The supported lifecycle entrypoint for these services is Dev Containers tooling, which provides the compose project isolation expected for parallel worktrees. The postgres service must not publish a host port by default.

In `backend/scripts/`, reduce the local runtime contract to direct commands that assume the devcontainer environment already exists. There must be no backend entrypoint that synthesizes a worktree identifier, allocates deterministic ports, creates worktree runtime files, or starts Docker itself.

In `extension/package.json`, the local development build flow must rely on the normal build plus a lightweight runtime-config step, not on `prepare:worktree` or `build:worktree`.

In `extension/chrome/src/shared/config.ts`, preserve the simple precedence order of runtime config first, manifest fallback second. That precedence is what allows the extension to keep a small local runtime contract after the worktree-specific artifact layer is removed. In `extension/chrome/manifest.json`, make the local-development host permissions broad enough to support localhost development across arbitrary backend ports.

At the end of the migration, the only per-worktree local runtime input should be the untracked `.devcontainer/.env` file inside each worktree checkout. `DJANGO_DEV_PORT` is the key host-visible differentiator, while compose-managed resource isolation comes from starting each worktree through Dev Containers tooling.

Revision note: 2026-05-01. Updated the ExecPlan after clarifying that the `dev-sandbox` container is an idle development sandbox rather than a backend container, that worktree sandboxes are started only through Dev Containers tooling, that parallel worktrees require unique `DJANGO_DEV_PORT` values, and that the local extension flow should be optimized for one active worktree at a time with a simple in-place runtime-config override.
