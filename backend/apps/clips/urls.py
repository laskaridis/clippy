from django.http import HttpResponse
from django.urls import path

def health(request):  # Placeholder; real views will be added in later phases
    return HttpResponse("OK")

app_name = "clips"

urlpatterns = [
    path("health/", health, name="health"),
]
