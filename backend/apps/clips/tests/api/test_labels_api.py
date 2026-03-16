from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.clips.api.views import LabelDetailView, LabelListCreateView
from apps.clips.models import Label


class LabelApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
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

    def _auth_get(self, path: str, user=None):
        request = self.factory.get(path)
        force_authenticate(request, user=user or self.user)
        return request

    def _auth_post(self, path: str, data: dict, user=None):
        request = self.factory.post(path, data, format="json")
        force_authenticate(request, user=user or self.user)
        return request

    def _auth_patch(self, path: str, data: dict, user=None):
        request = self.factory.patch(path, data, format="json")
        force_authenticate(request, user=user or self.user)
        return request

    def _auth_delete(self, path: str, user=None):
        request = self.factory.delete(path)
        force_authenticate(request, user=user or self.user)
        return request

    def test_list_labels_returns_only_current_user_labels(self) -> None:
        Label.objects.create(user=self.user, name="research")
        Label.objects.create(user=self.user, name="personal")
        Label.objects.create(user=self.other_user, name="other-user-label")

        view = LabelListCreateView.as_view()
        request = self._auth_get("/api/labels/")
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        names = {item["name"] for item in response.data}
        self.assertEqual(names, {"research", "personal"})

    def test_create_label_creates_label_for_current_user(self) -> None:
        payload = {
            "name": "research",
            "description": "Research notes",
            "color": "#ff0000",
        }

        view = LabelListCreateView.as_view()
        request = self._auth_post("/api/labels/", payload)
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Label.objects.filter(user=self.user).count(), 1)
        label = Label.objects.get(user=self.user)
        self.assertEqual(label.name, payload["name"])
        self.assertEqual(label.description, payload["description"])
        self.assertEqual(label.color, payload["color"])

    def test_update_label_updates_fields_for_current_user(self) -> None:
        label = Label.objects.create(user=self.user, name="research")

        payload = {
            "name": "updated",
            "description": "Updated description",
            "color": "#00ff00",
        }

        view = LabelDetailView.as_view()
        request = self._auth_patch(f"/api/labels/{label.id}/", payload)
        response = view(request, pk=str(label.id))

        self.assertEqual(response.status_code, 200)
        label.refresh_from_db()
        self.assertEqual(label.name, payload["name"])
        self.assertEqual(label.description, payload["description"])
        self.assertEqual(label.color, payload["color"])

    def test_delete_label_removes_label_for_current_user(self) -> None:
        label = Label.objects.create(user=self.user, name="research")

        view = LabelDetailView.as_view()
        request = self._auth_delete(f"/api/labels/{label.id}/")
        response = view(request, pk=str(label.id))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Label.objects.filter(id=label.id).exists())

    def test_label_not_accessible_to_other_user(self) -> None:
        label = Label.objects.create(user=self.user, name="research")

        view = LabelDetailView.as_view()
        request = self._auth_delete(f"/api/labels/{label.id}/", user=self.other_user)
        response = view(request, pk=str(label.id))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Label.objects.filter(id=label.id).exists())
