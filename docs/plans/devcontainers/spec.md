# Isolated Devcontainer Workspace Clones

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [docs/PLANS.md](docs/PLANS.md).

## Purpose / Big Picture

The repository already completed the first devcontainer-first simplification: local development now happens inside the `dev-sandbox` container, the backend is started explicitly with `make backend-run`, and the old host-side runtime bootstrap layer is gone. That work still leaves one important coupling in place: the running container sees the host checkout directly through a bind-mounted `/workspace`.

This follow-on change replaces that live bind mount with a per-sandbox Docker named volume that holds its own clone of the repository. After this change, the host checkout exists only to provide `.devcontainer/` metadata, docs, and launch context for Dev Containers tooling. The running sandbox works against its own cloned repository inside `/workspace`, starts from `origin/master`, and uses a token-backed Git helper for clone, fetch, and push. The observable outcome is that editing a file on the host no longer changes `/workspace` in a running sandbox, while reopening the same `SANDBOX_ID` reuses the same in-volume clone and branch state.

## Progress

- [x] (2026-05-01 19:05Z) Audited the repository surfaces tied to the original host-side worktree runtime model.
- [x] (2026-05-01 19:25Z) Authored the first devcontainer-first ExecPlan at `docs/plans/devcontainers/spec.md`.
- [x] (2026-05-02 12:18Z) Completed the first migration from host runtime bootstrap scripts to the bind-mounted `dev-sandbox` workflow, including Makefile cleanup, backend and extension runtime simplification, and doc updates.
- [x] (2026-05-02 09:27Z) Recorded the automated verification pass for the bind-mounted devcontainer model: `make help`, `make backend-test-unit`, `make backend-test-e2e`, `make extension-test-unit`, `make extension-test-e2e`, `make extension-test-a11y`, and `make all-verify`.
- [x] (2026-05-02 09:37Z) Recorded the manual two-worktree smoke check for the bind-mounted devcontainer model with ports `8794` and `8795`.
- [ ] Add the host-side preflight flow that rejects dirty host trees, requires `SANDBOX_REPO_URL`, `GIT_AUTH_TOKEN`, and `SANDBOX_ID`, and generates `.devcontainer/.env` including `COMPOSE_PROJECT_NAME=${SANDBOX_ID}`.
- [ ] Replace the live `/workspace` bind mount with a per-sandbox named volume and add first-start clone logic that creates a local `master` branch tracking `origin/master`.
- [ ] Add token-backed Git auth inside the sandbox for clone, fetch, and push without persisting the token to `.git/config` or remote URLs.
- [ ] Update living docs, quickstarts, and the architecture record to describe the isolated-clone sandbox workflow instead of the bind-mounted workflow.
- [ ] Run the isolated-clone validation flow and record evidence for first clone, same-`SANDBOX_ID` reopen, parallel sandboxes, host-change isolation, and in-sandbox Git operations.

## Surprises & Discoveries

- Observation: the current devcontainer workflow is already simplified operationally, but source isolation is still incomplete because `/workspace` is a live host bind mount.
  Evidence: `.devcontainer/docker-compose.yml` currently mounts `..:/workspace`.

- Observation: the repository now has a configured `origin` remote, but the isolated sandbox design still needs an explicit repo URL input.
  Evidence: as of 2026-05-03, `git remote -v` reports `origin https://github.com/laskaridis/clippy.git` for fetch and push in this worktree.

- Observation: reusing a sandbox clone across restarts matters because the coding agent is expected to create or switch branches inside the sandbox after startup.
  Evidence: the requested workflow always starts from remote `master`, then hands feature-branch selection to the coding agent inside the isolated clone.

- Observation: the new source-isolation requirement shifts the critical contract from “unique `DJANGO_DEV_PORT` per worktree” to “stable `SANDBOX_ID` per sandbox plus unique backend ports when two sandboxes run live backends at once”.
  Evidence: the named-volume workspace and compose project identity are now derived from `SANDBOX_ID`, while host-browser verification still uses `DJANGO_DEV_PORT`.

## Decision Log

- Decision: preserve the earlier devcontainer-first runtime simplification as completed historical context, but treat the bind-mounted `/workspace` model as superseded by this follow-on plan.
  Rationale: the first migration removed the old runtime-management layer successfully, but it did not satisfy the new source-isolation requirement.
  Date/Author: 2026-05-03 / Codex

