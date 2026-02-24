# Code Quality Guidelines

- Make small, focused changes.
- Keep code readable and explicit; avoid clever shortcuts.
- Preserve current language style:
  - Python: clear class/function boundaries, meaningful names, simple control flow.
  - Extension TS: write TypeScript source and keep emitted JavaScript build output compatible with the Chrome runtime.
- Keep user-facing error messages actionable.
- Remove dead code introduced during refactors.
- Do not introduce new dependencies without strong justification.
