from .settings import *
import os

# Production defaults for Vercel; allow temporary debug via env
DEBUG = os.getenv('VERCEL_DEBUG', '') == '1'

# Allow Vercel preview/production domains and your custom domains
ALLOWED_HOSTS = [
    '.vercel.app',
    'worksteamwear.shop',
    'www.worksteamwear.shop',
    'ecom.worksteamwear.shop',
    '*',
]

# Trust proxy headers; Vercel terminates HTTPS at the edge
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Use ephemeral SQLite in /tmp when DATABASE_URL is not provided
DATABASE_URL = os.getenv('DATABASE_URL', '')
if not DATABASE_URL:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }

# CSRF trusted origins for Vercel and your domain
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://worksteamwear.shop',
    'https://www.worksteamwear.shop',
    'http://worksteamwear.shop',
    'http://www.worksteamwear.shop',
    'https://ecom.worksteamwear.shop',
    'http://ecom.worksteamwear.shop',
]

# Social auth should report HTTPS behind proxy
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# Static files and sessions adjustments for Vercel serverless
# Avoid ManifestStaticFilesStorage which requires collectstatic manifest
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# WhiteNoise: disable long caching and enable autorefresh for ephemeral FS
WHITENOISE_MAX_AGE = 0
WHITENOISE_AUTOREFRESH = True

# Use cookie-based sessions to avoid DB writes during cold starts
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# Log server errors to console so Vercel shows tracebacks
DEBUG_PROPAGATE_EXCEPTIONS = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