- Decision: require `SANDBOX_REPO_URL`, `GIT_AUTH_TOKEN`, and `SANDBOX_ID` as host-provided sandbox inputs.
  Rationale: sandbox startup must not depend on host git metadata, SSH agent state, or implicit defaults when creating the isolated clone.
  Date/Author: 2026-05-03 / Codex

- Decision: generate `COMPOSE_PROJECT_NAME` from `SANDBOX_ID` inside the preflight-generated `.devcontainer/.env`.
  Rationale: Dev Containers and Compose need a deterministic project identity so the workspace volume and related resources stay isolated per sandbox.
  Date/Author: 2026-05-03 / Codex

- Decision: reuse the workspace volume when the same `SANDBOX_ID` is opened again.
  Rationale: the coding agent needs branch and working-tree continuity across restarts for a given sandbox instead of being forced back to a fresh clone every time.
  Date/Author: 2026-05-03 / Codex

- Decision: the first checkout inside a new workspace volume must always be `origin/master` materialized as a local `master` branch.
  Rationale: the requested v1 contract is that every sandbox starts from remote `master`, and feature branch selection happens only after the clone exists.
  Date/Author: 2026-05-03 / Codex

- Decision: `GIT_AUTH_TOKEN` may exist only in ignored `.devcontainer/.env` and ephemeral helper logic inside the container; it must never be written to `.git/config`, remote URLs, or tracked files.
  Rationale: HTTPS token auth is the required v1 mode, but the token should not be persisted into repository metadata that can leak through later inspection or commits.
  Date/Author: 2026-05-03 / Codex

- Decision: keep `dev-sandbox` as an idle development sandbox and keep `make backend-run` as the explicit backend start command inside the cloned workspace.
  Rationale: the source-isolation change does not alter the runtime-process contract established by the first migration.
  Date/Author: 2026-05-03 / Codex

## Outcomes & Retrospective

The previous phase of work achieved its intended outcome for the bind-mounted devcontainer model: the repository has one clear local runtime story, the legacy bootstrap layer is gone, and the existing validation evidence is recorded in this file. That work should remain visible here because the isolated-clone plan builds on it rather than replacing it with an unrelated workflow.

That said, the old plan now overstates completion if read as the current target state. The repository is not finished with sandbox isolation while `.devcontainer/docker-compose.yml` still bind-mounts the host checkout into `/workspace`. This follow-on plan reopens the ExecPlan with a narrower goal: preserve the successful runtime simplification, but move source isolation into a named Docker volume populated by an in-container clone.

## Context and Orientation

There are now four distinct concerns that must not be confused.

First, git worktrees under `.worktrees/` are still useful on the host for branch hygiene, task isolation, and launch context. They remain the place where developers keep local planning documents, open Dev Containers, and manage repository-level workflow helpers.

Second, `.devcontainer/` in the host checkout is still the entrypoint for sandbox startup. Files there define the devcontainer image, Compose services, initialization hooks, and example environment contract. In the new design, `.devcontainer/` belongs to the launcher side of the system, not the live workspace side.

Third, `/workspace` inside a running `dev-sandbox` is no longer supposed to be the host checkout. It becomes the isolated cloned repository stored in a named Docker volume. The coding agent works there, runs `make backend-run` there, switches branches there, and verifies code from there.

Fourth, the backend and extension runtime contract from the first migration still stands unless this plan changes it explicitly. The `dev-sandbox` container stays idle after startup. PostgreSQL still lives on the Compose network. The backend remains host-visible through `DJANGO_DEV_PORT`. The extension still loads from `extension/chrome` and uses runtime config plus localhost-friendly host permissions.

The key files for this follow-on change are:

- `.devcontainer/devcontainer.json`: the Dev Containers launch contract, including `initializeCommand`, service selection, and post-create bootstrap.
- `.devcontainer/.env.example`: the tracked source of example/default values that the preflight script uses to build `.devcontainer/.env`.
- `.devcontainer/docker-compose.yml`: the Compose definition that must stop bind-mounting the host checkout and instead mount a named workspace volume.
- `.devcontainer/Dockerfile`: the image definition that must include any clone/bootstrap helper needed before the sandbox goes idle.
- `.devcontainer/scripts/preflight.sh`: the new host-side script that validates the launch contract and writes `.devcontainer/.env`.
- `.devcontainer/scripts/init-workspace.sh`: the new in-container script that clones on first start and reuses the clone on reopen.

