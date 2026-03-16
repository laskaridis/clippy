from __future__ import annotations

from urllib.parse import urlencode

from django.http import QueryDict


def parse_label_slugs(values: list[str]) -> list[str]:
    """Normalize incoming label query values into unique, stable slug tokens."""
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
    selected_slugs = parse_label_slugs([*query_params.getlist("label"), label_slug])
    return _build_query(
        query_params=query_params,
        selected_label_slugs=selected_slugs,
    )


def remove_label_query(*, query_params: QueryDict, label_slug: str) -> str:
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
    return _build_query(query_params=query_params, selected_label_slugs=[])


def _build_query(*, query_params: QueryDict, selected_label_slugs: list[str]) -> str:
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
