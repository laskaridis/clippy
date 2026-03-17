# Feature Specification: Label-Based Clip Filtering

**Feature Branch**: `002-label-filter-sidebar`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "Enable users to filter clips by label with multi-select, querystring persistence, accessible collapsible sidebar, searchable and expandable label lists with counts, and removable selected-label pills above results."

## Clarifications

### Session 2026-03-14

- Q: When a user selects multiple labels, how should clip matching work? -> A: Show clips only when they contain all selected labels (AND logic).
- Q: How should selected labels be represented in bookmarkable URLs? -> A: Use label slugs in the query string.
- Q: What query-string format should be used for multiple selected labels? -> A: Use repeated label parameters (e.g., ?label=work&label=research).
- Q: How should label counts behave when filters are active? -> A: Show contextual counts that update based on active filters (faceted behavior).
- Q: How should the sidebar collapse state persist across reloads? -> A: Persist collapse state in the query string.
- Requirement update: The filter UX MUST render cleanly and remain fully usable in small-screen real estate, including mobile and tablet viewports.
- Requirement update: On small-screen viewports, render filters in an off-canvas drawer opened from a Filters trigger above results so results remain full-width.
- Q: What breakpoint should switch to the small-screen drawer pattern? -> A: Use off-canvas drawer for viewport widths 1024px and below.
- Q: On small screens, after toggling a label in the drawer, should it stay open or close? -> A: Keep the drawer open and apply filter changes immediately.
- Q: How should the small-screen filter drawer be dismissed? -> A: Allow dismissal via backdrop tap, Escape key, or explicit Close action.
- Q: How should long label names render in the drawer list and selected pills? -> A: Truncate both drawer labels and selected pills to a single line with ellipsis.
- Q: Where should users get a Clear all action for selected labels? -> A: Show Clear all above result pills and inside the small-screen drawer header.
- Q: Should label-name search be handled by backend API filtering? -> A: No. Search is UI-only against the label dataset loaded at page render.
- Q: Should `/api/labels` be aware of selected labels? -> A: No. Selection state is web/UI-owned.
- Q: Should `/api/labels` expose counts? -> A: No. `/api/labels` returns only flat label catalog data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter Clips By Labels (Priority: P1)

As a user browsing my saved clips, I want to select one or more labels so I can quickly narrow results to clips relevant to the topic I care about.

**Why this priority**: Filtering results is the core user value. Without this, the feature does not solve the primary discovery problem.

**Independent Test**: Can be fully tested by selecting and de-selecting label filters and confirming that only clips matching the selected labels are shown.

**Acceptance Scenarios**:

1. **Given** a user sees an unfiltered clip list, **When** they select one label, **Then** only clips tagged with that label are shown.
2. **Given** a user has selected multiple labels, **When** results are refreshed, **Then** only clips tagged with all selected labels are shown.
3. **Given** a user has selected labels, **When** they de-select all of them, **Then** the full unfiltered clip list is shown.

---

### User Story 2 - Preserve And Manage Filter State (Priority: P2)

As a user, I want selected labels reflected in the page URL and displayed as removable pills above results so I can share or bookmark filtered views and remove filters quickly.

**Why this priority**: Persistence and quick removal materially improve day-to-day usability and support repeat workflows.

**Independent Test**: Can be tested by applying labels, copying/reloading the URL, and removing labels via either pills or sidebar controls.

**Acceptance Scenarios**:

1. **Given** a user applies label filters, **When** the page URL is inspected, **Then** the selected labels are represented in the query string.
2. **Given** a user opens a bookmarked filtered URL, **When** the page loads, **Then** the corresponding labels are pre-selected and the filtered results are shown.
3. **Given** selected-label pills are visible above results, **When** a user clicks the remove action on a pill, **Then** that label is de-selected, results update, and the query string updates.
4. **Given** one or more labels are selected, **When** a user activates Clear all from above result pills or from the small-screen drawer header, **Then** all selected labels are removed, results reset to unfiltered, and label query-string parameters are removed.

---

### User Story 3 - Navigate Large Label Sets Efficiently (Priority: P3)

