# Frontend Development Guidelines

This document defines the standards coding agents should follow when implementing or refactoring frontend
code in this repository.

## Stack

- `html` for presentation
- `javascript` + `hotwire stimulus` for dynamic behaviour
- `css` for styling relying on BEM naming
- `htmx` for ajax requests

---

## Project Structure
 
This project contains two frontend-enabled sub-modules with different runtime environments:
 
- `backend/` — Django web application. Uses **stimulus** for component's dynamic behaviour.
- `extension/` — Browser extension. Uses **vanilla js** today, with a planned migration to
  Stimulus. HINT: Write vanilla JS in a Stimulus-compatible shape so the migration is mechanical.
 
When working on a task, identify which sub-module is in scope and apply the corresponding
JavaScript guidelines. **Web Component Design Guidelines apply to both sub-modules.**

---

## Web Component Design Guidelines 

These rules apply to both `backend/` and `extension/` modules.

### Core Principles

- Use existing stack primitives first. NEVER introduce new frontend dependencies
  unless explicitly required.
- Each web component models a single cohesive part of the user experience using clear 
  boundaries: one component - one responsibility.
- Use stimulus controllers for all web component's dynamic functionality.
- Never mix html with css and javascript code, keep responsibilities separate.
- A component's javascript must **never** query or manipulate the DOM outside its own root element (i.e. `this.element`).

### Naming

- Use intention-revealing component names in kebab-case.
  - CORRECT: clip-card, add-to-cart-button, filter-panel
  - WRONG: blue-box — name does not reveal intent
  - WRONG: ClipCard — not kebab-case
- Mark every component root element with data-component="<component-name>".
  This attribute is the stable semantic identifier used for readability. It is separate from any JS framework hook (e.g. data-controller).

### File Responsibilities
 
Each component is split into up to 3 files, all named after the **same** component name:
 
| Responsibility     | File                              | Required |
|--------------------|-----------------------------------|----------|
| Presentation       | `<component-name>.html`           | Yes      |
| Dynamic behaviour  | `<component-name>-controller.js`  | Optional |
| Styling            | `<component-name>.css`            | Optional |

### Web Component Coordination
 
- Components coordinate via **custom DOM events** or **URL/query state**.
- NEVER couple two components by having one directly call methods on the other.
- Controllers coordinate via Stimulus **outlets** or custom DOM events dispatched with `this.dispatch(...)`.
- Page-level orchestration (wiring multiple components together) belongs in a dedicated page entrypoint file — not inside any component.

### Example
```html
<article class="clip-card"
         data-component="clip-card"
         data-controller="clip-card"
         data-clip-card-clip-id-value="{{ clip.id }}">
  <h2 class="clip-card__title" data-clip-card-target="title">
    {{ clip.title }}
  </h2>
  <button class="clip-card__save btn"
          data-clip-card-target="saveButton"
          data-action="click->clip-card#save">Save</button>
</article>
```
```javascript
// .../static/js/controllers/clip_card_controller.js

export default class extends Controller {
  static targets = ["title", "saveButton"];
  static values  = { clipId: Number };

  async save() {
    this.saveButtonTarget.disabled = true;
    await saveClip(this.clipIdValue);
    this.saveButtonTarget.disabled = false;
  }
}
```

---

## General HTML Guidelines

- Use semantic html elements where possible.
- Do not use inline `<script>` or `<style>` in html files.
- Consider accessibility as part of the design
- Keep markup semantics and accessibility explicit (labels, roles, aria attributes where appropriate).

--- 

## General CSS Guidelines

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

---

## Module `backend/` Guidelines

These rules apply specifically to `backend/` module.
 
### Template Rules
 
- Component HTML templates are **partials** included by pages — they **never** use `{% extends %}`.
- Django page templates **may** use `{% extends %}` for layout inheritance.
- **ALWAYS** pass a component's variables explicitly using `with ... only`.  Components must **never** rely on ambient variables from the outer template scope.
 
### Stimulus Controller Placement
 
- All controllers live under `static/js/controllers/`.
- One controller per file. No exceptions.
- Never scatter controllers into per-app `static/` directories.
 
### Stimulus Controller Registration
 
- When adding a new controller, **also register it** in `static/js/controllers/index.js`.
 
### Stimulus API Rules - Hooks
 
- **Targets** (`data-{controller}-target`) — elements the controller reads or manipulates.
- **Actions** (`data-action="event->controller#method"`) — all event binding goes through
  Stimulus actions. Never attach events via bare `addEventListener` inside a controller
  when a declarative action descriptor will do.
- **Values** (`data-{controller}-{name}-value`) — pass server-side data from Django
  templates into controllers. Never use inline `<script>` blocks or global JS variables
  for this purpose.
 
### Page-Level Orchestration
 
- Cross-component wiring belongs in `static/js/pages/<page-name>.js`.
- Page entrypoints listen for custom events dispatched by controllers and coordinate responses — they do not reach into controller internals.
- Use idempotent initialization guards for repeat mount paths.
