"""Shared label-filter query utilities for clips list URL state.

Intent and purpose:
- Centralize label-related query-string behavior used by both Django views and
  template links.
- Keep add/remove/clear operations consistent so UI actions produce predictable,
  shareable URLs.
- Preserve non-label parameters (for example panel state or future filter
  groups) while mutating label selections.

Design decisions:
- Label values are normalized (trimmed, lowercased, deduplicated) before use to
  keep URL state canonical and stable across repeated interactions.
- Query building is funneled through a single helper (`_build_query`) to avoid
  drift between add/remove/clear paths.
- The module only operates on query-string shape; ownership/access checks and
  filtering semantics remain in service/view layers.

Key assumptions:
- Multi-select labels are represented as repeated `label` query parameters.
- Parameter order matters for UX consistency, so first-seen label order is
  preserved after normalization.
- Non-label query params may represent active or future filter groups and must
  not be dropped when label filters change.
"""

from __future__ import annotations

from urllib.parse import urlencode

from django.http import QueryDict


def parse_label_slugs(values: list[str]) -> list[str]:
    """Return canonical label slugs for query processing.

    Use this when reading label values from URLs or user input to ensure
    downstream filtering logic receives stable tokens:
    - trimmed
    - lowercase
    - de-duplicated while preserving first-seen order
    """
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        value = (raw_value or "").strip().lower()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def add_label_query(*, query_params: QueryDict, label_slug: str) -> str:
    """Build the next query string after adding one label selection.

    Existing non-label query parameters are preserved unchanged. Label values
    are normalized and deduplicated via ``parse_label_slugs``.
    """
    selected_slugs = parse_label_slugs([*query_params.getlist("label"), label_slug])
    return _build_query(
        query_params=query_params,
        selected_label_slugs=selected_slugs,
    )


def remove_label_query(*, query_params: QueryDict, label_slug: str) -> str:
    """Build the next query string after removing one selected label.

    If the target label is not currently selected, the returned query is
    effectively unchanged (except for normalization). Non-label parameters are
    always preserved.
    """
    normalized_slug = (label_slug or "").strip().lower()
    selected_slugs = [
        slug
        for slug in parse_label_slugs(query_params.getlist("label"))
        if slug != normalized_slug
    ]
    return _build_query(
        query_params=query_params,
        selected_label_slugs=selected_slugs,
    )


def clear_label_filters_query(*, query_params: QueryDict) -> str:
    """Build the next query string with all label filters removed.

    This keeps every non-label query parameter so other filter groups or UI
    state (for example panel state) remain intact after clearing labels.
    """
    return _build_query(query_params=query_params, selected_label_slugs=[])


def clear_url_filter_query(*, query_params: QueryDict) -> str:
    """Build the next query string with the URL filter removed.

    Preserve every other query parameter (including label selections and panel
    state) so users can clear just the URL constraint without losing the rest
    of their current filtering context.
    """
    pairs: list[tuple[str, str]] = []
    for key, values in query_params.lists():
        if key == "url":
            continue
        for value in values:
            pairs.append((key, value))
    if not pairs:
        return ""
    return f"?{urlencode(pairs)}"


def _build_query(*, query_params: QueryDict, selected_label_slugs: list[str]) -> str:
    """Compose a query string from preserved params plus selected labels.

    Intended as the single query-construction path for label add/remove/clear
    operations so behavior stays consistent across server-rendered links and
    JavaScript URL mutations.
    """
    pairs: list[tuple[str, str]] = []
    for key, values in query_params.lists():
        if key == "label":
            continue
        for value in values:
            pairs.append((key, value))
    for slug in selected_label_slugs:
        pairs.append(("label", slug))
    if not pairs:
        return ""
    return f"?{urlencode(pairs)}"