As a user with many labels, I want a searchable, collapsible filter sidebar that prioritizes selected labels and lets me expand long lists so I can find and apply labels quickly without clutter.

**Why this priority**: This improves speed and clarity for larger datasets and protects future extensibility of the sidebar.

**Independent Test**: Can be tested by using search, show more, and collapse/expand interactions while verifying list ordering and accessibility behavior.

**Acceptance Scenarios**:

1. **Given** a user has more labels than the default visible limit, **When** the sidebar first loads, **Then** only the default number is shown with a "Show more" control.
2. **Given** a user has selected labels, **When** the label list is shown, **Then** selected labels appear first and remaining labels appear in alphabetical order.
3. **Given** a user types in the label search input, **When** the query changes, **Then** the label list updates to matching labels while preserving selected-label priority.
4. **Given** the sidebar is expanded, **When** the user collapses it, **Then** it collapses to the left and can be expanded again without losing selected filters.
5. **Given** a user changes filter-panel visibility, **When** the URL is inspected or shared and reloaded, **Then** the same panel visibility state is restored from the query string.
6. **Given** a user is on a small-screen viewport, **When** they use sidebar and pill interactions, **Then** all filter actions remain available and the layout stays clear without clipped or overlapping controls.
7. **Given** a user is on a viewport that is 1024px wide or less, **When** the page loads, **Then** the results area remains full-width and filters are accessed from an off-canvas drawer opened by a Filters trigger above results.
8. **Given** a user opens then closes the small-screen filter drawer, **When** no label selections change, **Then** the result set remains unchanged and focus returns to the Filters trigger.
9. **Given** a user is using the small-screen filter drawer, **When** they select or de-select a label, **Then** results and URL state update immediately while the drawer remains open until the user dismisses it.
10. **Given** a user is on a small-screen viewport, **When** they dismiss the filter drawer via backdrop tap, Escape key, or explicit Close action, **Then** the drawer closes, filter state is preserved, and focus returns to the Filters trigger.
11. **Given** label names are longer than available space, **When** labels are shown in the small-screen drawer list or as selected pills, **Then** each label is displayed on one line with ellipsis while remaining selectable/removable.
12. **Given** a non-label filter-group query parameter is active, **When** a user adds, removes, or clears label filters, **Then** non-label filter-group parameters remain intact and results update consistently.

---

### Scope Boundaries

- In scope: label-based filtering, multi-select behavior, URL persistence, sidebar interactions, selected-label pills, responsive rendering across desktop/mobile/tablet viewports, and accessibility compliance for this flow.
- Out of scope: creating or editing labels, introducing new non-label filter types, and changing clip content beyond filter-driven visibility.

### Edge Cases

