# Security Guidelines

- Keep cross-user access impossible by construction (queryset scoping + constraints + tests).
- `CsrfExemptSessionAuthentication` exists for first-party extension compatibility. Do not expand CSRF exemptions casually.
- New endpoints must require authentication unless a public endpoint is explicitly required.

## Input Validation
- Never trust user input.
- Validate at API boundary.
- Treat clip text as user data; avoid logging raw clip content.

## Security Review Checklist

Before finishing a change, verify:
- Ownership checks are enforced in querysets and object lookups.
- No endpoint leaks cross-user data.
- Session/cookie behavior remains compatible with extension login flow.
- Error handling does not leak sensitive internals.
