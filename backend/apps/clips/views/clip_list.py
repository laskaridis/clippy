from functools import cached_property

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.clips.filtering import (
    clear_all_filters_query,
    remove_label_query,
)
from apps.clips.models import Clip
from apps.clips.services import (
    build_clip_filter_state,
    build_filtered_clips_queryset,
    build_web_label_filters_dataset,
)

PANEL_STATES = {"expanded", "collapsed", "open", "closed"}


def _parse_panel_state(raw_value: str | None) -> str:
    value = (raw_value or "").strip().lower()
    if value in PANEL_STATES:
        return value
    return "collapsed"


class ClipListView(LoginRequiredMixin, ListView):
    model = Clip
    template_name = "clips/pages/list.html"
    context_object_name = "clips"

    @cached_property
    def filter_state(self):
        return build_clip_filter_state(
            user=self.request.user,
            query_params=self.request.GET,
        )

    def get_queryset(self):
        return build_filtered_clips_queryset(
            user=self.request.user,
            query_params=self.request.GET,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_labels = self.filter_state["selected_labels"]
        selected_label_slugs = self.filter_state["selected_label_slugs"]
        context["active_url_filter"] = self.filter_state["active_url_filter"]
        context["selected_label_slugs"] = selected_label_slugs
        context["selected_labels"] = selected_labels
        context["selected_labels_count"] = len(selected_labels)
        context["current_query_params"] = self.request.GET
        context["clear_all_filters_query"] = clear_all_filters_query(
            query_params=self.request.GET
        )
        context["selected_label_metadata"] = [
            {
                "id": label.id,
                "name": label.name,
                "slug": label.slug,
                "color": label.color,
            }
            for label in selected_labels
        ]
        context["selected_label_pills"] = [
            {
                "id": label.id,
                "name": label.name,
                "slug": label.slug,
                "remove_query": remove_label_query(
                    query_params=self.request.GET,
                    label_slug=label.slug,
                ),
            }
            for label in selected_labels
        ]
        context["panel_state"] = _parse_panel_state(self.request.GET.get("panel"))
        context["label_filters_dataset"] = build_web_label_filters_dataset(
            user=self.request.user,
            selected_label_slugs=selected_label_slugs,
        )
        return context