- No labels exist for the user: the sidebar shows an empty-label state and clips remain visible unless filters are active from the URL.
- A URL includes labels that do not exist or are no longer accessible: unknown labels are ignored and do not block page load.
- Selected labels exceed the default visible limit: all selected labels remain visible at the top even before using "Show more".
- No labels match the search term: show a clear "no matching labels" state while preserving current selections.
- A selected label has zero matching clips due to other active constraints: selected state remains visible and the result area shows a clear empty-results message.
- On small screens, long label names or many selected pills must not hide essential actions; controls remain readable and operable.
- On small screens, the off-canvas drawer must be fully reachable by keyboard and must not trap focus after close.
- On small screens, backdrop dismiss must not cause unintended filter selection changes.
- Keyboard-only users must be able to expand/collapse the sidebar, search labels, select/de-select labels, and remove pills without requiring a pointer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a filter sidebar on the left side of the clips page.
- **FR-002**: The sidebar MUST be collapsible to the left and expandable again without clearing active filters.
- **FR-021**: The filter-panel visibility state MUST be persisted in the query string and restored on page load (collapsed/expanded sidebar on larger viewports and closed/open drawer on small viewports).
- **FR-003**: The sidebar MUST present labels as a dedicated filter group that can coexist with additional filter groups without changing label-filter behavior.
- **FR-004**: The label filter group MUST allow users to select one or more labels simultaneously.
- **FR-005**: When one or more labels are selected, the system MUST show only clips tagged with all selected labels.
- **FR-006**: When no labels are selected, the system MUST show the unfiltered clip result set.
- **FR-007**: Selected label filters MUST be encoded in the query string using canonical label slugs via repeated label parameters so filtered views are bookmarkable and shareable.
- **FR-008**: On page load, the system MUST read repeated label parameters from the query string and apply corresponding label filters automatically.
- **FR-009**: The label list in the sidebar MUST display selected labels first.
- **FR-010**: Labels that are not selected MUST be displayed in ascending alphabetical order by label name.
- **FR-011**: Each label in the sidebar MUST display a contextual clip count that updates as active filters change.
- **FR-012**: The sidebar MUST show only a default fixed number of labels initially and provide a "Show more" control to reveal additional labels.
- **FR-013**: The sidebar MUST provide a label search input directly above the label list.
- **FR-014**: As users type in the search input, the label list MUST update client-side to labels whose names match the entered text.
- **FR-015**: Selected labels MUST be displayed above the results area as removable pills.
- **FR-016**: Users MUST be able to remove a selected label by either de-selecting it in the sidebar or using the remove action on its pill.
- **FR-017**: Any label selection or de-selection action MUST update results, filter-panel state, pills, and query string consistently.
- **FR-022**: When users open or close the filter panel, the system MUST update query-string panel state consistently without mutating selected label filters.
- **FR-018**: The feature MUST satisfy all applicable requirements in the project's accessibility policy for this interaction flow, including keyboard operation, visible focus indicators, and screen-reader friendly control names and states for sidebar toggle, label controls, search input, and pill removal actions.
- **FR-019**: If query-string label slug values are invalid or unavailable, the system MUST ignore them gracefully and continue rendering available filters and results.
- **FR-020**: The system MUST provide clear empty states for both "no matching labels" and "no clips match current filters" conditions.
- **FR-023**: On viewport widths of 1024px and below, the filter UI MUST render cleanly without clipped or overlapping filter controls.
- **FR-024**: On viewport widths of 1024px and below, users MUST be able to perform all filter actions (open/close the filter drawer, search labels, show more labels, select/de-select labels, remove selected-label pills, and activate Clear all) without horizontal page scrolling.
- **FR-025**: On small screens, label rows and selected-label pills MUST remain understandable and operable when labels are long or selections are many.
- **FR-026**: On viewport widths of 1024px and below, filter controls MUST render in an off-canvas drawer rather than a persistent left sidebar.
- **FR-027**: On small screens, the filter drawer MUST be opened via a visible Filters trigger above results.
- **FR-028**: The Filters trigger on small screens MUST display the current number of selected labels.
- **FR-029**: Opening or closing the small-screen filter drawer MUST NOT change selected labels or filtered results.
- **FR-030**: For keyboard and assistive technology users, opening the small-screen filter drawer MUST move focus into the drawer, and closing it MUST return focus to the Filters trigger.
- **FR-031**: On viewport widths of 1024px and below, label selection changes made inside the filter drawer MUST apply immediately and MUST NOT auto-close the drawer.
- **FR-032**: On viewport widths of 1024px and below, the filter drawer MUST be dismissible via backdrop tap, Escape key, and an explicit Close action.
- **FR-033**: Label names in the small-screen drawer list and selected-label pills MUST render on a single line and truncate with ellipsis when space is insufficient.
- **FR-034**: When a label name is visually truncated, the full label text MUST remain available to assistive technologies.
- **FR-035**: When one or more labels are selected, the UI MUST expose a Clear all action above selected-label pills in the results area.
- **FR-036**: On viewport widths of 1024px and below, when one or more labels are selected, the small-screen drawer header MUST expose a Clear all action.
- **FR-037**: Activating Clear all MUST remove all selected labels, update results and URL query-string label parameters consistently, and MUST NOT auto-close the small-screen drawer.
- **FR-038**: `/api/labels` MUST return a complete, selection-agnostic flat label catalog for the current user with `name`, `slug`, and `color`.
- **FR-039**: `/api/labels` MUST ignore legacy query parameters (`label`, `limit`, `expanded`) and return the same complete flat label catalog.

### Accessibility Verification Checklist

