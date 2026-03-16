from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve

from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.clips.models import Clip, Label
from apps.clips.api.views import (
    ClipDetailView,
    ClipListCreateView,
    LabelDetailView,
    LabelListCreateView,
    QuickSearchView,
)


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

    def _auth_delete(self, path: str, user=None):
        request = self.factory.delete(path)
        force_authenticate(request, user=user or self.user)
        return request

    def _build_url_of_length(self, length: int) -> str:
        prefix = "https://example.com/"
        self.assertGreater(length, len(prefix))
        return f"{prefix}{'a' * (length - len(prefix))}"

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

    def test_create_clip_accepts_url_longer_than_200_chars(self) -> None:
        payload = {
            "url": self._build_url_of_length(2048),
            "raw_content": "Long URL should still be accepted.",
        }

        view = ClipListCreateView.as_view()
        request = self._auth_post("/api/clips/", payload)
        response = view(request)

        self.assertEqual(response.status_code, 201)
        clip = Clip.objects.get(user=self.user)
        self.assertEqual(clip.url, payload["url"])
        self.assertEqual(clip.domain, "example.com")

    def test_create_clip_rejects_url_longer_than_2048_chars(self) -> None:
        payload = {
            "url": self._build_url_of_length(2049),
            "raw_content": "This should fail validation.",
        }

        view = ClipListCreateView.as_view()
        request = self._auth_post("/api/clips/", payload)
        response = view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("url", response.data)

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

    def test_clip_list_url_routing(self) -> None:
        match = resolve("/api/clips/")
        self.assertIs(match.func.view_class, ClipListCreateView)

    def test_clip_detail_url_routing(self) -> None:
        match = resolve("/api/clips/00000000-0000-0000-0000-000000000000/")
        self.assertIs(match.func.view_class, ClipDetailView)

    def test_delete_clip_removes_clip_for_current_user(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        view = ClipDetailView.as_view()
        request = self._auth_delete(f"/api/clips/{clip.id}/")
        response = view(request, pk=str(clip.id))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Clip.objects.filter(id=clip.id).exists())

    def test_delete_clip_not_accessible_to_other_user(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        view = ClipDetailView.as_view()
        request = self._auth_delete(f"/api/clips/{clip.id}/", user=self.other_user)
        response = view(request, pk=str(clip.id))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Clip.objects.filter(id=clip.id).exists())


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


class QuickSearchApiTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="search@example.com",
            username="search@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            email="other-search@example.com",
            username="other-search@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.quick_search_path = "/api/clips/quick-search/"

    def _create_clip(self, *, user, title: str, url: str, content: str) -> Clip:
        return Clip.objects.create(
            user=user,
            title=title,
            url=url,
            domain="example.com",
            raw_content=content,
            normalized_text=content.lower(),
        )

    def test_quick_search_requires_authentication(self) -> None:
        response = self.client.get(self.quick_search_path, {"q": "python"})
        self.assertEqual(response.status_code, 401)

    def test_quick_search_requires_q_parameter(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(self.quick_search_path)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"q": ["This field is required."]})

    def test_quick_search_rejects_invalid_q_values(self) -> None:
        self.client.force_login(self.user)

        too_short = self.client.get(self.quick_search_path, {"q": "ab"})
        self.assertEqual(too_short.status_code, 400)
        self.assertEqual(
            too_short.json(),
            {"q": ["Ensure this field has at least 3 characters."]},
        )

        too_long = self.client.get(self.quick_search_path, {"q": "a" * 51})
        self.assertEqual(too_long.status_code, 400)
        self.assertEqual(
            too_long.json(),
            {"q": ["Ensure this field has no more than 50 characters."]},
        )

    def test_quick_search_accepts_phrase_queries_with_whitespace(self) -> None:
        self._create_clip(
            user=self.user,
            title="Stealth ship profile",
            url="https://example.com/stealth-ship",
            content="A stealth ship design reduces radar visibility.",
        )
        self.client.force_login(self.user)

        response = self.client.get(self.quick_search_path, {"q": "stealth ship"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["query"], "stealth ship")
        self.assertGreater(payload["total"], 0)
        self.assertTrue(
            any(
                hit["title"] == "Stealth ship profile"
                for hit in payload["hits"]["clips"]
            )
        )

    def test_quick_search_returns_grouped_user_scoped_results_with_global_max_five(
        self,
    ) -> None:
        label = Label.objects.create(user=self.user, name="python")
        other_label = Label.objects.create(user=self.other_user, name="python")

        owned = [
            self._create_clip(
                user=self.user,
                title=f"Python {index}",
                url=f"https://docs.python.org/{index}",
                content="python reference docs",
            )
            for index in range(7)
        ]
        for clip in owned:
            clip.labels.add(label)

        other_clip = self._create_clip(
            user=self.other_user,
            title="Python Other",
            url="https://other.example.com/python",
            content="python outsider",
        )
        other_clip.labels.add(other_label)

        self.client.force_login(self.user)
        response = self.client.get(self.quick_search_path, {"q": "python"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload["hits"].keys()), {"clips", "labels", "websites"})
        self.assertLessEqual(payload["total"], 5)
        total_hits = sum(
            len(payload["hits"][group]) for group in ("clips", "labels", "websites")
        )
        self.assertEqual(payload["total"], total_hits)

        for clip_hit in payload["hits"]["clips"]:
            self.assertIn("score", clip_hit)
            self.assertTrue(clip_hit["snippet"])
            self.assertIn("python", clip_hit["snippet"].lower())
            self.assertIn(clip_hit["clip_id"], {str(clip.id) for clip in owned})
            self.assertNotEqual(clip_hit["clip_id"], str(other_clip.id))

        for label_hit in payload["hits"]["labels"]:
            self.assertIn("score", label_hit)
            self.assertEqual(label_hit["label_slug"], label.slug)

    def test_quick_search_url_routing(self) -> None:
        match = resolve("/api/clips/quick-search/")
        self.assertIs(match.func.view_class, QuickSearchView)

    def test_quick_search_preserves_literal_percent_escape_sequences(self) -> None:
        self._create_clip(
            user=self.user,
            title="Escaped Python Notes",
            url="https://example.com/escaped",
            content="reference for python%20notes syntax",
        )
        self.client.force_login(self.user)

        response = self.client.get(f"{self.quick_search_path}?q=python%2520notes")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["query"], "python%20notes")
        self.assertGreater(payload["total"], 0)
        self.assertTrue(
            any(
                hit["title"] == "Escaped Python Notes"
                for hit in payload["hits"]["clips"]
            )
        )
