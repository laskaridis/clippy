"""Template filters for clips list query-string URL composition.

Purpose:
- Keep URL mutation rules out of templates while still enabling dynamic
  label-filter links from server-rendered HTML.
- Reuse canonical query behavior from `apps.clips.filtering` so template links
  match backend/JS filter-state semantics.
"""

from django import template

from apps.clips.filtering import add_label_query


register = template.Library()


@register.filter(name="label_filter_query")
def label_filter_query(query_params, label_slug: str) -> str:
    """Return the next query string when adding a label filter from templates.

    Intended template usage:
    `{{ request.GET|label_filter_query:label.slug }}`

    The returned query preserves existing non-label params (for example panel
    state or other filter groups) and appends the target label in canonical
    form.
    """
    return add_label_query(query_params=query_params, label_slug=label_slug)
