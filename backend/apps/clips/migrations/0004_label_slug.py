from django.db import migrations, models
from django.utils.text import slugify


def _slug_base(name: str) -> str:
    normalized = slugify(name or "")
    if not normalized:
        return "label"
    return normalized[:110]


def backfill_label_slugs(apps, schema_editor):
    Label = apps.get_model("clips", "Label")

    seen_by_user: dict[int, set[str]] = {}
    for label in Label.objects.all().order_by("user_id", "id").iterator():
        seen_slugs = seen_by_user.setdefault(label.user_id, set())
        base = _slug_base(label.name)
        candidate = base
        suffix = 2
        while candidate in seen_slugs:
            suffix_text = f"-{suffix}"
            candidate = f"{base[: 120 - len(suffix_text)]}{suffix_text}"
            suffix += 1
        seen_slugs.add(candidate)
        label.slug = candidate
        label.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("clips", "0003_alter_clip_url_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="label",
            name="slug",
            field=models.SlugField(blank=True, max_length=120, null=True),
        ),
        migrations.RunPython(backfill_label_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="label",
            name="slug",
            field=models.SlugField(max_length=120),
        ),
        migrations.AddConstraint(
            model_name="label",
            constraint=models.UniqueConstraint(
                fields=("user", "slug"), name="uniq_label_slug_per_user"
            ),
        ),
    ]
