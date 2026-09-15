import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('ip_address', models.GenericIPAddressField(protocol='IPv4')),
                ('type', models.CharField(choices=[('router', 'Router'), ('switch', 'Switch'), ('server', 'Server'), ('access-point', 'Access Point'), ('firewall', 'Firewall'), ('other', 'Other')], max_length=20)),
                ('status', models.CharField(choices=[('online', 'Online'), ('offline', 'Offline'), ('unknown', 'Unknown')], default='unknown', max_length=10)),
                ('monitoring_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name', 'created_at']},
        ),
        migrations.CreateModel(
            name='FaultEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fault_type', models.CharField(choices=[('DEVICE_UNREACHABLE', 'Device unreachable'), ('HIGH_LATENCY', 'High latency'), ('HIGH_PACKET_LOSS', 'High packet loss'), ('HIGH_CPU_USAGE', 'High CPU usage'), ('HIGH_MEMORY_USAGE', 'High memory usage'), ('INTERFACE_FAILURE', 'Interface failure'), ('CONNECTIVITY_FAILURE', 'Connectivity failure')], max_length=40)),
                ('severity', models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], max_length=10)),
                ('detected_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('acknowledged', 'Acknowledged'), ('resolved', 'Resolved')], default='active', max_length=15)),
                ('description', models.TextField(blank=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='faults', to='network.device')),
            ],
            options={'ordering': ['-detected_at']},
        ),
        migrations.CreateModel(
            name='MonitoringConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interval_seconds', models.PositiveIntegerField(default=60)),
                ('snmp_enabled', models.BooleanField(default=False)),
                ('snmp_version', models.CharField(blank=True, max_length=10, null=True)),
                ('available_metrics', models.JSONField(blank=True, default=list)),
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='monitoring_configuration', to='network.device')),
            ],
        ),
        migrations.CreateModel(
            name='MonitoringRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('reachable', models.BooleanField(null=True)),
                ('latency_ms', models.FloatField(blank=True, null=True)),
                ('packet_loss_percent', models.FloatField(blank=True, null=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monitoring_records', to='network.device')),
            ],
            options={'ordering': ['-timestamp']},
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('unread', 'Unread'), ('read', 'Read')], default='unread', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('fault', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification', to='network.faultevent')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='faultevent',
            index=models.Index(fields=['device', '-detected_at'], name='network_fau_device__f6c5a5_idx'),
        ),
        migrations.AddIndex(
            model_name='faultevent',
            index=models.Index(fields=['status', '-detected_at'], name='network_fau_status_4db0f0_idx'),
        ),
        migrations.AddIndex(
            model_name='monitoringrecord',
            index=models.Index(fields=['device', '-timestamp'], name='network_mon_device__fbe5f0_idx'),
        ),
    ]
