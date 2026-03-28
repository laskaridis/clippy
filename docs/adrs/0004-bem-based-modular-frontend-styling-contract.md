# 0004: Follow BEM for styling the front end components

- Status: Accepted
- Date: 2026-03-27

## Context

The modular front-end specification (`docs/plans/modular-front-end/spec.md`) defines the long-term architecture for the Django-rendered backend UI. The project needs stable and explicit standards that keep styling, behavior, and component boundaries deterministic as the codebase evolves.

Without a strict styling and ownership contract, frontend work can regress into selector coupling, hidden dependencies, and brittle cross-component interactions.

## Decision

Adopt BEM as the required styling model for backend front-end components, with explicit contracts across templates, CSS, and JavaScript.

Specifically:

1. Styling uses explicit BEM class contracts.
   - Block: `.block-name`
   - Element: `.block-name__element-name`
   - Block modifier: `.block-name--modifier-name`
   - Element modifier: `.block-name__element-name--modifier-name`
   - Every styled component root exposes one stable block class.
   - Modifier classes are always used together with their base block/element class.

2. CSS selector coupling is prohibited for component styling.
   - Do not rely on tag selectors, ids, or DOM hierarchy.
   - Do not style via `[data-component="..."]` selectors.
   - Nesting may organize rules, but selectors remain explicit BEM class names.
   - `&` may reference complete selectors (for example `&.block--compact`) but must not construct class names (`&__...`, `&--...`).

3. JavaScript and CSS ownership are intentionally separated.
   - `data-*` attributes are stable JavaScript hooks.
   - JavaScript queries use `data-*` hooks, not CSS classes.
   - `data-component` defines JS ownership, not CSS styling scope.
   - Component JS enhances only DOM within its own component root.

4. Components follow a naming and file-triplet contract.
   - Component base names are kebab-case and intent-revealing.
   - Related files share the same base name:
     - `templates/.../components/<component-name>.html`
     - `static/.../js/components/<component-name>.js` (optional)
     - `static/.../css/components/<component-name>.css` (optional)
   - Page orchestration belongs in `static/.../js/pages/<page-name>.js`.

5. Template composition and explicit input contracts are required.
   - Use `{% extends %}` only for page/layout inheritance.
   - Use `{% include %}` for components.
   - Component headers document inputs/actions and BEM block/elements/modifiers.
   - Include call sites pass explicit context using `with`.

6. Bootstrap/Optics primitives are preferred before introducing custom BEM blocks.
   - New custom blocks are added only when existing primitives are insufficient.

7. Scope for this decision.
   - Applies to all backend web front-end components and pages, including new work and modifications to existing UI.
   - Does not change the extension stack.

## Consequences

### Positive

- Styling and behavior contracts become explicit and consistent across components.
- Front-end changes gain higher determinism and lower regression risk.
- JS/CSS responsibility boundaries are clear, reducing accidental coupling.
- Reviews and automation can validate concrete acceptance criteria.

### Negative

- Some changes may require additional up-front effort to align existing markup/classes with the standard.
- Temporary compatibility aliases may be needed when replacing legacy class contracts.
- Team discipline is required to keep JS hooks and styling contracts separated.

### Neutral

- Tech stack remains unchanged (Django templates, Bootstrap CSS, vanilla JavaScript).
- Directory roots stay unchanged; modular structure is introduced inside existing roots.
