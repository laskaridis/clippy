## Goal

Replace the current bind-mounted /workspace model with a per-sandbox Docker
named volume populated by cloning the repo inside the container. The sandbox
always starts from master; the coding agent then creates or switches to its
feature branch inside the isolated clone. The host checkout is used only to
launch the devcontainer and provide config, not as the live workspace.

## Interface Changes

- Add required sandbox inputs:
    - SANDBOX_REPO_URL: HTTPS Git URL for the repo to clone.
    - GIT_AUTH_TOKEN: token used for clone, fetch, and push inside the sandbox.
    - SANDBOX_ID: unique sandbox identifier used as the Compose project name and
      volume prefix.
- Add a host-side preflight script, invoked from devcontainer.json initializeCommand, that:
    - verifies the host tree is clean,
    - verifies SANDBOX_REPO_URL, GIT_AUTH_TOKEN, and SANDBOX_ID are set,
    - writes resolved values into an env file consumed by Compose.

## Assumptions

- Devcontainer-first only; other sandbox entrypoints are out of scope for this pass.
- HTTPS token auth is the only supported Git auth mode in v1.
- The sandbox always initializes from remote master; feature branch selection is
  handled later by the coding agent inside the container.
- The repo must be clonable from a remote URL; this repo currently has no
  configured remote, so adoption requires supplying SANDBOX_REPO_URL.
- Local uncommitted host changes are never imported into the sandbox.
