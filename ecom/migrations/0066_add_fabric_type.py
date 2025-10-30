# Generated manually to fix fabric_type NOT NULL constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0065_add_design_scale'),
    ]

    operations = [
        migrations.AddField(
            model_name='customjerseydesign',
            name='fabric_type',
            field=models.CharField(default='polyester', max_length=50),
        ),
    ]