"""Add a draft/published status to stories.

New stories start as drafts. Every story that exists when this migration runs
is already live, so it is marked published and stays visible to players. The
column has a database default, so the previous release can still create
stories between this migration and the release that reads the status.
"""

from django.db import migrations, models


def publish_existing_stories(apps, schema_editor):
    apps.get_model("core", "Story").objects.update(status="published")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_copy_words_into_forms"),
    ]

    operations = [
        migrations.AddField(
            model_name="story",
            name="status",
            field=models.CharField(
                choices=[("draft", "Draft"), ("published", "Published")],
                db_default="draft",
                default="draft",
                help_text="Only published stories are shown to players. A story with problems that break play stays a draft.",
                max_length=10,
            ),
        ),
        migrations.RunPython(publish_existing_stories, migrations.RunPython.noop),
    ]