- **A11Y-001**: Keyboard users can open/close the drawer, toggle labels, remove pills, and activate Clear all without pointer input.
- **A11Y-002**: Focus moves into the drawer on open and returns to the Filters trigger on close.
- **A11Y-003**: Sidebar toggle, drawer controls, label controls, and pill remove actions expose accessible names and state.
- **A11Y-004**: All interactive controls have visible focus indicators.
- **A11Y-005**: Truncated labels and selected pills preserve full label text for assistive technologies.
- **A11Y-006**: At viewport widths of 1024px and below, core filtering actions do not require horizontal scrolling.

### Assumptions

- Multi-label filtering within the label group uses AND matching: a clip is shown only if it has all selected labels.
- The initial visible label limit is 10 before users choose "Show more".
- Label search matching is case-insensitive and based on label name text in the client-rendered label dataset.
- Label counts are faceted/contextual and reflect the currently active filter state.
- Label counts are a web filtering concern and are not part of `/api/labels`.
- Query-string persistence uses canonical label slugs rather than display names.
- Multiple selected labels in the URL use repeated label parameters rather than comma-separated or JSON-encoded values.
- Filter-panel visibility state is encoded in the query string and survives reload/share flows.
- On small screens, filters use an off-canvas drawer while results remain full-width.
- For this feature, small-screen behavior is defined as viewport widths of 1024px and below.
- On small screens, filter selection changes apply immediately and the drawer stays open until explicitly dismissed.
- On small screens, drawer dismissal supports backdrop tap, Escape key, and explicit Close action.
- Long label names use one-line ellipsis in drawer labels and selected pills.
- Clear all actions are shown only when at least one label is selected.

### Dependencies

- Clips and labels are already associated in a way that supports retrieving labels and clip counts per label.
- Existing query-string handling on the clips page supports adding and reading filter values.
- Existing UI patterns allow adding accessible interactive controls in the sidebar and results header.

### Key Entities *(include if feature involves data)*

- **Clip**: A saved web clipping item shown in results; each clip can have zero or more labels.
- **Label**: A user-visible categorization value applied to clips; includes display name and associated clip count.
- **Label Filter State**: The current set of selected labels represented in both UI controls and query string.
- **Filter Panel State**: The view state of the filter container across breakpoints, including sidebar collapsed/expanded or drawer closed/open state (query-string persisted), and whether the full label list is expanded.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability testing, at least 90% of users can apply one or more label filters and see expected filtered clips in under 10 seconds.
- **SC-002**: In acceptance testing, 100% of tested filtered URLs restore selected labels, filter-panel visibility state, and result set after page reload.
- **SC-003**: In accessibility verification, the feature has zero critical and zero serious violations against the project's accessibility policy for the clips filtering flow.
- **SC-004**: In representative datasets with at least 100 labels, at least 85% of users can find and select a target label using sidebar search in under 8 seconds.
- **SC-005**: In functional QA, 100% of label removal actions (sidebar de-select and pill remove) produce consistent updates across results, pills, and URL state.
- **SC-006**: In responsive QA at viewport widths of 1024px and below, 100% of core filtering flows complete without clipped or overlapping controls.
- **SC-007**: In responsive QA at viewport widths of 1024px and below, 100% of core filtering flows complete without requiring horizontal page scrolling.
- **SC-008**: In responsive accessibility QA at viewport widths of 1024px and below, 100% of small-screen filter drawer open/close flows preserve results state and return keyboard focus to the Filters trigger on close.
- **SC-009**: In responsive QA at viewport widths of 1024px and below, 100% of label selection changes inside the drawer apply immediately without auto-closing the drawer.
- **SC-010**: In responsive QA at viewport widths of 1024px and below, 100% of drawer dismissals via backdrop tap, Escape key, and explicit Close action preserve selected labels and result state.
- **SC-011**: In responsive QA at viewport widths of 1024px and below, 100% of overlength label names in drawer rows and selected pills render as single-line ellipsis without breaking control usability.
- **SC-012**: In functional and responsive QA, 100% of Clear all actions (results area and small-screen drawer header) clear filters and URL label parameters consistently without unexpected drawer closure.
