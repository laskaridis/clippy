from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PANEL_STATES = {"expanded", "collapsed", "open", "closed"}


def parse_label_slugs(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        value = (raw_value or "").strip().lower()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def parse_panel_state(raw_value: str | None) -> str:
    value = (raw_value or "").strip().lower()
    if value in PANEL_STATES:
        return value
    return "collapsed"


def replace_label_query_params(url: str, label_slugs: list[str]) -> str:
    parts = urlsplit(url)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    preserved = [(key, value) for key, value in pairs if key != "label"]
    for slug in parse_label_slugs(label_slugs):
        preserved.append(("label", slug))
    query = urlencode(preserved, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
