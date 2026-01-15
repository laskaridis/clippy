from django.urls import path

from apps.clips.views import ClipDetailView, ClipListView


app_name = "clips_web"


urlpatterns = [
    path("", ClipListView.as_view(), name="list"),
    path("<uuid:pk>/", ClipDetailView.as_view(), name="detail"),
]
