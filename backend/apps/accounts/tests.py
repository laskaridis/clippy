from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from unittest.mock import patch

from apps.accounts.bootstrap import ensure_admin_user_from_env
from django.contrib.auth.tokens import default_token_generator


class AccountsAuthTests(TestCase):
    def test_login_page_renders(self) -> None:
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/pages/login.html")

    def test_home_navbar_is_not_forced_to_dark_theme(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertNotContains(response, "navbar-dark", html=False)
        self.assertContains(response, 'id="themeToggle"', html=False)
        self.assertContains(
            response, 'src="/static/js/theme-controller.js"', html=False
        )
        self.assertContains(
            response, 'data-controller="global-theme-toggle"', html=False
        )
        self.assertContains(
            response,
            'data-action="click->global-theme-toggle#toggle"',
            html=False,
        )
        self.assertContains(
            response,
            'type="module" src="/static/js/application.js"',
            html=False,
        )
        self.assertNotContains(response, "window.localStorage.setItem(", html=False)

    def test_home_page_uses_auth_and_anon_primary_ctas(self) -> None:
        anonymous_response = self.client.get(reverse("home"))
        self.assertEqual(anonymous_response.status_code, 200)
        self.assertContains(anonymous_response, "Sign in to start clipping")
        self.assertNotContains(anonymous_response, "Go to my clips")

        User = get_user_model()
        user = User.objects.create_user(
            email="cta-user@example.com",
            username="cta-user@example.com",
            password="password123",
        )
        self.client.force_login(user)
        authenticated_response = self.client.get(reverse("home"))
        self.assertEqual(authenticated_response.status_code, 200)
        self.assertContains(authenticated_response, "Go to my clips")
        self.assertNotContains(authenticated_response, "Sign in to start clipping")

    def test_register_page_renders_modular_template(self) -> None:
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/pages/register.html")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="test-no-reply@clippy.local",
    )
    def test_register_creates_inactive_user_and_sends_activation_email(self) -> None:
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "signup-user@example.com",
                "password1": "RefactorTestPassword123!",
                "password2": "RefactorTestPassword123!",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        user = get_user_model().objects.get(username="signup-user@example.com")
        self.assertEqual(user.email, "signup-user@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["signup-user@example.com"])
        self.assertEqual(mail.outbox[0].from_email, "test-no-reply@clippy.local")
        self.assertIn("Confirm your Clippy account", mail.outbox[0].subject)
        self.assertIn("/accounts/activate/", mail.outbox[0].body)

    def test_password_reset_pages_render_modular_templates(self) -> None:
        reset_form_response = self.client.get(reverse("accounts:password_reset"))
        self.assertEqual(reset_form_response.status_code, 200)
        self.assertTemplateUsed(
            reset_form_response, "accounts/pages/password-reset-form.html"
        )

        reset_done_response = self.client.get(reverse("accounts:password_reset_done"))
        self.assertEqual(reset_done_response.status_code, 200)
        self.assertTemplateUsed(
            reset_done_response, "accounts/pages/password-reset-done.html"
        )

        reset_complete_response = self.client.get(
            reverse("accounts:password_reset_complete")
        )
        self.assertEqual(reset_complete_response.status_code, 200)
        self.assertTemplateUsed(
            reset_complete_response, "accounts/pages/password-reset-complete.html"
        )

    def test_password_reset_confirm_page_renders_modular_template(self) -> None:
        User = get_user_model()
        user = User.objects.create_user(
            email="reset-user@example.com",
            username="reset-user@example.com",
            password="password123",
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": uid, "token": token},
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/pages/password-reset-confirm.html")

    def test_activation_page_renders_modular_template(self) -> None:
        User = get_user_model()
        user = User.objects.create_user(
            email="activation-user@example.com",
            username="activation-user@example.com",
            password="password123",
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.get(
            reverse("accounts:activate", kwargs={"uidb64": uid, "token": token})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/pages/activation-complete.html")

    def test_activation_marks_user_active_with_valid_token(self) -> None:
        user = get_user_model().objects.create_user(
            email="activation-success@example.com",
            username="activation-success@example.com",
            password="password123",
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.get(
            reverse("accounts:activate", kwargs={"uidb64": uid, "token": token})
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertContains(response, "Your account is active")

    def test_successful_login_redirects_to_clips(self) -> None:
        User = get_user_model()
        user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="password123",
        )

        response = self.client.post(
            "/accounts/login/",
            {"username": "user@example.com", "password": "password123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/clips/"))

        # After login, a subsequent request to /clips/ should succeed.
        response = self.client.get("/clips/")
        self.assertEqual(response.status_code, 200)

    def test_logout_via_get_clears_session(self) -> None:
        User = get_user_model()
        user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="password123",
        )

        # Log in first.
        self.client.login(username="user@example.com", password="password123")
        response = self.client.get("/clips/")
        self.assertEqual(response.status_code, 200)

        # Now hit logout via GET and ensure we are redirected.
        response = self.client.get("/accounts/logout/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

        # After logout, accessing /clips/ should redirect to login.
        response = self.client.get("/clips/", follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])


class EnsureAdminUserBootstrapTests(TestCase):
    def test_ensure_admin_user_creates_default_admin(self) -> None:
        User = get_user_model()

        self.assertFalse(User.objects.filter(username="admin").exists())
        result = ensure_admin_user_from_env()

        self.assertEqual(result, "created:admin")
        admin_user = User.objects.get(username="admin")
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.check_password("admin"))

    def test_ensure_admin_user_honors_env_overrides(self) -> None:
        User = get_user_model()

        with patch.dict(
            "os.environ",
            {
                "DJANGO_ADMIN_USERNAME": "root-admin",
                "DJANGO_ADMIN_EMAIL": "root@example.com",
                "DJANGO_ADMIN_PASSWORD": "secret123",
            },
            clear=False,
        ):
            result = ensure_admin_user_from_env()

        self.assertEqual(result, "created:root-admin")
        admin_user = User.objects.get(username="root-admin")
        self.assertEqual(admin_user.email, "root@example.com")
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.check_password("secret123"))

    def test_ensure_admin_user_updates_existing_user(self) -> None:
        user = get_user_model().objects.create_user(
            username="admin",
            email="old-admin@example.com",
            password="password123",
            is_staff=False,
            is_superuser=False,
        )

        with patch.dict(
            "os.environ",
            {"DJANGO_ADMIN_EMAIL": "new-admin@example.com"},
            clear=False,
        ):
            result = ensure_admin_user_from_env()

        self.assertEqual(result, "updated:admin")
        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.email, "new-admin@example.com")

    def test_ensure_admin_user_returns_exists_for_matching_admin(self) -> None:
        get_user_model().objects.create_superuser(
            username="admin",
            email="admin@clippy.local",
            password="password123",
        )

        result = ensure_admin_user_from_env()

        self.assertEqual(result, "exists:admin")

    def test_ensure_admin_user_skips_in_production_environment(self) -> None:
        User = get_user_model()

        with patch.dict("os.environ", {"DJANGO_ENV": "production"}, clear=False):
            result = ensure_admin_user_from_env()

        self.assertEqual(result, "skipped:production")
        self.assertFalse(User.objects.filter(username="admin").exists())

    def test_ensure_admin_user_skips_when_environment_is_production(self) -> None:
        User = get_user_model()

        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            result = ensure_admin_user_from_env()

        self.assertEqual(result, "skipped:production")
        self.assertFalse(User.objects.filter(username="admin").exists())

    def test_ensure_admin_user_skips_if_either_production_marker_is_set(self) -> None:
        User = get_user_model()

        with patch.dict(
            "os.environ",
            {"DJANGO_ENV": "development", "ENVIRONMENT": "production"},
            clear=False,
        ):
            result = ensure_admin_user_from_env()

        self.assertEqual(result, "skipped:production")
        self.assertFalse(User.objects.filter(username="admin").exists())
