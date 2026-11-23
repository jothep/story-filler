from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_alter_appconfig_options_remove_appconfig_description_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="story",
            name="word_bank",
        ),
    ]
