from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('network', '0003_rename_type_device_device_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitoringconfiguration',
            name='snmp_community',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='monitoringconfiguration',
            name='snmp_port',
            field=models.PositiveIntegerField(default=161),
        ),
        migrations.AddField(
            model_name='monitoringconfiguration',
            name='snmp_timeout_seconds',
            field=models.FloatField(default=2.0),
        ),
        migrations.CreateModel(
            name='SNMPMetric',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('metric', models.CharField(max_length=80)),
                ('oid', models.CharField(max_length=128)),
                ('value', models.TextField()),
                ('value_type', models.CharField(blank=True, max_length=40)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snmp_metrics', to='network.device')),
            ],
            options={
                'ordering': ['-timestamp', 'metric'],
                'indexes': [
                    models.Index(fields=['device', '-timestamp'], name='network_snm_device__f4d2a4_idx'),
                    models.Index(fields=['device', 'metric', '-timestamp'], name='network_snm_device__4f20ab_idx'),
                ],
            },
        ),
    ]
