from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from apps.clips.models import Clip, Label
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

    def test_list_renders_raw_content_and_labels_without_domain(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="First",
            url="https://example.com/one",
            domain="example.com",
            raw_content="First clip content shown on list page",
            normalized_text="first clip content shown on list page",
        )
        clip.labels.add(Label.objects.create(user=self.user, name="research"))

        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First clip content shown on list page")
        self.assertContains(response, "research")
        self.assertNotContains(
            response,
            '<th scope="col" class="d-none d-md-table-cell">Domain</th>',
            html=False,
        )

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

    def test_delete_removes_clip_for_current_user_via_delete_method(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        url = reverse("clips_web:detail", args=[clip.id])
        self.client.force_login(self.user)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Clip.objects.filter(id=clip.id).exists())

    def test_delete_not_accessible_to_other_user_via_delete_method(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        url = reverse("clips_web:detail", args=[clip.id])
        self.client.force_login(self.other_user)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Clip.objects.filter(id=clip.id).exists())

    def test_owner_can_update_clip_labels_via_post(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        # Existing label for the user should be reused
        existing_label = Label.objects.create(user=self.user, name="research")
        clip.labels.add(existing_label)

        url = reverse("clips_web:detail", args=[clip.id])
        self.client.force_login(self.user)
        response = self.client.post(url, {"labels": "research, work"})

        self.assertEqual(response.status_code, 302)
        clip.refresh_from_db()
        label_names = list(clip.labels.order_by("name").values_list("name", flat=True))
        self.assertEqual(label_names, ["research", "work"])

    def test_other_user_cannot_update_clip_labels(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Owned",
            url="https://example.com/owned",
            domain="example.com",
            raw_content="Owned clip",
            normalized_text="owned clip",
        )

        label = Label.objects.create(user=self.user, name="research")
        clip.labels.add(label)

        url = reverse("clips_web:detail", args=[clip.id])
        self.client.force_login(self.other_user)
        response = self.client.post(url, {"labels": "hijack"})

        self.assertEqual(response.status_code, 404)
        clip.refresh_from_db()
        label_names = list(clip.labels.order_by("name").values_list("name", flat=True))
        self.assertEqual(label_names, ["research"])


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

        # Label is not found for other user, so 404 and no change
        self.assertEqual(response.status_code, 404)
        label.refresh_from_db()
        self.assertEqual(label.name, "research")
