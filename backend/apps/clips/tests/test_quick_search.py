from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.clips.models import Clip, Label
from apps.clips.services import quick_search


class QuickSearchServiceTests(TestCase):
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

    # Factory method to create clips
    def _create_clip(
        self,
        *,
        user,
        title: str,
        url: str,
        raw_content: str,
        normalized_text: str,
    ) -> Clip:
        return Clip.objects.create(
            user=user,
            title=title,
            url=url,
            domain="example.com",
            raw_content=raw_content,
            normalized_text=normalized_text,
        )

    def test_rejects_too_short_query(self) -> None:
        with self.assertRaisesMessage(ValidationError, "at least 3 characters"):
            quick_search(user=self.user, query="ab")

    def test_rejects_whitespace_in_query(self) -> None:
        with self.assertRaisesMessage(ValidationError, "Whitespace is not allowed"):
            quick_search(user=self.user, query="python notes")

    def test_rejects_too_long_query(self) -> None:
        with self.assertRaisesMessage(ValidationError, "no more than 50 characters"):
            quick_search(user=self.user, query=("a" * 51))

    def test_results_are_scoped_to_current_user(self) -> None:
        own_clip = self._create_clip(
            user=self.user,
            title="Python notes",
            url="https://example.com/python",
            raw_content="Python clipping",
            normalized_text="python clipping",
        )
        own_label = Label.objects.create(user=self.user, name="python")
        own_clip.labels.add(own_label)

        other_clip = self._create_clip(
            user=self.other_user,
            title="Python secrets",
            url="https://other.com/python",
            raw_content="private content",
            normalized_text="python private",
        )
        other_label = Label.objects.create(user=self.other_user, name="python")
        other_clip.labels.add(other_label)

        result = quick_search(user=self.user, query="python")

        clip_ids: set[str] = {item["clip_id"] for item in result["hits"]["clips"]}
        label_ids: set[str] = {item["label_uuid"] for item in result["hits"]["labels"]}
        website_urls: set[str] = {item["url"] for item in result["hits"]["websites"]}

        self.assertNotIn(str(other_clip.id), clip_ids)
        self.assertNotIn(str(other_label.uuid), label_ids)
        self.assertNotIn(other_clip.url, website_urls)
        self.assertIn(str(own_clip.id), clip_ids)

    def test_result_count_is_capped_to_five_globally(self) -> None:
        for idx in range(7):
            clip = self._create_clip(
                user=self.user,
                title=f"Python clip {idx}",
                url=f"https://example.com/python/{idx}",
                raw_content=f"python content {idx}",
                normalized_text=f"python content {idx}",
            )
            label, _ = Label.objects.get_or_create(user=self.user, name=f"python-{idx}")
            clip.labels.add(label)

        result = quick_search(user=self.user, query="python")

        total_items = (
            len(result["hits"]["clips"])
            + len(result["hits"]["labels"])
            + len(result["hits"]["websites"])
        )
        self.assertEqual(result["total"], 5)
        self.assertEqual(total_items, 5)

    def test_website_hits_are_grouped_by_exact_url(self) -> None:
        exact_url = "https://example.com/articles/python"
        self._create_clip(
            user=self.user,
            title="Guide A",
            url=exact_url,
            raw_content="python docs",
            normalized_text="python docs",
        )
        self._create_clip(
            user=self.user,
            title="Guide B",
            url=exact_url,
            raw_content="python docs second",
            normalized_text="python docs second",
        )
        self._create_clip(
            user=self.user,
            title="Guide C",
            url="https://example.com/articles/python-advanced",
            raw_content="python advanced",
            normalized_text="python advanced",
        )

        result = quick_search(user=self.user, query="example.com/articles/python")

        website_hits = {
            item["url"]: item["clip_count"] for item in result["hits"]["websites"]
        }
        self.assertIn(exact_url, website_hits)
        self.assertEqual(website_hits[exact_url], 2)
        self.assertTrue(all(count >= 1 for count in website_hits.values()))

    def test_ordering_is_deterministic_for_tied_scores(self) -> None:
        older = self._create_clip(
            user=self.user,
            title="Alpha",
            url="https://example.com/a",
            raw_content="alpha content",
            normalized_text="alpha content",
        )
        newer = self._create_clip(
            user=self.user,
            title="Alpha",
            url="https://example.com/b",
            raw_content="alpha content",
            normalized_text="alpha content",
        )
        Clip.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        Clip.objects.filter(pk=newer.pk).update(created_at=timezone.now())

        first = quick_search(user=self.user, query="alpha")
        second = quick_search(user=self.user, query="alpha")
        first_ids = [item["clip_id"] for item in first["hits"]["clips"]]
        second_ids = [item["clip_id"] for item in second["hits"]["clips"]]

        self.assertEqual(first_ids, second_ids)
        self.assertGreaterEqual(len(first_ids), 2)
        self.assertEqual(first_ids[0], str(newer.id))

    def test_returns_original_query_value(self) -> None:
        self._create_clip(
            user=self.user,
            title="Python",
            url="https://example.com/python",
            raw_content="python content",
            normalized_text="python content",
        )

        result = quick_search(user=self.user, query="python%32")
        self.assertEqual(result["query"], "python%32")
