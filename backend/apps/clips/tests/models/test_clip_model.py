from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase

from apps.clips.models import Clip


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
