from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, TemplateView

from apps.clips.filtering import (
    clear_label_filters_query,
    parse_label_slugs,
    remove_label_query,
)
from apps.clips.models import Clip, Label
from apps.clips.services import (
    apply_label_and_filter,
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
        context["selected_label_metadata"] = [
            {"id": label.id, "name": label.name, "slug": label.slug}
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
        return context


class ClipDetailView(LoginRequiredMixin, DetailView):
    model = Clip
    template_name = "clips/detail.html"
    context_object_name = "clip"

    def get_queryset(self):
        return (
            Clip.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("labels")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clip: Clip = context["clip"]
        label_names = list(clip.labels.order_by("name").values_list("name", flat=True))
        context["labels_text"] = ", ".join(label_names)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        raw_labels = request.POST.get("labels", "")
        names = [name.strip() for name in raw_labels.split(",") if name.strip()]

        labels = []
        for name in names:
            label, _ = Label.objects.get_or_create(user=request.user, name=name)
            labels.append(label)

        # Setting the labels list replaces any previous associations; an empty
        # POST payload clears all labels for the clip.
        self.object.labels.set(labels)

        return redirect("clips_web:detail", pk=self.object.pk)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(status=204)


class LabelManagementView(LoginRequiredMixin, TemplateView):
    template_name = "clips/labels.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        labels = (
            Label.objects.filter(user=self.request.user)
            .prefetch_related("clips")
            .order_by("name")
        )
        context["labels"] = labels
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "create":
            name = (request.POST.get("name") or "").strip()
            description = (request.POST.get("description") or "").strip() or None
            color = (request.POST.get("color") or "").strip() or None

            if name:
                Label.objects.get_or_create(
                    user=request.user,
                    name=name,
                    defaults={"description": description, "color": color},
                )

            return redirect("clips_web:labels")

        label_id = request.POST.get("id")
        label = get_object_or_404(Label, id=label_id, user=request.user)

        if action == "update":
            name = (request.POST.get("name") or "").strip()
            description = (request.POST.get("description") or "").strip() or None
            color = (request.POST.get("color") or "").strip() or None

            if name:
                label.name = name
            label.description = description
            label.color = color
            label.save()
        elif action == "delete":
            label.delete()

        return redirect("clips_web:labels")