## Plan of Work

Start on the host side by introducing a preflight script and wiring it into `devcontainer.json` through `initializeCommand`. That script must fail if the host tree is dirty, fail if `SANDBOX_REPO_URL`, `GIT_AUTH_TOKEN`, or `SANDBOX_ID` are missing, and generate `.devcontainer/.env` from `.devcontainer/.env.example` plus the required sandbox values. The generated file must include `COMPOSE_PROJECT_NAME=${SANDBOX_ID}` so Compose resources stay isolated per sandbox.

Next, replace the Compose workspace mount. `.devcontainer/docker-compose.yml` must stop mounting `..:/workspace` and instead attach a named volume at `/workspace`. The actual Docker volume identity should come from the Compose project name generated by preflight, so reopening the same sandbox reattaches the same workspace volume while a different `SANDBOX_ID` gets a distinct volume.

Then, add the in-container workspace initialization flow. The image should contain a script that runs before `sleep infinity`. When `/workspace/.git` is absent, the script must clone `SANDBOX_REPO_URL`, materialize local `master` from `origin/master`, and write a small metadata marker recording `SANDBOX_ID` and `SANDBOX_REPO_URL`. When `/workspace/.git` is present, the script must reuse the existing clone and fail fast if the metadata does not match the current sandbox request.

After the clone exists, the existing bootstrap model should continue to work: `postCreateCommand` runs inside `/workspace`, `make backend-init` and `make extension-init` prepare dependencies, and later `make backend-run` starts Django only when requested. The Git token must be available for clone, fetch, and push, but only through ignored env and ephemeral helper behavior.

Finally, update docs and validation artifacts. The core docs must stop telling users to hand-create `.devcontainer/.env`, stop implying that the host checkout is the live workspace, and explain the split between launcher-side host files and cloned in-container workspace files. The ExecPlan must then record the validation evidence for first clone, reopen behavior, parallel sandbox isolation, host-change isolation, and in-sandbox Git operations.

## Concrete Steps

Perform the work from the repository root unless a step explicitly says otherwise.

1. Confirm the current launcher-side contract and the remaining bind mount:

       sed -n '1,200p' .devcontainer/devcontainer.json
       sed -n '1,220p' .devcontainer/docker-compose.yml
       git remote -v

2. Add the host preflight flow and verify it before touching Compose:

       SANDBOX_REPO_URL=https://github.com/laskaridis/clippy.git \
       GIT_AUTH_TOKEN=test-token \
       SANDBOX_ID=devcontainer-smoke \
       bash .devcontainer/scripts/preflight.sh

   Expected result: `.devcontainer/.env` is written, includes `COMPOSE_PROJECT_NAME=devcontainer-smoke`, and preserves the existing Django/Postgres values from `.env.example`.

3. Remove the bind mount, add the named volume plus in-container workspace initialization, and start the devcontainer through Dev Containers tooling.

   Expected result: the first startup creates the workspace volume, clones the repo into `/workspace`, and leaves the sandbox attached to a local `master` branch tracking `origin/master`.

4. Reopen the same `SANDBOX_ID` and verify reuse behavior.

   Expected result: the existing clone is reused without recloning, and in-volume branch state remains intact.

5. Start two distinct sandboxes with different `SANDBOX_ID` values and different backend ports when both live backends must run at once.

   Expected result: each sandbox gets its own Compose project and workspace volume, while `make backend-run` inside each sandbox still publishes its backend through the configured `DJANGO_DEV_PORT`.

6. Validate host/source isolation and in-sandbox Git operations.

   Expected result: editing a host file after startup does not change the corresponding file inside `/workspace`, and `git fetch` plus `git push` from inside the sandbox use the token-backed helper without storing the token in `.git/config`.

## Validation and Acceptance

The change is accepted only when the repository has both runtime isolation and source isolation under the devcontainer-first model.

For preflight acceptance, `.devcontainer/scripts/preflight.sh` must reject a dirty host tree and reject missing `SANDBOX_REPO_URL`, `GIT_AUTH_TOKEN`, or `SANDBOX_ID`. A successful run must write `.devcontainer/.env` with `SANDBOX_REPO_URL`, `GIT_AUTH_TOKEN`, `SANDBOX_ID`, and `COMPOSE_PROJECT_NAME=${SANDBOX_ID}` plus the existing Django/Postgres contract values.

