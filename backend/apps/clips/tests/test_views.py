from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from apps.clips.models import Clip
from apps.clips.views import ClipDetailView, ClipListView


class ClipHtmlViewsTests(TestCase):
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

    def test_clip_list_url_routing(self) -> None:
        match = resolve("/clips/")
        self.assertIs(match.func.view_class, ClipListView)

    def test_clip_detail_url_routing(self) -> None:
        match = resolve("/clips/00000000-0000-0000-0000-000000000000/")
        self.assertIs(match.func.view_class, ClipDetailView)

    def test_list_shows_only_current_user_clips(self) -> None:
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

        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:list"))

        self.assertEqual(response.status_code, 200)
        clips = list(response.context["clips"])
        self.assertEqual(len(clips), 2)
        self.assertTrue(all(clip.user == self.user for clip in clips))

    def test_detail_view_scoped_to_current_user(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        url = reverse("clips_web:detail", args=[clip.id])

        # Owner can see the clip
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["clip"], clip)

        # Other user receives 404
        self.client.force_login(self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
