# Generated manually to fix collar_type NOT NULL constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0061_auto_20251027_2302'),
    ]

    operations = [
        migrations.AddField(
            model_name='customjerseydesign',
            name='collar_type',
            field=models.CharField(default='standard', max_length=50),
        ),
    ]