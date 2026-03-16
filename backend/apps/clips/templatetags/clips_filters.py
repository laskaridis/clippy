from django import template

from apps.clips.filtering import add_label_query


register = template.Library()


@register.filter(name="label_filter_query")
def label_filter_query(query_params, label_slug: str) -> str:
    return add_label_query(query_params=query_params, label_slug=label_slug)
