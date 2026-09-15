from django.db import migrations


def rename_device_type_column(apps, schema_editor):
    """Rename the legacy Device.type column when it exists.

    SQLite can rebuild tables while applying earlier migrations. In some
    database states the column may already have the target name, so the
    migration must be idempotent with respect to the physical schema while
    still advancing Django's migration state.
    """
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(%s)" % quote_name("network_device")
            ).fetchall()
        }

    if "type" in columns and "device_type" not in columns:
        schema_editor.execute(
            'ALTER TABLE network_device RENAME COLUMN "type" TO "device_type"'
        )
    elif "device_type" not in columns:
        raise RuntimeError(
            "network_device has neither the legacy 'type' column nor the "
            "target 'device_type' column."
        )


def reverse_rename_device_type_column(apps, schema_editor):
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(%s)" % quote_name("network_device")
            ).fetchall()
        }

    if "device_type" in columns and "type" not in columns:
        schema_editor.execute(
            'ALTER TABLE network_device RENAME COLUMN "device_type" TO "type"'
        )
    elif "type" not in columns:
        raise RuntimeError(
            "network_device has neither the target 'device_type' column nor "
            "the legacy 'type' column."
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "network",
            "0002_rename_network_fau_device__f6c5a5_idx_network_fau_device__b8227f_idx_and_more",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    rename_device_type_column,
                    reverse_code=reverse_rename_device_type_column,
                ),
            ],
            state_operations=[
                migrations.RenameField(
                    model_name="device",
                    old_name="type",
                    new_name="device_type",
                ),
            ],
        ),
    ]
