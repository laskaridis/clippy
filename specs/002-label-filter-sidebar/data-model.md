# Data Model: Label-Based Clip Filtering

**Feature**: [specs/002-label-filter-sidebar/spec.md](specs/002-label-filter-sidebar/spec.md)  
**Plan**: [specs/002-label-filter-sidebar/plan.md](specs/002-label-filter-sidebar/plan.md)

This document defines the implementation-aware data model for label-based filtering, responsive filter panel state, and contextual label filters.

---

## Entities

### Clip

Represents a saved clipping owned by one user.

Key fields:
- `id` (UUID primary key)
- `user_id` (owner reference)
- `title`
- `url`
- `domain`
- `raw_content`
- `normalized_text`
- `notes` (nullable)
- `created_at`
- `updated_at`

Relationships:
- Many-to-one to `User`
- Many-to-many to `Label` through `ClipLabel`

Validation and invariants:
- Clip must belong to exactly one user.
- `domain` is derived from `url`.
- Clip-label relations must keep ownership alignment (`clip.user_id == label.user_id`).

---

### Label

Represents a user-owned categorization value for clips.

Key fields:
- `id` (int primary key)
- `uuid` (stable external identifier, currently used in existing links)
- `user_id` (owner reference)
- `name`
- `slug` (new canonical URL identifier for filter query strings)
- `description` (nullable)
- `color` (nullable)

Relationships:
- Many-to-one to `User`
- Many-to-many to `Clip` through `ClipLabel`

Validation and invariants:
- `(user_id, name)` must stay unique.
- `(user_id, slug)` must be unique after introducing slug support.
- `slug` must be URL-safe lowercase text.
- Slug lookup and filtering must always be user-scoped.

---

### ClipLabel

Join entity linking `Clip` and `Label`.

Key fields:
- `clip_id`
- `label_id`

Validation and invariants:
- `(clip_id, label_id)` unique constraint.
- Ownership guard: clip and label must belong to same user.

---

### LabelFilterState (Derived Request State)

Represents active selected labels from query string.

Key fields:
- `selected_label_slugs: list[str]` (from repeated `label` parameters)
- `resolved_label_ids: list[int]` (user-owned labels resolved from slugs)
- `ignored_label_slugs: list[str]` (unknown/invalid/unavailable slugs)
- `has_active_labels: bool`

Validation and invariants:
- Input normalization: trim, lowercase, dedupe while preserving first-seen order.
- Unknown slugs are ignored gracefully and must not fail page rendering.
- Effective clip filtering uses AND semantics across `resolved_label_ids`.

State transitions:
- Add label: append slug if not already selected.
- Remove label: remove only that slug.
- Clear all: remove all label parameters.
- Reload/bookmark: restore selected labels from query string.

---

### FilterPanelState (Derived UI State)

Represents query-string-persisted filter-panel visibility across breakpoints.

Key fields:
- `panel` query parameter value
- Desktop semantic state: `expanded` or `collapsed`
- Small-screen semantic state: `open` or `closed`
- `is_small_screen` (runtime viewport condition at <=1024px)

Validation and invariants:
- Allowed values are constrained to known panel states.
- Invalid `panel` values fall back to default closed/collapsed behavior.
- Panel state changes must not mutate selected labels.

State transitions:
- Desktop toggle: `expanded <-> collapsed`
- Small-screen toggle: `open <-> closed`
- Drawer dismiss (backdrop/Escape/Close): state becomes `closed` while preserving label filters.

---

### WebLabelFilterItem (Derived View Model)

Represents each label row rendered in the clips sidebar/drawer.

Key fields:
- `label_id`
- `label_name`
- `label_slug`
- `label_color` (nullable)
- `contextual_results_count`

Validation and invariants:
- Selection/order/visibility are owned by web/UI state.
- Search filtering is case-insensitive on label name and executed client-side.

---

### ApiLabelCatalogItem (API DTO)

Represents each label entry returned by `/api/labels`.

Key fields:
- `name`
- `slug`
- `color` (nullable)

Validation and invariants:
- Selection-agnostic: no selected-state fields.
- Count-agnostic: no clip-count or contextual-count fields.
- Ordered deterministically by label name.

---

## Query and Count Semantics

- Clip result set for selected labels uses AND semantics.
- Contextual counts are computed only for web filter rendering.
- `/api/labels` does not return counts.
- Empty states:
  - No matching labels in search: show no-match labels state.
  - No clips for active filters: show no-results state while preserving selected labels/pills.

---

## Data Changes and Migration Notes

- Add `slug` to `Label` and backfill existing records.
- Add uniqueness constraint for `(user_id, slug)`.
- Preserve existing UUID field for compatibility while migrating links and filters to slugs.
