from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.test import TestCase

from apps.clips.models import Clip, Label
from apps.clips.services.clipqueries import (
    build_clip_filter_state,
    build_filtered_clips_queryset,
)


class ClipQueryServiceTests(TestCase):
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

    def test_build_clip_filter_state_keeps_accessible_labels_in_order(self) -> None:
        first_label = Label.objects.create(user=self.user, name="Research")
        second_label = Label.objects.create(user=self.user, name="Work")
        inaccessible_label = Label.objects.create(user=self.other_user, name="Secret")
        query_params = QueryDict(
            f"label={second_label.slug}&label=unknown&label={inaccessible_label.slug}&label={first_label.slug}&url=https%3A%2F%2Fexample.com%2Fclips%2F1"
        )

        filter_state = build_clip_filter_state(
            user=self.user,
            query_params=query_params,
        )

        self.assertEqual(
            filter_state["selected_label_slugs"],
            [second_label.slug, first_label.slug],
        )
        self.assertEqual(
            [label.slug for label in filter_state["selected_labels"]],
            [second_label.slug, first_label.slug],
        )
        self.assertEqual(
            filter_state["active_url_filter"],
            "https://example.com/clips/1",
        )

    def test_build_filtered_clips_queryset_applies_label_and_url_filters(self) -> None:
        matching_clip = Clip.objects.create(
            user=self.user,
            title="Matching",
            url="https://example.com/clips/1",
            domain="example.com",
            raw_content="Matching clip",
            normalized_text="matching clip",
        )
        other_url_clip = Clip.objects.create(
            user=self.user,
            title="Wrong URL",
            url="https://example.com/clips/2",
            domain="example.com",
            raw_content="Wrong URL clip",
            normalized_text="wrong url clip",
        )
        other_user_clip = Clip.objects.create(
            user=self.other_user,
            title="Other user",
            url="https://example.com/clips/1",
            domain="example.com",
            raw_content="Other user clip",
            normalized_text="other user clip",
        )
        label = Label.objects.create(user=self.user, name="Research")
        other_label = Label.objects.create(user=self.user, name="Work")
        matching_clip.labels.add(label)
        other_url_clip.labels.add(label)
        other_user_clip.labels.add(
            Label.objects.create(user=self.other_user, name="Research")
        )
        matching_clip.labels.add(other_label)
        query_params = QueryDict(
            f"label={label.slug}&label={other_label.slug}&url=https%3A%2F%2Fexample.com%2Fclips%2F1"
        )

        queryset = build_filtered_clips_queryset(
            user=self.user,
            query_params=query_params,
        )

        self.assertEqual(
            list(queryset.values_list("id", flat=True)),
            [matching_clip.id],
        )
