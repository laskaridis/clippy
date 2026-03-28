from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import resolve, reverse

from apps.clips.models import Label


class LabelHtmlViewsTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="other@example.com",
            password="password123",
        )

    def test_labels_management_url_routing(self) -> None:
        match = resolve("/clips/labels/")
        from apps.clips.views import LabelManagementView

        self.assertIs(match.func.view_class, LabelManagementView)

    def test_list_shows_only_current_user_labels(self) -> None:
        Label.objects.create(user=self.user, name="research")
        Label.objects.create(user=self.user, name="work")
        Label.objects.create(user=self.other_user, name="other")

        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:labels"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clips/pages/labels.html")
        labels = list(response.context["labels"])
        self.assertEqual(len(labels), 2)
        self.assertTrue(all(label.user == self.user for label in labels))

    def test_owner_can_create_label_via_post(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("clips_web:labels"),
            {
                "action": "create",
                "name": "research",
                "description": "Notes",
                "color": "#ffffff",
            },
        )

        self.assertEqual(response.status_code, 302)
        label = Label.objects.get(user=self.user, name="research")
        self.assertEqual(label.description, "Notes")
        self.assertEqual(label.color, "#ffffff")

    def test_labels_page_renders_csrf_tokens_for_post_forms(self) -> None:
        Label.objects.create(user=self.user, name="research")

        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:labels"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csrfmiddlewaretoken"', html=False)

    def test_owner_can_create_label_via_post_with_csrf_enforced_client(self) -> None:
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        csrf_client.get(reverse("clips_web:labels"))
        csrf_token = csrf_client.cookies["csrftoken"].value

        response = csrf_client.post(
            reverse("clips_web:labels"),
            {
                "csrfmiddlewaretoken": csrf_token,
                "action": "create",
                "name": "research",
                "description": "Notes",
                "color": "#ffffff",
            },
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 302)
        label = Label.objects.get(user=self.user, name="research")
        self.assertEqual(label.description, "Notes")
        self.assertEqual(label.color, "#ffffff")

    def test_owner_can_update_label_via_post(self) -> None:
        label = Label.objects.create(user=self.user, name="research", description="Old")

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("clips_web:labels"),
            {
                "action": "update",
                "id": str(label.id),
                "name": "work",
                "description": "New",
                "color": "#000000",
            },
        )

        self.assertEqual(response.status_code, 302)
        label.refresh_from_db()
        self.assertEqual(label.name, "work")
        self.assertEqual(label.description, "New")
        self.assertEqual(label.color, "#000000")

    def test_owner_can_delete_label_via_post(self) -> None:
        label = Label.objects.create(user=self.user, name="research")

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("clips_web:labels"),
            {
                "action": "delete",
                "id": str(label.id),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Label.objects.filter(id=label.id).exists())

    def test_other_user_cannot_modify_label(self) -> None:
        label = Label.objects.create(user=self.user, name="research")

        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse("clips_web:labels"),
            {
                "action": "update",
                "id": str(label.id),
                "name": "hijack",
            },
        )

        self.assertEqual(response.status_code, 404)
        label.refresh_from_db()
        self.assertEqual(label.name, "research")
