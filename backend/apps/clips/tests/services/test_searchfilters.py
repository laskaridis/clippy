from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.clips.models import Label
from apps.clips.services.searchfilters import resolve_selected_labels


class ResolveSelectedLabelsTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="password123",
        )

    def test_selected_labels_include_color_without_deferred_field_lookup(self) -> None:
        label = Label.objects.create(user=self.user, name="research", color="#123456")

        selected_labels = resolve_selected_labels(
            user=self.user,
            selected_label_slugs=[label.slug],
        )

        self.assertEqual(len(selected_labels), 1)
        self.assertEqual(selected_labels[0].color, "#123456")
        self.assertNotIn("color", selected_labels[0].get_deferred_fields())
