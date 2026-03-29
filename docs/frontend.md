# Frontend Development Guidelines

This document defines the default standards coding agents should follow when implementing or refactoring frontend
code in this repository.

## Core Principles

- Never mix html with css and javascript code, keep responsibilities separate.
- Use existing stack primitives first. NEVER introduce new frontend dependencies unless explicitly required.
- Front ends are structured high level in the following core elements:
  - pages
  - layouts
  - components
- Each component model a single cohesive part of the user experience using clear boundaries: one component - one responsibility.
- Consider accessibility as part of the design

## Componentization Guidelines

- Use **intent-revealing** component names in kebab-case (for example `clip-card`):
  - Good example: `data-component="clip-card"`
  - Bad example: `data-component="blue-box"` (name does not reveal component intent)
  - Bad example: `data-component="ClipCard"` (name does not follow kebab-case)
- Name components explicitly in html using `data-component` attribute.
- Components are split in up to 3 files for each different responsibility (html, js, css) each file named
  after the **same** component name:
  - Presentation logic: `templates/.../components/<component-name>.html`
  - Dynamic behaviour: `static/.../js/components/<component-name>.js` (optional)
  - Component styling: `static/.../css/components/<component-name>.css` (optional)
- Avoid generic suffixes like `-controller`, `-utils`, `-helper` in component file names.
- Component html templates are partials included by pages; they NEVER extend other templates.
  - Django page templates may use `{% extends %}` for layout inheritance.
- ALWAYS pass a component's variables in django templates explicitly using `with ... only` instead of relying on outer template scope.
- Components must NEVER rely on hidden ambient django template variables.

## HTML Guidelines

- Use semantic html elements where possible.
- Do not use inline `<script>` or `<style>` in html files.
- Keep markup semantics and accessibility explicit (labels, roles, aria attributes where appropriate).

## JavaScript Guidelines

- NEVER use classes as js hooks.
- Use stable `data-*` js hooks for interfacing with DOM elements from javascript:
  - Use `data-component` js hook on the **component root** element.
  - Use `data-action` js hooks to **trigger behavior** (event handling only).
  - Use `data-role` js hooks to reference a component's **internal** elements (structure only).
  Example:
  ```html
  <!--
  CONTRACTS:
  data-action="add-to-cart"  : requires data-product-id
  data-action="toggle-modal" : requires data-product-id
  data-product-id="1"        : required by add-to-cart and toggle-modal actions
  data-role="product-price-label"
  -->
  <div class="card" data-component="card">
    <span class="card__label" data-role="product-price-label">$99</span>
    <button class="card__delete btn" data-action="add-to-cart" data-product-id="99">Add</button>
    <button class="card__toggle btn" data-action="toggle-modal" data-product-id="99">Preview</button>
  </div>
  ```
  ```javascript
  const card = document.querySelector('[data-component="card"]');
  const label = card.querySelector('[data-role="product-price-label"]'); // structural ref
  const btn = card.querySelector('[data-action="add-to-cart"]');  // event target
  ```
- Use scoped queries within a component root.
- Use intention-revealing names in js hooks, for example: `data-action="delete-clip"`, `data-action="close-clip-preview"`, `data-role="clip-title"`
- Treat js hooks as part of the component's API contract.
- A component's js should interact with the DOM only inside its own root.
- Page-level orchestration belongs in `static/.../js/pages/<page-name>.js`.
- Page entrypoints should initialize component modules explicitly.
- Use idempotent initialization guards for repeat mount paths.
- Prefer explicit coordination mechanisms (events or URL/query state) over tight component coupling.

## CSS Guidelines

- Reserve css classes strictly for styling.
- Use explicit BEM class contracts for styling components:
  - Block: `.block`
  - Element: `.block__element`
  - Modifier: `.block--modifier`, `.block__element--modifier`
- Every styled component root should expose a canonical block class.
- Modifiers should appear with their base block/element class.
- Style via classes, not by `[data-component]`, tag selectors, id selectors, or fragile DOM hierarchy coupling.
- Use nesting for organization only; keep emitted selectors explicit BEM class names.
- Prefer Bootstrap/utilities first; introduce custom block styles only when needed.

## Accessibility Guidelines

- Prefer semantic elements first (`button`, `nav`, `main`, `form`, `label`) before adding ARIA roles.
- Use ARIA only to fill semantic gaps; do not duplicate native semantics with redundant roles/attributes.
- Every interactive element must be keyboard accessible:
  - use native controls where possible
  - do not rely on click-only interactions
  - support `Enter`/`Space` behavior for custom controls when native elements are not possible
- Ensure visible focus states for all interactive controls (`:focus-visible` must be clear and not removed).
- Keep focus management explicit for overlays/dialogs/drawers:
  - move focus into the opened surface
  - restore focus to the trigger on close
  - support `Escape` to close when applicable
- Associate form controls with accessible names:
  - use `<label for>` or equivalent programmatic labeling
  - include clear help/error text and connect it via ARIA when needed
- Provide meaningful text alternatives:
  - `alt` text for informative images
  - `aria-label` only when visible text is not present
- Announce important dynamic UI changes when needed (for example status/error updates) using appropriate live-region patterns.
- Do not convey meaning using color alone; preserve readable contrast and include textual/iconic cues when state changes.
- Verify accessibility in every frontend change:
  - keyboard-only navigation path works
  - focus order is logical
  - controls are discoverable by accessible name
  - no new obvious accessibility regressions in desktop/mobile flows
