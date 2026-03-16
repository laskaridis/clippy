from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clips.models import Clip, ClipLabel, Label


class ClipLabelModelTests(TestCase):
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

    def test_cliplabel_enforces_same_user_for_clip_and_label(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Clip",
            url="https://example.com/",
            domain="example.com",
            raw_content="content",
            normalized_text="content",
        )
        label = Label.objects.create(user=self.other_user, name="research")

        with self.assertRaises(ValidationError):
            ClipLabel.objects.create(clip=clip, label=label)

    def test_cliplabel_allows_same_user_for_clip_and_label(self) -> None:
        clip = Clip.objects.create(
            user=self.user,
            title="Clip",
            url="https://example.com/",
            domain="example.com",
            raw_content="content",
            normalized_text="content",
        )
        label = Label.objects.create(user=self.user, name="research")

        association = ClipLabel.objects.create(clip=clip, label=label)
        self.assertEqual(association.clip, clip)
        self.assertEqual(association.label, label)
