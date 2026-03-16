from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
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


class ClipQuickSearchMigrationTests(TestCase):
    def test_postgres_quick_search_support_objects_exist(self) -> None:
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL-only migration checks")

        expected_indexes = {
            "clips_clip_user_id_3effdd_idx",
            "clips_clip_normalized_text_trgm_idx",
            "clips_clip_title_trgm_idx",
            "clips_clip_url_trgm_idx",
            "clips_label_name_trgm_idx",
            "clips_clip_search_vector_idx",
            "clips_label_search_vector_idx",
        }

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
            self.assertIsNotNone(cursor.fetchone())

            cursor.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = current_schema()
                AND tablename IN ('clips_clip', 'clips_label')
                """
            )
            index_names = {row[0] for row in cursor.fetchall()}

        for index_name in expected_indexes:
            self.assertIn(index_name, index_names)


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
