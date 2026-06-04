from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from apps.clips.models import Label
from apps.clips.services import normalize_label_name, normalize_optional_text


class LabelManagementView(LoginRequiredMixin, TemplateView):
    template_name = "clips/pages/labels.html"

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
            name = normalize_label_name(request.POST.get("name"))
            description = normalize_optional_text(request.POST.get("description"))
            color = normalize_optional_text(request.POST.get("color"))

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
            name = normalize_label_name(request.POST.get("name"))
            description = normalize_optional_text(request.POST.get("description"))
            color = normalize_optional_text(request.POST.get("color"))

            if name:
                label.name = name
            label.description = description
            label.color = color
            label.save()
        elif action == "delete":
            label.delete()

        return redirect("clips_web:labels")
