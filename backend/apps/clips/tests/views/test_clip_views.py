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

    def test_list_filters_by_label_slug_for_current_user(self) -> None:
        matching_clip = Clip.objects.create(
            user=self.user,
            title="Matches label",
            url="https://example.com/label-match",
            domain="example.com",
            raw_content="Matches label",
            normalized_text="matches label",
        )
        non_matching_clip = Clip.objects.create(
            user=self.user,
            title="No match",
            url="https://example.com/no-match",
            domain="example.com",
            raw_content="No match",
            normalized_text="no match",
        )
        matching_label = Label.objects.create(user=self.user, name="research")
        other_label = Label.objects.create(user=self.user, name="personal")
        matching_clip.labels.add(matching_label)
        non_matching_clip.labels.add(other_label)

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?label={matching_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        clips = list(response.context["clips"])
        self.assertEqual([clip.id for clip in clips], [matching_clip.id])

    def test_list_filters_by_repeated_label_slugs_with_and_semantics(self) -> None:
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

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?label={first_label.slug}&label={second_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        clips = list(response.context["clips"])
        self.assertEqual([clip.id for clip in clips], [both_clip.id])
        self.assertEqual(
            response.context["selected_label_slugs"],
            [first_label.slug, second_label.slug],
        )

    def test_list_renders_label_as_clickable_link_to_label_filter(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="First",
            url="https://example.com/one",
            domain="example.com",
            raw_content="First clip content shown on list page",
            normalized_text="first clip content shown on list page",
        )
        label = Label.objects.create(user=self.user, name="research")
        clip.labels.add(label)

        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?label={label.slug}"',
            html=False,
        )

    def test_list_label_link_preserves_existing_non_label_query_params(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="First",
            url="https://example.com/one",
            domain="example.com",
            raw_content="First clip content shown on list page",
            normalized_text="first clip content shown on list page",
        )
        label = Label.objects.create(user=self.user, name="research")
        clip.labels.add(label)

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?url=https%3A%2F%2Fexample.com%2Fone&panel=expanded&group=domain"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?url=https%3A%2F%2Fexample.com%2Fone&amp;panel=expanded&amp;group=domain&amp;label={label.slug}"',
            html=False,
        )

    def test_list_label_link_preserves_existing_selected_labels(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="First",
            url="https://example.com/one",
            domain="example.com",
            raw_content="First clip content shown on list page",
            normalized_text="first clip content shown on list page",
        )
        selected_label = Label.objects.create(user=self.user, name="research")
        candidate_label = Label.objects.create(user=self.user, name="personal")
        clip.labels.add(selected_label, candidate_label)

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?label={selected_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?label={selected_label.slug}&amp;label={candidate_label.slug}"',
            html=False,
        )

    def test_list_ignores_unknown_label_slug(self) -> None:
        Clip.objects.create(
            user=self.user,
            title="First",
            url="https://example.com/one",
            domain="example.com",
            raw_content="First clip",
            normalized_text="first clip",
        )

        self.client.force_login(self.user)
        response = self.client.get(f"{reverse('clips_web:list')}?label=unknown")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(response.context["clips"])), 1)

    def test_list_ignores_inaccessible_label_slug(self) -> None:
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

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?label={own_label.slug}&label={other_user_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item.id for item in response.context["clips"]], [clip.id])
        self.assertEqual(response.context["selected_label_slugs"], [own_label.slug])

    def test_list_renders_selected_label_pills_with_remove_actions(self) -> None:
        first_label = Label.objects.create(user=self.user, name="research")
        second_label = Label.objects.create(user=self.user, name="personal")

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?panel=expanded&group=domain&label={first_label.slug}&label={second_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selected labels:")
        self.assertContains(response, "data-selected-label-pill", count=2)
        self.assertContains(response, "data-label-pill-remove", count=2)
        self.assertContains(
            response,
            f'data-label-slug="{first_label.slug}"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?panel=expanded&amp;group=domain&amp;label={second_label.slug}"',
            html=False,
        )
        self.assertContains(
            response,
            f'data-label-slug="{second_label.slug}"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?panel=expanded&amp;group=domain&amp;label={first_label.slug}"',
            html=False,
        )

    def test_list_clear_all_labels_link_removes_only_label_params(self) -> None:
        first_label = Label.objects.create(user=self.user, name="research")
        second_label = Label.objects.create(user=self.user, name="personal")

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?panel=expanded&group=domain&group=source&label={first_label.slug}&label={second_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["clear_label_filters_query"],
            "?panel=expanded&group=domain&group=source",
        )
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?panel=expanded&amp;group=domain&amp;group=source"',
            html=False,
        )

    def test_list_renders_filtered_empty_state_when_labels_have_no_results(
        self,
    ) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="No match",
            url="https://example.com/no-match",
            domain="example.com",
            raw_content="No match",
            normalized_text="no match",
        )
        clip.labels.add(Label.objects.create(user=self.user, name="personal"))
        selected_label = Label.objects.create(user=self.user, name="research")

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?label={selected_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No clips match the selected labels")
        self.assertContains(response, "Clear label filters")
        self.assertEqual(response.context["selected_labels_count"], 1)
        self.assertEqual(
            response.context["selected_label_metadata"],
            [{"id": selected_label.id, "name": "research", "slug": "research"}],
        )

    def test_list_filters_by_exact_url_for_current_user(self) -> None:
        matching_url = "https://example.com/path"
        matching_clip = Clip.objects.create(
            user=self.user,
            title="Exact URL 1",
            url=matching_url,
            domain="example.com",
            raw_content="Exact URL clip 1",
            normalized_text="exact url clip 1",
        )
        Clip.objects.create(
            user=self.user,
            title="Different URL",
            url="https://example.com/other",
            domain="example.com",
            raw_content="Different URL",
            normalized_text="different url",
        )
        Clip.objects.create(
            user=self.user,
            title="Exact URL 2",
            url=matching_url,
            domain="example.com",
            raw_content="Exact URL clip 2",
            normalized_text="exact url clip 2",
        )
        Clip.objects.create(
            user=self.other_user,
            title="Other user URL",
            url=matching_url,
            domain="example.com",
            raw_content="Other user clip",
            normalized_text="other user clip",
        )

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?url=https%3A%2F%2Fexample.com%2Fpath"
        )

        self.assertEqual(response.status_code, 200)
        clips = list(response.context["clips"])
        self.assertEqual(len(clips), 2)
        self.assertTrue(all(clip.user == self.user for clip in clips))
        self.assertIn(matching_clip.id, [clip.id for clip in clips])

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

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["clip"], clip)

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
