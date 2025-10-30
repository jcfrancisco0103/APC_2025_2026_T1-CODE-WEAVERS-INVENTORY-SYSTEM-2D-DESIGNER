# Generated manually to fix design_scale NOT NULL constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0064_add_collar_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='customjerseydesign',
            name='design_scale',
            field=models.FloatField(default=1.0),
        ),
    ]