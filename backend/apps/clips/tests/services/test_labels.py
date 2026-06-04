from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.clips.models import Label
from apps.clips.services.labels import resolve_or_create_labels


class ResolveOrCreateLabelsTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="password123",
        )

    def test_resolve_or_create_labels_trims_names_and_skips_blanks(self) -> None:
        existing = Label.objects.create(user=self.user, name="research")

        labels = resolve_or_create_labels(
            user=self.user,
            names=[" research ", "", "  ", "work"],
        )

        self.assertEqual([label.name for label in labels], ["research", "work"])
        self.assertEqual(labels[0].id, existing.id)
        self.assertTrue(Label.objects.filter(user=self.user, name="work").exists())
