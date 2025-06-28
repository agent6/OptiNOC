from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='last_seen',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='last_scanned',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='discovered_snmp_community',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='device',
            name='discovered_ssh_username',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='device',
            name='discovered_ssh_password',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='device',
            name='roadblocks',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='interface',
            name='last_scanned',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
