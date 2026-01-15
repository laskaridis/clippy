from django.http import HttpResponse
from django.urls import path

from apps.clips.api.views import ClipDetailView, ClipListCreateView


def health(request):  # Placeholder; real views will be added in later phases
    return HttpResponse("OK")


app_name = "clips"


urlpatterns = [
    path("health/", health, name="health"),
    path("clips/", ClipListCreateView.as_view(), name="clip-list-create"),
    path("clips/<uuid:pk>/", ClipDetailView.as_view(), name="clip-detail"),
]
