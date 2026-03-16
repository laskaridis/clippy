from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve

from rest_framework.test import APIClient

from apps.clips.api.views import QuickSearchView
from apps.clips.models import Clip, Label


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
