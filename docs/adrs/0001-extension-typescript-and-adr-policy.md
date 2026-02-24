# 0001: Adopt TypeScript for Chrome extension and ADRs for architecture decisions

- Status: Accepted
- Date: 2026-02-24

## Context

The Chrome extension codebase has been implemented in vanilla JavaScript. As the extension grows, this increases the chance of runtime-only failures (for example: shape mismatches in messages, DOM/chrome API misuse, and weakly typed payloads).

In parallel, the project has lacked a lightweight, durable place to record architecturally significant decisions and their trade-offs over time.

## Decision

1. **Use TypeScript as the source language for the Chrome extension** under `extension/chrome/src`.
   - Source files are `.ts`.
   - TypeScript is compiled to JavaScript output under `extension/chrome/dist` for Chrome runtime consumption.
   - The extension manifest references compiled JavaScript files in `dist/`.
2. **Establish an ADR policy** for architecturally significant decisions.
   - ADRs are stored under `docs/adrs/`.
   - Each ADR follows the standard ADR structure (Context, Decision, Consequences).
   - ADRs are append-only records and should be superseded by new ADRs when decisions evolve.

## Consequences

### Positive

- Earlier detection of extension issues via static analysis and typed editor/tooling support.
- Clearer contracts between extension components (popup/content/background/shared modules).
- A durable decision log that captures architectural intent and trade-offs.

### Negative

- Adds a compile step for extension development and testing.
- Requires maintaining TypeScript/compiler configuration and generated artifacts.
- ADR process adds a small documentation overhead for architectural changes.

### Neutral

- Existing runtime behavior remains JavaScript-based in the packaged extension; TypeScript is a build-time authoring choice.
