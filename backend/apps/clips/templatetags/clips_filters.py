from urllib.parse import urlencode

from django import template

from apps.clips.services import parse_label_slugs


register = template.Library()


@register.filter(name="label_filter_query")
def label_filter_query(selected_label_slugs: list[str], label_slug: str) -> str:
    slugs = parse_label_slugs([*selected_label_slugs, label_slug])
    if not slugs:
        return ""
    query = urlencode([("label", slug) for slug in slugs])
    return f"?{query}"
