from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0006_monitoringrecord_indexes'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='faultevent',
            constraint=models.UniqueConstraint(
                fields=('device', 'fault_type'),
                condition=Q(status__in=['active', 'acknowledged']),
                name='uniq_active_fault_type',
            ),
        ),
    ]
