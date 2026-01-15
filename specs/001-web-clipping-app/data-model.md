# Data Model: Web Clipping and Reference Application

**Feature**: [specs/001-web-clipping-app/spec.md](specs/001-web-clipping-app/spec.md)  
**Plan**: [specs/001-web-clipping-app/plan.md](specs/001-web-clipping-app/plan.md)

This document captures the conceptual data model for the MVP. It is implementation-aware (e.g., Django + PostgreSQL) but framework-agnostic at the level of behavior and constraints.

---

## Entities

### User

Represents an authenticated person using the system.

**Key fields** (in addition to Django’s standard auth fields):
- `id` (UUID or integer primary key)
- `email` (unique, used for login)
- `date_joined`
- `is_active`

**Relationships**:
- One `User` **owns many** `Clip` records.
- One `User` **owns many** `Label` records.

**Validation / Rules**:
- `email` must be unique per user.
- Deactivating a user should not automatically delete clips; clips remain in storage but become inaccessible via the UI/API.

---

### Clip

Represents a saved piece of text from a webpage.

**Key fields**:
- `id`: Primary key (UUID recommended for API stability).
- `user_id`: Foreign key to `User` (owner).
- `title`: Short text (e.g., page title or user-specified title).
- `url`: Full URL string of the source page.
- `domain`: Normalized domain (e.g., `example.com`) extracted from `url` for grouping and filtering.
- `raw_content`: The exact text as clipped by the user (may contain line breaks and basic formatting).
- `normalized_text`: A normalized version of the content used for search (e.g., lower-cased, stripped of extra whitespace).
- `created_at`: Timestamp when the clipping was created.
- `updated_at`: Timestamp when the clipping was last updated (e.g., if labels or notes change).
- `notes` (optional): User-authored notes for the clipping.

**Relationships**:
- Many-to-one with `User`.
- Many-to-many with `Label` via an association table (e.g., `clip_labels`).

**Validation / Rules**:
- `url` must be a well-formed URL.
- `raw_content` must not be empty.
- `domain` is derived from `url` and should be stored in normalized form.
- A clip must always belong to exactly one user.
- Deleting a user should either cascade-delete their clips or be prevented; for MVP, soft deletion or archival can be considered later.

---

### Label

Represents a user-defined tag used to organize clips.

**Key fields**:
- `id`: Primary key.
- `user_id`: Foreign key to `User` (owner of the label namespace).
- `name`: Short, human-readable label name.
- `description` (optional): Free-text description.
- `color` (optional): Optional color code for UI display.

**Relationships**:
- Many-to-one with `User`.
- Many-to-many with `Clip` via `clip_labels`.

**Validation / Rules**:
- `(user_id, name)` must be unique, preventing two labels with exactly the same name for a single user.
- Labels cannot exist without an owning user.
- Renaming a label preserves existing clip associations.

---

### ClipLabel (join table)

Join table for the many-to-many relationship between `Clip` and `Label`.

**Key fields**:
- `id`: Primary key (or composite key of `clip_id` + `label_id`).
- `clip_id`: Foreign key to `Clip`.
- `label_id`: Foreign key to `Label`.

**Validation / Rules**:
- Each `(clip_id, label_id)` pair must be unique.
- `clip.user_id` must match `label.user_id` (no cross-user associations).

---

## Derived and Supporting Data

### Search Index

For MVP, we can rely on PostgreSQL indexes on the `normalized_text`, `title`, `url`, and `domain` fields:

- B-tree indexes on `user_id`, `created_at`, and `domain` for efficient filtering and sorting.
- Text-search-friendly indexes (e.g., GIN on `to_tsvector(normalized_text)`) can be added later if needed.

### Time and Ordering

- Default ordering for clip lists is `created_at DESC` (most recent first).
- Additional ordering by relevance can be introduced later if full-text search is enhanced.

---

## State Transitions

### Clip Lifecycle

- **Created**: A new clip is created when a user confirms a clipping action in the Chrome extension or web UI.
- **Updated**: A clip can be updated when the user edits notes or labels.
- **Deleted**: When a user deletes a clip, it is removed from active queries and associations. For MVP, hard deletion is acceptable; soft deletion can be added later if needed.

### Label Lifecycle

- **Created**: A label is created explicitly by the user (e.g., in a label management UI) or implicitly when they first assign a new label name to a clip.
- **Renamed/Updated**: A label can be renamed or have its attributes (description, color) updated, preserving existing clip associations.
- **Deleted**: Deleting a label removes it from associated clips but does not delete the clips themselves.

---

## Validation Summary

- All user-facing operations must enforce per-user scoping (no access to other users’ clips or labels).
- Input validation must ensure URLs are valid, text content is non-empty, and labels do not conflict with existing `(user_id, name)` constraints.
- Backend services should normalize domains and text to keep search and grouping behavior predictable.
