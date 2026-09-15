from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('network', '0002_rename_network_fau_device__f6c5a5_idx_network_fau_device__b8227f_idx_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE network_device RENAME COLUMN "type" TO "device_type"',
                    reverse_sql='ALTER TABLE network_device RENAME COLUMN "device_type" TO "type"',
                ),
            ],
            state_operations=[
                migrations.RenameField(
                    model_name='device',
                    old_name='type',
                    new_name='device_type',
                ),
            ],
        ),
    ]