For workspace initialization acceptance, the first startup for a new `SANDBOX_ID` must create a named Docker volume, clone the repository into `/workspace`, and materialize local `master` from `origin/master`. Reopening the same `SANDBOX_ID` must reuse that clone rather than recloning it, and a metadata mismatch between the existing volume and the requested sandbox inputs must fail fast.

For source-isolation acceptance, changing a file in the host checkout after the sandbox has started must not change the corresponding file inside `/workspace`. The live workspace inside `dev-sandbox` must be the cloned repository in the named volume, not the host checkout.

For Git-auth acceptance, clone, fetch, and push inside the sandbox must work with `GIT_AUTH_TOKEN` through helper logic that does not persist the token into `.git/config`, tracked files, or remote URLs.

For workflow acceptance, two sandboxes with different `SANDBOX_ID` values must create separate Compose projects and separate named workspace volumes. If both also run live backends, they still require different `DJANGO_DEV_PORT` values for host-browser verification.

For regression acceptance, the explicit backend-start and verification contract from the first migration must remain intact. `make backend-run` inside the sandbox must still be the manual backend start path, and host verification must still work through `http://localhost:<DJANGO_DEV_PORT>/accounts/login/`.

## Idempotence and Recovery

The host preflight step must be safe to rerun. Re-running it with the same inputs should overwrite `.devcontainer/.env` deterministically without editing tracked files. Re-running it with missing inputs must fail before partially generating a misleading env file.

The workspace initialization step must also be idempotent. Reopening the same `SANDBOX_ID` should reuse the existing volume and clone. Starting a different `SANDBOX_ID` should create a separate volume instead of mutating the first one. If the metadata marker shows that an existing workspace volume belongs to a different repo URL or sandbox identity than the current request, startup should fail with an explicit error rather than trying to reconcile incompatible state automatically.

If a partial migration leaves the repository in a mixed state, recovery means restoring the previous coherent launcher-side config or deleting only the affected sandbox volume and recreating it through the supported preflight plus Dev Containers startup path. Do not leave the repo half bind-mounted and half volume-backed.

## Artifacts and Notes

The current repo fact that shaped this plan is worth recording directly.

    $ git remote -v
    origin  https://github.com/laskaridis/clippy.git (fetch)
    origin  https://github.com/laskaridis/clippy.git (push)

That host remote must remain informational only. The sandbox still requires explicit `SANDBOX_REPO_URL` so startup does not silently depend on host git metadata.

The earlier bind-mounted migration remains valid historical context, but it is no longer the finish line for sandbox isolation.

## Interfaces and Dependencies

The stable host-side inputs for this change are `SANDBOX_REPO_URL`, `GIT_AUTH_TOKEN`, and `SANDBOX_ID`. They must be present before Dev Containers startup, and they must feed the generated `.devcontainer/.env`.

The generated `.devcontainer/.env` remains ignored and becomes the concrete Compose input file. It must contain `COMPOSE_PROJECT_NAME=${SANDBOX_ID}` as well as the existing backend and PostgreSQL environment values needed by the sandbox.

In `.devcontainer/docker-compose.yml`, the `dev-sandbox` service must mount a named volume at `/workspace` instead of the host checkout. The service remains the default development sandbox, remains idle after initialization, and continues exposing the backend through `DJANGO_DEV_PORT` when Django is started manually.

In the image and init scripts, the sandbox must create a local `master` branch from `origin/master` on first clone and then reuse the existing clone on later starts for the same `SANDBOX_ID`. The token-backed Git helper must enable clone, fetch, and push without writing credentials into repository config.

The runtime contract established by the earlier migration remains in force unless explicitly changed here: PostgreSQL stays on the Compose network, `make backend-run` remains the explicit Django entrypoint, the extension keeps loading from `extension/chrome`, and host verification continues through `localhost` plus `DJANGO_DEV_PORT`.

Revision note: 2026-05-03. Rewrote the ExecPlan from a completed bind-mounted devcontainer migration into a follow-on plan for isolated sandbox workspace clones because the new requirement is source isolation inside the sandbox, not just runtime simplification.
