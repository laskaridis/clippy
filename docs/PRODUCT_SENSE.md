# Product Sense Guidelines

## Target User
Busy knowledge workers saving research snippets quickly.

## Core Value
Speed of capture and retrieval.

## UX Principles
- Minimize clicks.
- Show content before metadata.
- Avoid modal overload.
- Favor inline editing.
- Favour simple, unclutter UX over flexibility.
- Accessibility is a first-class requirement for every new feature.

## Accessibility Baseline
- Every new user-facing flow must be keyboard navigable.
- Use semantic labels/roles so assistive technologies can interpret UI state and actions.
- Do not rely on color alone to communicate status or meaning.
- Validate contrast and focus visibility for all interactive elements.

## Scope Discipline
- No advanced configuration unless >30% of users benefit.
- Avoid adding new entity types without clear ROI.
- Default to flat models unless hierarchy is essential.

## Performance Bias
- Prioritize perceived speed over feature richness.
- Home page must render under 300ms locally.

## Design Tradeoffs
- Prefer convention over configuration.
- Prefer deletion over soft-deletion unless compliance requires otherwise.
