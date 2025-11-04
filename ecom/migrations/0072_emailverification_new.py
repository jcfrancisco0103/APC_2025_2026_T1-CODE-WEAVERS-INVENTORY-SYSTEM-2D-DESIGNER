"""
This migration was a duplicate of 0071_emailverification and attempted to
recreate the same EmailVerification table, causing
sqlite3.OperationalError: table "ecom_emailverification" already exists.

To preserve migration history without breaking existing databases or CI, we
convert this migration into a no-op. It now only depends on 0071 and performs
no operations.
"""

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0071_emailverification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    # No-op: 0071 already created the model/table
    operations = []
