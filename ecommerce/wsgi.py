"""
WSGI config for ecommerce project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use Vercel settings when deployed on Vercel
if os.environ.get('VERCEL'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.vercel_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

# On Vercel cold start, ensure the SQLite DB in /tmp exists by running migrations.
if os.environ.get('VERCEL'):
    try:
        import pathlib
        db_path = pathlib.Path('/tmp/db.sqlite3')
        flag_path = pathlib.Path('/tmp/.migrated')
        if not flag_path.exists():
            import django
            django.setup()
            from django.core.management import call_command
            # Create DB and apply migrations non-interactively
            call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)
            flag_path.touch()
    except Exception as e:
        # Log but continue to let Django handle and surface the error in logs
        import sys
        print(f"[WSGI] Migration step failed: {e}", file=sys.stderr)

# Create WSGI application with verbose error logging to Vercel console
try:
    application = get_wsgi_application()
except Exception as e:
    # Surface full traceback to stderr so Vercel shows details
    import sys, traceback
    print(f"[WSGI] Application init failed: {e}", file=sys.stderr)
    traceback.print_exc()
    raise

# Expose 'app' alias for Vercel's Python runtime
app = application
