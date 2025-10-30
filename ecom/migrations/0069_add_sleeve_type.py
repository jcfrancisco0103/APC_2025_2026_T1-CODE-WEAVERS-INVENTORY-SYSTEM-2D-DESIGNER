# Generated manually to add sleeve_type field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0068_add_logo_position_3d'),
    ]

    operations = [
        migrations.AddField(
            model_name='customjerseydesign',
            name='sleeve_type',
            field=models.CharField(default='short_sleeve', max_length=50),
        ),
        # Update existing records to have the default sleeve_type
        migrations.RunSQL(
            "UPDATE ecom_customjerseydesign SET sleeve_type = 'short_sleeve' WHERE sleeve_type IS NULL OR sleeve_type = '';",
            reverse_sql="UPDATE ecom_customjerseydesign SET sleeve_type = NULL;"
        ),
        # Also update jersey_type and collar_type defaults for existing records
        migrations.RunSQL(
            "UPDATE ecom_customjerseydesign SET jersey_type = 'jersey' WHERE jersey_type = 'standard';",
            reverse_sql="UPDATE ecom_customjerseydesign SET jersey_type = 'standard' WHERE jersey_type = 'jersey';"
        ),
        migrations.RunSQL(
            "UPDATE ecom_customjerseydesign SET collar_type = 'crew_neck' WHERE collar_type = 'standard';",
            reverse_sql="UPDATE ecom_customjerseydesign SET collar_type = 'standard' WHERE collar_type = 'crew_neck';"
        ),
    ]