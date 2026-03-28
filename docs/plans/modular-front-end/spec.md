# Modular Front End

## Goals

Use a modular, componentized architecture for the web application, with explicit boundaries
so that AI coding agents can work with efficiently and effectively, achieving higher execution
determinism and minimizing errors.

Design goals are to maximize:
- Locality; everything for a component co-located.
- Explicitness; no hidden behavior.
- Small files; agents perform better on bounded context.

## Expected structure

While Django template/static roots remains unchanged, we add component/page structure
inside existing roots which does not require `settings.py` changes.

```
/backend
|-- /webclippings/templates
|   |-- /layouts                           # global layouts
|   `-- /components                        # shared global HTML partials
|       `-- /my-global-component.html      # example
|-- /static
|   |-- /js                                # global javascript
|   |   `-- /components                    # shared global component JS files
|   |       `-- /my-global-component.js    # example
|   `-- /css
|       |-- /tokens.css                    # design tokens (fonts, colors, spacing)
|       |-- /base.css                      # global css
|       `-- /components                    # shared global component CSS files
|           `-- /my-global-component.css   # example
`-- /apps/<application>
    |-- /templates/<application>
    |   |-- /pages                         # app pages (one per route)
    |   |-- /components                    # reusable app-level HTML partials
    |   |   `-- /my-component.html         # example
    |   `-- /layouts                       # app-specific layouts
    `-- /static/<application>
        |-- /js
        |   `-- /components                # one JS file per app component
        |       `-- /my-component.js       # example
        `-- /css
            `-- /components                # one CSS file per app component
                `-- /my-component.css      # example
```

## Guidelines

- Optimize for change locality, not conceptual purity.
- Name components by intent, not style (e.g. user-card, not blue-box)
- One component = one responsibility
- One component = one html template + one javascript file (optional) + one css file (optional)
- Prefer existing Bootstrap/Optics primitives before introducing a new custom block; only add new BEM blocks when no existing primitive fits.
- Component naming conventions:
    - Every component uses a single kebab-case base name `<component-name>`.
    - Related component files MUST use the exact same base name:
      - `templates/.../components/<component-name>.html`
      - `static/.../js/components/<component-name>.js` (if JS is needed)
      - `static/.../css/components/<component-name>.css` (if CSS is needed)
    - DO NOT use generic suffixes like `-controller`, `-utils`, `-actions`, `-helper`.
    - If behavior is page-level orchestration (not a reusable component), place it under a page entrypoint file in `static/.../js/pages/<page-name>.js` and keep component behavior inside component files.
- No inline JS/CSS in templates
- Use `data-` attributes as JS hooks (stable API)
- Keep javascript imperative and local (no global state)
- Document each component:
    ```html
    <!--
    component: user-card
    inputs:
      - user{name, avatar}
      - ...
    hooks:
      - ...
    block: user-card
    elements:
      - user-card__avatar
      - user-card__name
      - ...
    modifiers:
      - user-card--compact
      - user-card__name--muted
      - ...
    -->
    ```

## Use BEM modeling standard

- CSS class contracts MUST use explicit BEM naming:
  - Block: `.block-name`
  - Element: `.block-name__element-name`
  - Block modifier: `.block-name--modifier-name`
  - Element modifier: `.block-name__element-name--modifier-name`
- Class names MUST be semantic and intention-revealing, not appearance-driven (except modifiers such as `--compact`).
- Every styled component root MUST expose one stable block class.
- Modifiers MUST always be used together with their base block/element class.
- CSS selectors MUST NOT rely on tag selectors, ids, or DOM hierarchy for component styling.
- `&` may be used only as a textual reference to full selectors (for example `&.block--modifier`), never to construct class names (`&__...`, `&--...`).
- Nesting is for organization only; selectors must remain explicit BEM class names.

Good:
```css
.clip-card {
  .clip-card__title {
    &.clip-card__title--muted { }
  }

  &.clip-card--compact { }
}
```

Bad:
```css
[data-component="clip-card"] .clip-title { }
.clip-card h3 { }
#clip-title { }
```

## Component composition

1. Template composition:
  - Use `{% extends %}` only for page and layout inheritance.
  - Use `{% include %}` for components.
  - Components do not extend other templates.

2. Component input contract:
  - Each component must document required and optional inputs in its header comment.
  - Include call sites must pass explicit context using `with ... only`.
  - Components must never rely on hidden ambient variables.

3. JavaScript ownership:
  - Component JS only enhances DOM inside its own root using `[data-component="<component-name>"]`.
  - JavaScript DOM queries MUST use `data-*` attributes as stable hooks (specifically `data-action` and `data-role`), not CSS classes.
  - Do this:
    ```js
    const button = document.querySelector('[data-action="toggle"]');
    ```
  - DON'T do this:
    ```js
    const button = document.querySelector('.card__button');
    ```
  - Page-level orchestration logic belongs in `static/.../js/pages/<page-name>.js`.
  - Page entrypoints initialize component modules explicitly.

4. CSS scope:
  - Component CSS is scoped by the component's BEM block class.
  - `data-component` attributes are a JavaScript ownership contract, not a CSS styling contract.
  - Component state styling should use explicit BEM modifiers.
  - Component CSS must not apply global element overrides.

5. Cross-component communication:
  - Prefer DOM events (`CustomEvent`) or URL/query state for coordination.
  - Avoid direct component-to-component imports unless unavoidable.

## Stack

No changes, keep the same tech stack: 
- Templates: Django templates
- Styling: Bootstrap CSS
- JavaScript: vanilla JavaScript

## Acceptance criteria

- Structural compliance:
  - Every migrated component follows the naming triplet:
    - `templates/.../components/<component-name>.html`
    - `static/.../js/components/<component-name>.js` (if JS is needed)
    - `static/.../css/components/<component-name>.css` (if CSS is needed)
  - Migrated page templates live under `templates/.../pages/`.
  - No inline `<script>` or `<style>` in migrated templates.
  - Component styling uses explicit BEM classes (block/element/modifier) instead of selector coupling.
  - CSS selectors for component styling do not rely on `[data-component="..."]`, tag selectors, or ids.
  - Modifier classes always appear with their corresponding base block/element classes.
  - Each styled component root has one canonical BEM block class.

- Behavioral parity:
  - For each migrated route, rendered UI and primary user flows match pre-refactor behavior.
  - Existing interactions keep working (theme toggle, quick search, filters, form submissions).
  - No auth or ownership regressions on clips pages.

- Verification:
  - For each migration batch run:
    - `make backend-test-unit`
    - `make backend-lint`
    - `make backend-typecheck`
  - Before handoff run:
    - `make all-verify`
  - Manual smoke checks per migrated route:
    - Page loads without template errors.
    - Primary action path works.
    - Desktop and mobile layout sanity check passes.
    - Browser console shows no new JavaScript errors.
