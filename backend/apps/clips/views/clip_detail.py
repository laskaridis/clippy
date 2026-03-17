from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import DetailView

from apps.clips.models import Clip, Label


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
