from django.urls import path

from apps.accounts.views import SignInView, SignOutView


app_name = "accounts"


urlpatterns = [
    path("login/", SignInView.as_view(), name="login"),
    path("logout/", SignOutView.as_view(), name="logout"),
]
