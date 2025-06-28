from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_discovery_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='devices', to='inventory.tag'),
        ),
        migrations.AddField(
            model_name='alertprofile',
            name='devices',
            field=models.ManyToManyField(blank=True, related_name='alert_profiles', to='inventory.device'),
        ),
        migrations.AddField(
            model_name='alertprofile',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='alert_profiles', to='inventory.tag'),
        ),
    ]
