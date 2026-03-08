import uuid

from django.db import migrations, models


# Backfills label UUIDs after the addition of the new column:
def populate_label_uuids(apps, schema_editor):
    Label = apps.get_model("clips", "Label")
    for label in Label.objects.filter(uuid__isnull=True).iterator():
        label.uuid = uuid.uuid4()
        label.save(update_fields=["uuid"])


def create_postgres_search_support(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    statements = [
        "CREATE EXTENSION IF NOT EXISTS pg_trgm",
        "CREATE INDEX IF NOT EXISTS clips_clip_normalized_text_trgm_idx ON clips_clip USING gin (normalized_text gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS clips_clip_title_trgm_idx ON clips_clip USING gin (title gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS clips_clip_url_trgm_idx ON clips_clip USING gin (url gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS clips_label_name_trgm_idx ON clips_label USING gin (name gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS clips_clip_search_vector_idx ON clips_clip USING gin (((setweight(to_tsvector('simple', coalesce(title, '')), 'A') || setweight(to_tsvector('simple', coalesce(normalized_text, '')), 'A')) || setweight(to_tsvector('simple', coalesce(url, '')), 'B')))",
        "CREATE INDEX IF NOT EXISTS clips_label_search_vector_idx ON clips_label USING gin (setweight(to_tsvector('simple', coalesce(name, '')), 'A'))",
    ]

    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def drop_postgres_search_support(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    statements = [
        "DROP INDEX IF EXISTS clips_label_search_vector_idx",
        "DROP INDEX IF EXISTS clips_clip_search_vector_idx",
        "DROP INDEX IF EXISTS clips_label_name_trgm_idx",
        "DROP INDEX IF EXISTS clips_clip_url_trgm_idx",
        "DROP INDEX IF EXISTS clips_clip_title_trgm_idx",
        "DROP INDEX IF EXISTS clips_clip_normalized_text_trgm_idx",
    ]

    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


class Migration(migrations.Migration):

    dependencies = [
        ("clips", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="label",
            name="uuid",
            field=models.UUIDField(db_index=True, editable=False, null=True),
        ),
        migrations.RunPython(populate_label_uuids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="label",
            name="uuid",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddIndex(
            model_name="clip",
            index=models.Index(fields=["user", "url"], name="clips_clip_user_id_3effdd_idx"),
        ),
        migrations.RunPython(create_postgres_search_support, drop_postgres_search_support),
    ]
