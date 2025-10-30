# Generated manually to fix NOT NULL constraint error
# Migration for adding text_position_3d field to CustomJerseyDesign model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0069_add_sleeve_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='customjerseydesign',
            name='text_position_3d',
            field=models.JSONField(default=dict, help_text='3D text position coordinates'),
        ),
    ]