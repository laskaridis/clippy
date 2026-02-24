from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch

from apps.accounts.bootstrap import ensure_admin_user_from_env


class AccountsAuthTests(TestCase):
    def test_login_page_renders(self) -> None:
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

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
