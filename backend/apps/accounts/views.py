from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import FormView


class SignInView(LoginView):
    template_name = "accounts/pages/login.html"
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


class SignUpView(FormView):
    template_name = "accounts/pages/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        user: User = form.save(commit=False)
        # Treat username as email for this app and require activation.
        user.email = form.cleaned_data.get("username")
        user.is_active = False
        user.save()

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = self.request.build_absolute_uri(
            reverse("accounts:activate", kwargs={"uidb64": uid, "token": token})
        )

        context = {
            "user": user,
            "activation_link": activation_link,
            "site_name": "Clippy",
        }

        subject = "Confirm your Clippy account"
        message = (
            f"Hi {user.username},\n\n"
            f"Thanks for signing up to Clippy.\n\n"
            f"Please confirm your email by visiting this link:\n{activation_link}\n\n"
            f"If you didn’t request this, you can safely ignore this email."
        )

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
        send_mail(subject, message, from_email, [user.email])

        return super().form_valid(form)


class ActivateAccountView(View):
    template_name = "accounts/pages/activation-complete.html"

    def get(self, request, uidb64, token):  # pragma: no cover - simple flow
        user = None
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
        except Exception:
            user = None

        success = False
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            success = True

        return render(request, self.template_name, {"success": success})


class ClippyPasswordResetView(PasswordResetView):
    template_name = "accounts/pages/password-reset-form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class ClippyPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/pages/password-reset-done.html"


class ClippyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/pages/password-reset-confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class ClippyPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/pages/password-reset-complete.html"
