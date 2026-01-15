from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.clips.models import Clip, ClipLabel, Label


class LabelModelTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="password123",
        )

    def test_label_name_is_unique_per_user(self) -> None:
        Label.objects.create(user=self.user, name="research")
        with self.assertRaises(IntegrityError):
            Label.objects.create(user=self.user, name="research")

    def test_same_label_name_allowed_for_different_users(self) -> None:
        User = get_user_model()
        other_user = User.objects.create_user(
            email="other@example.com",
            username="other@example.com",
            password="password123",
        )

        first = Label.objects.create(user=self.user, name="research")
        second = Label.objects.create(user=other_user, name="research")

        self.assertNotEqual(first.user, second.user)
        self.assertEqual(first.name, second.name)


class ClipModelTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="password123",
        )

    def test_default_ordering_is_most_recent_first(self) -> None:
        older = Clip.objects.create(
            user=self.user,
            title="Older",
            url="https://example.com/older",
            domain="example.com",
            raw_content="older",
            normalized_text="older",
        )
        newer = Clip.objects.create(
            user=self.user,
            title="Newer",
            url="https://example.com/newer",
            domain="example.com",
            raw_content="newer",
            normalized_text="newer",
        )

        clips = list(Clip.objects.filter(user=self.user))
        self.assertEqual(clips[0], newer)
        self.assertEqual(clips[1], older)


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
