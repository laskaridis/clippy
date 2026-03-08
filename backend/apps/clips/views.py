from uuid import UUID

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, TemplateView

from apps.clips.models import Clip, Label


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
        label_uuid_raw = (self.request.GET.get("label") or "").strip()
        if label_uuid_raw:
            try:
                label_uuid = UUID(label_uuid_raw)
            except ValueError:
                return queryset.none()
            queryset = queryset.filter(labels__uuid=label_uuid).distinct()

        url_filter = self.request.GET.get("url")
        if url_filter:
            queryset = queryset.filter(url=url_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        label_uuid_raw = (self.request.GET.get("label") or "").strip()
        context["active_url_filter"] = self.request.GET.get("url") or ""
        context["active_label_uuid"] = label_uuid_raw
        context["active_label_name"] = ""
        if label_uuid_raw:
            try:
                label_uuid = UUID(label_uuid_raw)
            except ValueError:
                return context
            label = Label.objects.filter(
                user=self.request.user, uuid=label_uuid
            ).first()
            if label is not None:
                context["active_label_name"] = label.name
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
