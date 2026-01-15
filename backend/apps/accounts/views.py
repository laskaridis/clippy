from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy


class SignInView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # After signing in, send users to their clip list.
        return reverse_lazy("clips_web:list")


class SignOutView(LogoutView):
    next_page = reverse_lazy("accounts:login")
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):  # pragma: no cover - thin wrapper
        """Allow GET requests to log the user out.

        The navigation uses an <a> link to /accounts/logout/, which issues a
        GET; delegate to the POST handler so the session is cleared.
        """
        return self.post(request, *args, **kwargs)
