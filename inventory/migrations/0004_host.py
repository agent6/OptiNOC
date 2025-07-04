# Generated by Django 4.2.23 on 2025-06-28 22:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_tagging_alert_profiles"),
    ]

    operations = [
        migrations.CreateModel(
            name="Host",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("mac_address", models.CharField(max_length=32, unique=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("last_seen", models.DateTimeField(blank=True, null=True)),
                (
                    "interface",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hosts",
                        to="inventory.interface",
                    ),
                ),
            ],
        ),
    ]
