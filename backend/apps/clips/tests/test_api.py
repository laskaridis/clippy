from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.clips.models import Clip, Label
from apps.clips.api.views import ClipDetailView, ClipListCreateView


class ClipApiTests(TestCase):
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

    def test_list_clips_returns_only_current_user_clips(self) -> None:
        # Create two clips for the authenticated user and one for another user
        Clip.objects.create(
            user=self.user,
            title="First",
            url="https://example.com/one",
            domain="example.com",
            raw_content="First clip",
            normalized_text="first clip",
        )
        Clip.objects.create(
            user=self.user,
            title="Second",
            url="https://example.com/two",
            domain="example.com",
            raw_content="Second clip",
            normalized_text="second clip",
        )
        Clip.objects.create(
            user=self.other_user,
            title="Other",
            url="https://other.com/",
            domain="other.com",
            raw_content="Other user clip",
            normalized_text="other user clip",
        )

        view = ClipListCreateView.as_view()
        request = self._auth_get("/api/clips/")
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        ids = {str(item["id"]) for item in response.data}
        self.assertEqual(ids, {str(c.id) for c in Clip.objects.filter(user=self.user)})

    def test_create_clip_creates_clip_and_labels(self) -> None:
        payload = {
            "title": "My clip",
            "url": "https://example.com/path",
            "raw_content": "Some interesting text  \n  with spaces",
            "notes": "Optional notes",
            "labels": ["research", " personal "],
        }

        view = ClipListCreateView.as_view()
        request = self._auth_post("/api/clips/", payload)
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Clip.objects.filter(user=self.user).count(), 1)

        clip = Clip.objects.get(user=self.user)
        self.assertEqual(clip.url, payload["url"])
        self.assertEqual(clip.domain, "example.com")
        self.assertEqual(clip.normalized_text, "some interesting text with spaces")
        self.assertEqual(clip.notes, payload["notes"])

        # Labels should be created/associated and trimmed
        labels = list(clip.labels.order_by("name"))
        self.assertEqual(len(labels), 2)
        self.assertEqual({l.name for l in labels}, {"research", "personal"})
        for label in labels:
            self.assertEqual(label.user, self.user)

    def test_create_clip_requires_non_empty_raw_content(self) -> None:
        payload = {
            "url": "https://example.com/path",
            "raw_content": "   ",
        }

        view = ClipListCreateView.as_view()
        request = self._auth_post("/api/clips/", payload)
        response = view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("raw_content", response.data)

    def test_retrieve_clip_scoped_to_current_user(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        view = ClipDetailView.as_view()
        request = self._auth_get(f"/api/clips/{clip.id}/")
        response = view(request, pk=str(clip.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data["id"]), str(clip.id))
        self.assertEqual(response.data["title"], clip.title)

    def test_retrieve_clip_not_accessible_to_other_user(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        view = ClipDetailView.as_view()
        request = self._auth_get(f"/api/clips/{clip.id}/", user=self.other_user)
        response = view(request, pk=str(clip.id))

        self.assertEqual(response.status_code, 404)
