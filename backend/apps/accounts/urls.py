from django.urls import path

from apps.accounts.views import (
    SignInView,
    SignOutView,
    SignUpView,
    ActivateAccountView,
    ClippyPasswordResetView,
    ClippyPasswordResetDoneView,
    ClippyPasswordResetConfirmView,
    ClippyPasswordResetCompleteView,
)


app_name = "accounts"


urlpatterns = [
    path("login/", SignInView.as_view(), name="login"),
    path("logout/", SignOutView.as_view(), name="logout"),
    path("register/", SignUpView.as_view(), name="register"),
    path(
        "activate/<str:uidb64>/<str:token>/",
        ActivateAccountView.as_view(),
        name="activate",
    ),
    path("password-reset/", ClippyPasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        ClippyPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        ClippyPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        ClippyPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
