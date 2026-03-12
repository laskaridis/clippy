from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clips", "0002_label_uuid_quick_search_support"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clip",
            name="url",
            field=models.URLField(max_length=2048),
        ),
    ]
