from django.urls import path

from apps.clips.views import ClipDetailView, ClipListView, LabelManagementView


app_name = "clips_web"


urlpatterns = [
    path("", ClipListView.as_view(), name="list"),
    path("labels/", LabelManagementView.as_view(), name="labels"),
    path("<uuid:pk>/", ClipDetailView.as_view(), name="detail"),
]
