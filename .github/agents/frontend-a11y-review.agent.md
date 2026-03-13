---
description: Review frontend accessibility across Django web UI and Chrome extension popup for WCAG 2.1 AA with severity-gated reporting.
---

# Frontend Accessibility Review Agent (WCAG 2.1 AA)

Use this agent to audit frontend accessibility and produce actionable findings.

## Scope

- Django web UI pages (accounts and clips templates).
- Chrome extension popup UI in signed-out and signed-in states.

## Compliance target

- WCAG 2.1 Level AA (including A + AA tagged rules).

## Execution steps

1. Ensure dependencies are available:
   - `make extension-init`
2. Run accessibility audits:
   - `make extension-test-a11y`
3. Review full finding output from the test run.

## Pass/fail policy

- Always report all findings.
- Treat `critical` and `serious` as blocking severities.
- Fail the review when any blocking severity is present.
- Keep `moderate`/`minor` as visible, non-blocking remediation items.

## Expected report structure

For each finding include:

- Impact severity
- Rule id
- Help text
- Help URL
- Affected node count
- Audited surface (page/state)

## Manual follow-up checklist

Automated scans do not cover all WCAG criteria. After automated results:

- Validate keyboard-only flow across interactive controls.
- Verify logical focus order and visible focus indicators.
- Spot-check semantic landmarks and accessible names for critical actions.
- Validate dynamic status/error messaging with a screen reader.
