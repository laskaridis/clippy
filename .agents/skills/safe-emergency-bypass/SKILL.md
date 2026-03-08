---
name: safe-emergency-bypass
description: Use a controlled, auditable emergency bypass path with mandatory reason logging and follow-up remediation steps.
---

# Safe Emergency Bypass

Use only for urgent incidents when normal workflow gates would delay mitigation.

## Workflow

Run `<path-to-skill>/scripts/bypass.sh --reason "..." --ticket <reference>`.

This does not commit automatically. It logs the bypass request and prints constrained next commands.
