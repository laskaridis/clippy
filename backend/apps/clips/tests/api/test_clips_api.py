from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.clips.api.views import ClipDetailView, ClipListCreateView
from apps.clips.models import Clip, Label


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

    def test_list_clips_filters_by_repeated_label_slug_with_and_semantics(self) -> None:
        both_clip = Clip.objects.create(
            user=self.user,
            title="Has both labels",
            url="https://example.com/both",
            domain="example.com",
            raw_content="Has both labels",
            normalized_text="has both labels",
        )
        first_only_clip = Clip.objects.create(
            user=self.user,
            title="First only",
            url="https://example.com/first",
            domain="example.com",
            raw_content="First only",
            normalized_text="first only",
        )
        second_only_clip = Clip.objects.create(
            user=self.user,
            title="Second only",
            url="https://example.com/second",
            domain="example.com",
            raw_content="Second only",
            normalized_text="second only",
        )
        first_label = Label.objects.create(user=self.user, name="research")
        second_label = Label.objects.create(user=self.user, name="personal")
        both_clip.labels.add(first_label, second_label)
        first_only_clip.labels.add(first_label)
        second_only_clip.labels.add(second_label)

        view = ClipListCreateView.as_view()
        request = self._auth_get(
            f"/api/clips/?label={first_label.slug}&label={second_label.slug}"
        )
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [str(item["id"]) for item in response.data], [str(both_clip.id)]
        )

    def test_list_clips_ignores_unknown_or_inaccessible_label_slugs(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned clip",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )
        own_label = Label.objects.create(user=self.user, name="research")
        other_user_label = Label.objects.create(user=self.other_user, name="secret")
        clip.labels.add(own_label)

        view = ClipListCreateView.as_view()
        request = self._auth_get(
            f"/api/clips/?label={own_label.slug}&label=unknown&label={other_user_label.slug}"
        )
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([str(item["id"]) for item in response.data], [str(clip.id)])

    def test_list_clips_ignores_unknown_or_inaccessible_slugs_with_filter_groups(
        self,
    ) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned clip",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )
        own_label = Label.objects.create(user=self.user, name="research")
        other_user_label = Label.objects.create(user=self.other_user, name="secret")
        clip.labels.add(own_label)

        view = ClipListCreateView.as_view()
        request = self._auth_get(
            f"/api/clips/?group=domain&group=source&label={own_label.slug}&label=unknown&label={other_user_label.slug}"
        )
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([str(item["id"]) for item in response.data], [str(clip.id)])

    def test_list_clips_keeps_label_filtering_stable_with_non_label_group_params(
        self,
    ) -> None:
        matching_clip = Clip.objects.create(
            user=self.user,
            title="Matches label",
            url="https://example.com/one",
            domain="example.com",
            raw_content="Matches label",
            normalized_text="matches label",
        )
        non_matching_clip = Clip.objects.create(
            user=self.user,
            title="No match",
            url="https://example.com/two",
            domain="example.com",
            raw_content="No match",
            normalized_text="no match",
        )
        label = Label.objects.create(user=self.user, name="research")
        other_label = Label.objects.create(user=self.user, name="personal")
        matching_clip.labels.add(label)
        non_matching_clip.labels.add(other_label)

        view = ClipListCreateView.as_view()
        request = self._auth_get(
            f"/api/clips/?group=domain&group=source&label={label.slug}"
        )
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [str(item["id"]) for item in response.data], [str(matching_clip.id)]
        )

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
