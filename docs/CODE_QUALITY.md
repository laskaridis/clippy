# Code Quality Guidelines

- Make small, focused changes.
- Keep code readable and explicit; avoid clever shortcuts.
- Preserve current language style:
  - Python: clear class/function boundaries, meaningful names, simple control flow.
  - Extension JS: plain JavaScript compatible with current no-build setup.
- Keep user-facing error messages actionable.
- Remove dead code introduced during refactors.
- Do not introduce new dependencies without strong justification.
