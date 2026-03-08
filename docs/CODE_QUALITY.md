# Code Quality Guidelines

- Make small, focused changes.
- Preserve current language style:
  - Python: clear class/function boundaries, meaningful names, simple control flow.
  - Extension TS: write TypeScript source and keep emitted JavaScript build output compatible with the Chrome runtime.
- Keep user-facing error messages actionable.
- Remove dead code introduced during refactors.
- Do not introduce new dependencies without strong justification.

## General principles
- Emphasize writing clean, easily maintainable code.
- Apply SOLID and KISS principles.
- Bias heavily towards high cohesion and low coupling.

## Code clarity
- Use intention revealing names for variables, functions, classes, etc.
- **ALLWAYS** document your code:
- In your comments communicate intent and purpose, not simply to describe what the code does.
- **ALLWAYS** ask: if this code breaks at 1am in production, would somebody looking at it for the first time
  be able to quickly understand it to fix it? If the answer is no - refactor.
- Make sure any that pre-conditions, invariants and side-effects are crealry visible to the reader, preferrably
  in code and secondarily via comments.
- Prefer functional programing paradigm if possible for clarity.

## Code safety
- Prefer immutability.
- Use optionals when possible instead of NULL values.
- For non-statically typed languages use type hints as much as possible

## Scripting
- Allways use color coding for messages (green=ok, yellow=warn, red=error)
- Allways include documentation to explain purpose and intendent usage and expected outcomes.
- Modularise script files to improve clarity and maintainability (i.e. avoid monolithic scripts)

## Tooling

### Backend (`backend/`)
- **Lint**: `ruff`
- **Format**: `black`
- **Type check**: `mypy`
- Config is in `backend/pyproject.toml`.

### Extension (`extension/`)
- **Lint**: `eslint` (`eslint.config.mjs`)
- **Format**: `prettier`
- **Type check**: `typescript` (`tsc --noEmit`)
- Config and ignores live in:
  - `extension/eslint.config.mjs`
  - `extension/.prettierignore`
  - `extension/chrome/tsconfig.json`

## Commands

Run repository-wide checks from repo root:

```bash
./scripts/lint.sh
./scripts/format.sh
./scripts/typecheck.sh
```

Run module-specific checks:

```bash
# backend
cd backend
pip install -r requirements-dev.txt
python -m ruff check .
python -m black --check .
python -m mypy .

# extension
cd extension
pnpm install --frozen-lockfile
pnpm run lint
pnpm run format:check
pnpm run typecheck
```

## Auto-fix and formatting

Use these commands to apply fixes:

```bash
# backend
cd backend
python -m black .
python -m ruff check --fix .

# extension
cd extension
pnpm run lint:fix
pnpm run format
```

The git pre-commit hook runs branch policy checks plus fast, staged-file formatting/linting for backend Python and extension TypeScript files.
