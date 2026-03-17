from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.clips.filtering import (
    clear_label_filters_query,
    clear_url_filter_query,
    parse_label_slugs,
    remove_label_query,
)
from apps.clips.models import Clip
from apps.clips.services import (
    apply_label_and_filter,
    build_web_label_filters_dataset,
    resolve_selected_labels,
)

PANEL_STATES = {"expanded", "collapsed", "open", "closed"}


def _parse_panel_state(raw_value: str | None) -> str:
    value = (raw_value or "").strip().lower()
    if value in PANEL_STATES:
        return value
    return "collapsed"


class ClipListView(LoginRequiredMixin, ListView):
    model = Clip
    template_name = "clips/list.html"
    context_object_name = "clips"

    def get_queryset(self):
        queryset = (
            Clip.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("labels")
        )
        selected_label_slugs = parse_label_slugs(self.request.GET.getlist("label"))
        selected_labels = resolve_selected_labels(
            user=self.request.user, selected_label_slugs=selected_label_slugs
        )
        queryset = apply_label_and_filter(queryset=queryset, labels=selected_labels)

        url_filter = self.request.GET.get("url")
        if url_filter:
            queryset = queryset.filter(url=url_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_label_slugs = parse_label_slugs(self.request.GET.getlist("label"))
        selected_labels = resolve_selected_labels(
            user=self.request.user, selected_label_slugs=selected_label_slugs
        )
        context["active_url_filter"] = self.request.GET.get("url") or ""
        context["selected_label_slugs"] = [label.slug for label in selected_labels]
        context["selected_labels"] = selected_labels
        context["selected_labels_count"] = len(selected_labels)
        context["current_query_params"] = self.request.GET
        context["clear_label_filters_query"] = clear_label_filters_query(
            query_params=self.request.GET
        )
        context["clear_url_filter_query"] = clear_url_filter_query(
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
