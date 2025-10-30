# Generated manually to fix is_3d_design NOT NULL constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0066_add_fabric_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='customjerseydesign',
            name='is_3d_design',
            field=models.BooleanField(default=False),
        ),
    ]