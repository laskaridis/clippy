from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import DetailView, ListView

from apps.clips.models import Clip


class ClipListView(LoginRequiredMixin, ListView):
    model = Clip
    template_name = "clips/list.html"
    context_object_name = "clips"

    def get_queryset(self):
        return (
            Clip.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("labels")
        )


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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(status=204)
