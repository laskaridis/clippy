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

    def test_list_clear_all_link_removes_label_and_url_params(self) -> None:
        first_label = Label.objects.create(user=self.user, name="research")
        second_label = Label.objects.create(user=self.user, name="personal")

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?panel=expanded&group=domain&group=source&url=https%3A%2F%2Fexample.com%2Fone&label={first_label.slug}&label={second_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["clear_all_filters_query"],
            "?panel=expanded&group=domain&group=source",
        )
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?panel=expanded&amp;group=domain&amp;group=source"',
            html=False,
        )

    def test_list_url_filter_section_renders_clear_all_when_no_labels_selected(
        self,
    ) -> None:
        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?url=https%3A%2F%2Fexample.com%2Fone&panel=expanded"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["clear_all_filters_query"],
            "?panel=expanded",
        )
        self.assertContains(
            response,
            "Active URL filter:",
        )
        self.assertContains(
            response,
            f'href="{reverse("clips_web:list")}?panel=expanded"',
            html=False,
        )
        self.assertContains(response, "Clear all")

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
        self.assertContains(response, "Clear all")
        self.assertEqual(response.context["selected_labels_count"], 1)
        self.assertEqual(
            response.context["selected_label_metadata"],
            [
                {
                    "id": selected_label.id,
                    "name": "research",
                    "slug": "research",
                    "color": None,
                }
            ],
        )

    def test_list_context_exposes_flat_label_filters_dataset_with_counts_and_color(
        self,
    ) -> None:
        selected_label = Label.objects.create(user=self.user, name="Zulu")
        selected_clip = Clip.objects.create(
            user=self.user,
            title="Selected clip",
            url="https://example.com/selected",
            domain="example.com",
            raw_content="Selected clip",
            normalized_text="selected clip",
        )
        selected_clip.labels.add(selected_label)

        for name in [
            "Alpha",
            "Beta",
            "Charlie",
            "Delta",
            "Echo",
            "Foxtrot",
            "Golf",
            "Hotel",
            "India",
            "Juliet",
            "Kilo",
        ]:
            Label.objects.create(user=self.user, name=name)

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?label={selected_label.slug}"
        )

        self.assertEqual(response.status_code, 200)
        dataset = response.context["label_filters_dataset"]
        self.assertEqual(len(dataset), 12)
        self.assertEqual(
            [item["name"] for item in dataset],
            [
                "Alpha",
                "Beta",
                "Charlie",
                "Delta",
                "Echo",
                "Foxtrot",
                "Golf",
                "Hotel",
                "India",
                "Juliet",
                "Kilo",
                "Zulu",
            ],
        )
        self.assertEqual(
            [item for item in dataset if item["slug"] == selected_label.slug][0][
                "color"
            ],
            None,
        )
        self.assertEqual(
            [item for item in dataset if item["slug"] == selected_label.slug][0][
                "contextual_results_count"
            ],
            1,
        )

    def test_list_context_dataset_is_alphabetical_independent_of_selected_order(
        self,
    ) -> None:
        first = Label.objects.create(user=self.user, name="Research")
        second = Label.objects.create(user=self.user, name="Personal")
        clip = Clip.objects.create(
            user=self.user,
            title="Both labels",
            url="https://example.com/both",
            domain="example.com",
            raw_content="Both labels",
            normalized_text="both labels",
        )
        clip.labels.add(first, second)

        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('clips_web:list')}?label={second.slug}&label={first.slug}"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.context["label_filters_dataset"]
        self.assertEqual(
            [item["slug"] for item in payload],
            [second.slug, first.slug],
        )

    def test_list_panel_state_defaults_and_accepts_supported_values(self) -> None:
        self.client.force_login(self.user)
        base_url = reverse("clips_web:list")

        default_response = self.client.get(base_url)
        self.assertEqual(default_response.context["panel_state"], "collapsed")

        invalid_response = self.client.get(f"{base_url}?panel=invalid")
        self.assertEqual(invalid_response.context["panel_state"], "collapsed")

        for value in ("expanded", "collapsed", "open", "closed"):
            response = self.client.get(f"{base_url}?panel={value}")
            self.assertEqual(response.context["panel_state"], value)

    def test_list_navbar_renders_quick_search_input_and_not_inert_label(
        self,
    ) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'class="nav-item clips-nav-search-item"',
            html=False,
        )
        self.assertContains(
            response,
            'id="quick-search-input"',
            html=False,
        )
        self.assertContains(
            response,
            '<label class="visually-hidden" for="quick-search-input">Quick search</label>',
            html=False,
        )
        self.assertNotContains(
            response,
            "data-nav-quick-search-label",
            html=False,
        )
        self.assertNotContains(
            response,
            '<section class="mb-4" aria-label="Quick search">',
            html=False,
        )

    def test_labels_page_renders_clips_navbar_quick_search(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:labels"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="quick-search-input"', html=False)
        self.assertContains(
            response,
            '<label class="visually-hidden" for="quick-search-input">Quick search</label>',
            html=False,
        )
        self.assertNotContains(response, "data-nav-quick-search-label", html=False)

    def test_list_renders_accessible_sidebar_and_drawer_filter_controls(self) -> None:
        for index in range(12):
            Label.objects.create(user=self.user, name=f"Label {index:02d}")

        self.client.force_login(self.user)
        response = self.client.get(reverse("clips_web:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "data-filter-panel-toggle",
            html=False,
        )
        self.assertContains(
            response,
            'aria-controls="label-filter-sidebar-panel"',
            html=False,
        )
        self.assertContains(
            response,
            'aria-expanded="false"',
            html=False,
        )
        self.assertContains(
            response,
            "data-filter-drawer-trigger",
            html=False,
        )
        self.assertContains(
            response,
            'aria-controls="label-filter-drawer"',
            html=False,
        )
        self.assertContains(
            response,
            'aria-haspopup="dialog"',
            html=False,
        )
        self.assertContains(
            response,
            'id="label-filter-drawer"',
            html=False,
        )
        self.assertContains(
            response,
            'class="label-filter-drawer d-none"',
            html=False,
        )
        self.assertContains(response, 'role="dialog"', html=False)
        self.assertContains(response, 'aria-modal="true"', html=False)
        self.assertContains(response, "data-filter-drawer-close", html=False)
        self.assertContains(response, "data-filter-drawer-backdrop", html=False)
        self.assertContains(response, "data-label-search-input", count=2, html=False)
        self.assertContains(response, "data-label-show-more", count=2, html=False)
        self.assertContains(response, "data-filter-no-horizontal-scroll", html=False)

    def test_list_small_screen_filters_trigger_shows_selected_labels_count(
        self,
    ) -> None:
        first_label = Label.objects.create(user=self.user, name="research")
        second_label = Label.objects.create(user=self.user, name="personal")

        self.client.force_login(self.user)
        base_url = reverse("clips_web:list")

        unselected_response = self.client.get(base_url)
        self.assertEqual(unselected_response.status_code, 200)
        self.assertContains(
            unselected_response,
            "<span data-selected-label-count>0</span>",
            html=False,
        )

        selected_response = self.client.get(
            f"{base_url}?label={first_label.slug}&label={second_label.slug}"
        )
        self.assertEqual(selected_response.status_code, 200)
        self.assertContains(
            selected_response,
            "<span data-selected-label-count>2</span>",
            html=False,
        )

        deselected_response = self.client.get(f"{base_url}?label={first_label.slug}")
        self.assertEqual(deselected_response.status_code, 200)
        self.assertContains(
            deselected_response,
            "<span data-selected-label-count>1</span>",
            html=False,
        )

    def test_list_truncation_exposes_full_label_text_for_assistive_tech(self) -> None:
        long_name = (
            "Label with a very long descriptive name that must remain fully available"
        )
        label = Label.objects.create(user=self.user, name=long_name)

        self.client.force_login(self.user)
        response = self.client.get(f"{reverse('clips_web:list')}?label={label.slug}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'data-full-label="{long_name}"',
            html=False,
        )
        self.assertContains(
            response,
            f'title="{long_name}"',
            html=False,
        )
        self.assertContains(
            response,
            f'data-label-full-name="{long_name}"',
            html=False,
        )
        self.assertContains(
            response,
            f'aria-label="Toggle label {long_name}"',
            html=False,
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
