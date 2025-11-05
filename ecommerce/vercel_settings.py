from .settings import *

# Production defaults for Vercel
DEBUG = False

# Allow Vercel preview/prod domains
ALLOWED_HOSTS = [
    '.vercel.app',
    'localhost',
    '127.0.0.1',
]

# Trust proxy headers from Vercel
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Use ephemeral SQLite in /tmp for serverless instances
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }
}

# Keep existing static settings from base; WhiteNoise will serve collected assets
# Ensure CSRF includes Vercel
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
]

# Ensure social auth treats HTTPS correctly on Vercel
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

