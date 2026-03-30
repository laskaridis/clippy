# 0005: Use Hotwire Stimulus for web component behavior

- Status: Accepted
- Date: 2026-03-30

## Context

The project needs one consistent model for implementing dynamic web component behavior. Without a shared behavioral contract, JavaScript tends to drift into ad-hoc DOM manipulation, implicit coupling between components, and interfaces that are harder for humans and coding agents to understand safely.

The desired front-end architecture is modular, explicit, and intention-revealing, with clear separation between presentation, styling, and behavior.

## Decision

Adopt Hotwire Stimulus as the required approach for dynamic behavior in web components across the project.

Specifically:

1. Dynamic behavior is implemented through Stimulus controllers.
2. Component behavior stays scoped to the component root and its explicit Stimulus targets, values, actions, and outlets.
3. Cross-component coordination happens through explicit interfaces such as custom events, outlets, or page-level orchestration code, not direct controller-to-controller reach-in.
4. HTML, CSS, and JavaScript responsibilities remain separated:
   - templates define structure
   - CSS defines presentation
   - Stimulus defines behavior

## Consequences

### Positive

- Dynamic behavior follows one predictable, modular pattern across the codebase.
- Component boundaries and interfaces become more explicit and easier to reason about.
- Coding agents can work more safely by relying on consistent conventions for state, events, and DOM ownership.

### Negative

- Existing non-Stimulus dynamic code should be migrated over time to align with the standard.
- Team discipline is required to avoid bypassing Stimulus with ad-hoc DOM scripting.

### Neutral

- This decision complements the existing component and BEM-based styling conventions rather than replacing them.
