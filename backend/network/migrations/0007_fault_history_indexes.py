from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0006_monitoringrecord_indexes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='faultevent',
            index=models.Index(
                fields=['device', 'status', '-detected_at'],
                name='fault_device_status_time_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='faultevent',
            index=models.Index(
                fields=['device', 'fault_type', '-detected_at'],
                name='fault_device_type_time_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='faultevent',
            index=models.Index(
                fields=['severity', '-detected_at'],
                name='fault_severity_time_idx',
            ),
        ),
    ]
