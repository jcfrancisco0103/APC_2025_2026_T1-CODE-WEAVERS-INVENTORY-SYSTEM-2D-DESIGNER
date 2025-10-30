# Generated manually to fix logo_position_3d NOT NULL constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0067_add_is_3d_design'),
    ]

    operations = [
        migrations.AddField(
            model_name='customjerseydesign',
            name='logo_position_3d',
            field=models.JSONField(default=dict, help_text="3D logo position coordinates"),
        ),
    ]