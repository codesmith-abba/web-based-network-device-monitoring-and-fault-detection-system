from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0005_rename_network_snm_device__f4d2a4_idx_network_snm_device__28657a_idx_and_more'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='monitoringrecord',
            new_name='monitoring_device_time_idx',
            old_name='network_mon_device__44e2a3_idx',
        ),
        migrations.AddIndex(
            model_name='monitoringrecord',
            index=models.Index(fields=['timestamp'], name='monitoring_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='monitoringrecord',
            index=models.Index(fields=['device', 'reachable', '-timestamp'], name='monitoring_device_status_time_idx'),
        ),
    ]
