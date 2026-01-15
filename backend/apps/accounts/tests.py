from django.contrib.auth import get_user_model
from django.test import TestCase


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
