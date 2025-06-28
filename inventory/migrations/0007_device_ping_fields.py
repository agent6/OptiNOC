from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_alert_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="is_online",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="device",
            name="last_ping",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
