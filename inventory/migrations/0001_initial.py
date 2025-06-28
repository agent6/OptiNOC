from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AlertProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('cpu_threshold', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('interface_down', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hostname', models.CharField(max_length=255)),
                ('management_ip', models.GenericIPAddressField(blank=True, null=True, protocol='both', unpack_ipv4=True)),
                ('vendor', models.CharField(blank=True, max_length=255)),
                ('model', models.CharField(blank=True, max_length=255)),
                ('os_version', models.CharField(blank=True, max_length=255)),
                ('snmp_community', models.CharField(blank=True, max_length=255)),
                ('ssh_username', models.CharField(blank=True, max_length=255)),
                ('ssh_password', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Interface',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('mac_address', models.CharField(blank=True, max_length=32)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, protocol='both', unpack_ipv4=True)),
                ('status', models.CharField(blank=True, max_length=50)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interfaces', to='inventory.device')),
            ],
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=255)),
                ('interface_a', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='link_end_a', to='inventory.interface')),
                ('interface_b', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='link_end_b', to='inventory.interface')),
            ],
        ),
    ]

