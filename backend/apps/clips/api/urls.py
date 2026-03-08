from django.http import HttpResponse
from django.urls import path

from apps.clips.api.views import (
    ClipDetailView,
    ClipListCreateView,
    LabelDetailView,
    LabelListCreateView,
    QuickSearchView,
)


def health(request):  # Placeholder; real views will be added in later phases
    return HttpResponse("OK")


app_name = "clips"


urlpatterns = [
    path("health/", health, name="health"),
    path("clips/", ClipListCreateView.as_view(), name="clip-list-create"),
    path("clips/<uuid:pk>/", ClipDetailView.as_view(), name="clip-detail"),
    path("clips/quick-search/", QuickSearchView.as_view(), name="clip-quick-search"),
    path("labels/", LabelListCreateView.as_view(), name="label-list-create"),
    path("labels/<int:pk>/", LabelDetailView.as_view(), name="label-detail"),
]
