from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('network', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='device',
            old_name='type',
            new_name='device_type',
        ),
    ]
