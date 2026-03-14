# Quickstart: Label-Based Clip Filtering

**Feature**: [specs/002-label-filter-sidebar/spec.md](specs/002-label-filter-sidebar/spec.md)  
**Plan**: [specs/002-label-filter-sidebar/plan.md](specs/002-label-filter-sidebar/plan.md)

This quickstart describes how to run and validate the label-filter sidebar/drawer behavior end to end.

---

## Prerequisites

- Python 3.12 environment for backend development
- Node 18+ and pnpm (for extension/tooling commands where needed)
- Docker available if local PostgreSQL auto-provisioning is used
- Repository initialized in a compliant feature worktree

---

## 1. Install Dependencies

From repository root:

```bash
make backend-init
make extension-init
```

---

## 2. Start Backend in Current Worktree

Use the canonical worktree-aware backend entrypoint:

```bash
make backend-run
```

Optional status check:

```bash
make backend-status
```

---

## 3. Seed/Prepare User Data for Filtering Flows

Create or ensure:
- At least 1 authenticated user
- At least 15 labels (to exercise Show more)
- Clips with overlapping labels to validate AND semantics
- A few long label names to validate single-line truncation and assistive text

You can use existing admin tools or fixtures in backend tests for deterministic data setup.

---

## 4. Manual Verification Flow

1. Open `/clips/` while authenticated.
2. Select one label and verify only matching clips appear.
3. Select multiple labels and verify clips must contain all selected labels.
4. Confirm URL contains repeated label slugs: `?label=work&label=research`.
5. Reload and verify selected labels, pills, and filtered result set restore correctly.
6. Remove one selected label via its pill and confirm results + URL update.
7. Use Clear all above pills and verify labels are removed and URL label params clear.
8. At desktop width (>1024), collapse and expand sidebar, then verify panel state persists in URL.
9. At 1024px and below, open filters via trigger, verify selected count on trigger, and confirm drawer remains open while toggling labels.
10. Dismiss drawer via backdrop tap, Escape, and Close button; verify filter state remains and focus returns to trigger.
11. Validate long labels and pills render as one line with ellipsis while full text remains available to assistive tech.

---

## 5. Automated Test Execution

Run targeted backend tests while iterating:

```bash
cd backend
python manage.py test apps.clips.tests.test_views apps.clips.tests.test_api apps.clips.tests.test_models
```

Run broader project checks before handoff:

```bash
make all-check
```

---

## 6. Accessibility and Responsive Checks

Minimum checks:
- Keyboard-only navigation for sidebar/drawer toggle, search, label selection, pill removal, and Clear all.
- Visible focus indicators for all interactive controls.
- Screen-reader names/states for filter trigger, drawer, label controls, and pill remove actions.
- No horizontal scrolling or clipped controls at widths <=1024px.
