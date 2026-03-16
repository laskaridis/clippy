from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.clips.models import Label


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

    def test_label_uuid_is_auto_generated_and_unique(self) -> None:
        first = Label.objects.create(user=self.user, name="research")
        second = Label.objects.create(user=self.user, name="work")

        self.assertIsNotNone(first.uuid)
        self.assertIsNotNone(second.uuid)
        self.assertNotEqual(first.uuid, second.uuid)

    def test_label_slug_is_generated_from_name(self) -> None:
        label = Label.objects.create(user=self.user, name="Deep Work")
        self.assertEqual(label.slug, "deep-work")

    def test_label_slug_is_unique_per_user(self) -> None:
        first = Label.objects.create(user=self.user, name="Research")
        second = Label.objects.create(user=self.user, name="research")

        self.assertEqual(first.slug, "research")
        self.assertEqual(second.slug, "research-2")

    def test_same_slug_allowed_for_different_users(self) -> None:
        User = get_user_model()
        other_user = User.objects.create_user(
            email="other-slug@example.com",
            username="other-slug@example.com",
            password="password123",
        )
        first = Label.objects.create(user=self.user, name="Research")
        second = Label.objects.create(user=other_user, name="Research")

        self.assertEqual(first.slug, second.slug)

    def test_slug_regenerated_when_name_changes(self) -> None:
        label = Label.objects.create(user=self.user, name="Research")
        label.name = "Updated Research"
        label.save()

        self.assertEqual(label.slug, "updated-research")
