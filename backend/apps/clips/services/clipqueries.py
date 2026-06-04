from __future__ import annotations

from typing import TypedDict

from django.http import QueryDict

from apps.clips.filtering import parse_label_slugs
from apps.clips.models import Clip, Label
from apps.clips.services.searchfilters import (
    apply_label_and_filter,
    resolve_selected_labels,
)


class ClipFilterState(TypedDict):
    active_url_filter: str
    selected_label_slugs: list[str]
    selected_labels: list[Label]


def build_clip_filter_state(*, user, query_params: QueryDict) -> ClipFilterState:
    selected_label_slugs = parse_label_slugs(query_params.getlist("label"))
    selected_labels = resolve_selected_labels(
        user=user,
        selected_label_slugs=selected_label_slugs,
    )
    return {
        "active_url_filter": query_params.get("url") or "",
        "selected_label_slugs": [label.slug for label in selected_labels],
        "selected_labels": selected_labels,
    }


def build_filtered_clips_queryset(*, user, query_params: QueryDict):
    filter_state = build_clip_filter_state(user=user, query_params=query_params)
    queryset = _clips_queryset_for_user(user=user)
    queryset = apply_label_and_filter(
        queryset=queryset,
        labels=filter_state["selected_labels"],
    )
    if filter_state["active_url_filter"]:
        queryset = queryset.filter(url=filter_state["active_url_filter"])
    return queryset


def _clips_queryset_for_user(*, user):
    return (
        Clip.objects.filter(user=user)
        .select_related("user")
        .prefetch_related("labels")
    )
