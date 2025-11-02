# chat_project/settings.py
# Production-ready settings adapted from user's original file.
# - Read secrets from environment variables
# - Support Channels (ASGI) + Redis
# - Use dj-database-url for DATABASE_URL
# - WhiteNoise for static files
# - Secure production defaults (can be relaxed for local dev)

from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------ Environment helpers ------------------
def env(key, default=None):
    val = os.environ.get(key, default)
    return val

# ------------------ Basic ------------------
# IMPORTANT: do not commit a real SECRET_KEY into git. Use environment variable in production.
SECRET_KEY = env('SECRET_KEY', 'django-insecure-*-dev-secret-change-me-*')
DEBUG = env('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS must be set in production via environment variable (comma separated)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', '*').split(',') if env('ALLOWED_HOSTS') else ['*']

# CSRF trusted origins: comma-separated list (e.g. https://sayhi.io.vn)
# Keep local/ngrok origins for development convenience when DEBUG=True
default_trusted = 'http://127.0.0.1:8000,http://localhost:8000'
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', default_trusted).split(',') if env('CSRF_TRUSTED_ORIGINS') else []

# ------------------ Installed apps & middleware ------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Channels
    'channels',

    # Your apps
    'chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise to serve static files in production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chat_project.urls'

# Templates: keep templates folder from BASE_DIR/templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ASGI for Channels
ASGI_APPLICATION = 'chat_project.asgi.application'
WSGI_APPLICATION = 'chat_project.wsgi.application'  # keep for management commands

# ------------------ Database ------------------
DATABASE_URL = env('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ------------------ Password validation ------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------ Internationalization ------------------
LANGUAGE_CODE = 'vi'
TIME_ZONE = env('TIME_ZONE', 'Asia/Bangkok')
USE_I18N = True
USE_TZ = True

# ------------------ Static & Media ------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Use WhiteNoise storage for compressed manifest files (production)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ------------------ Auth redirects ------------------
LOGIN_REDIRECT_URL = '/chat/home/'
LOGIN_URL = '/chat/login/'
LOGOUT_REDIRECT_URL = '/chat/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------ Channels / Redis ------------------
# Prefer REDIS_URL from environment in production (e.g. redis://:password@host:port)
REDIS_URL = env('REDIS_URL', 'redis://127.0.0.1:6379/0')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# If you need a pure in-memory fallback for local dev, set CHANNEL_LAYERS_OVERRIDE
if env('CHANNEL_LAYERS_OVERRIDE', 'False') == 'True':
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }

# ------------------ Sessions & Cookie Security ------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', 'False') == 'True'

# ------------------ Security headers ------------------
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', 'False') == 'True'
SECURE_HSTS_SECONDS = int(env('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False') == 'True'
SECURE_HSTS_PRELOAD = env('SECURE_HSTS_PRELOAD', 'False') == 'True'
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# If your app is behind a proxy (Cloudflare, Render), this helps Django detect TLS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ------------------ Logging ------------------
LOG_LEVEL = env('LOG_LEVEL', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'verbose': {'format': '%(levelname)s %(asctime)s %(module)s %(message)s'}},
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': LOG_LEVEL},
}

# ------------------ Email (example) ------------------
EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', '')
EMAIL_PORT = int(env('EMAIL_PORT', '587')) if env('EMAIL_PORT') else None
EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')

# ------------------ Development conveniences ------------------
if DEBUG:
    # Allow common ngrok domains and localhost for CSRF when debugging
    extra = ['https://*.ngrok-free.app', 'https://*.ngrok-free.dev', 'https://*.trycloudflare.com']
    CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS + extra))
    # For dev convenience keep wildcard ALLOWED_HOSTS (but DO NOT use in production)
    if ALLOWED_HOSTS == ['*']:
        ALLOWED_HOSTS = ['*']

# ------------------ End of file ------------------
# Reminder: set environment variables on Render (SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, DATABASE_URL, REDIS_URL, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True, SECURE_SSL_REDIRECT=True)
