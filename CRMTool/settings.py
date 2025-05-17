import os
from pathlib import Path
import dj_database_url
from datetime import timedelta

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-p9&e07ltcc4ghu**l0b23#huhmldm#8x)fskp)w=$nd62#yah@'
DEBUG = True

ALLOWED_HOSTS = ["crmbussinesstool.up.railway.app","bussinesstoolcrm.up.railway.app"]  # Set specific Railway domain in production for security

DATABASES_URL = "postgresql://postgres:KJsFPonSukFNLOHNafzGZTFyaVMdjqwH@switchback.proxy.rlwy.net:54684/railway"
# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'corsheaders',
    'daphne',
    'channels',
    'django.contrib.staticfiles',
    'auth_section',
    'rest_framework',
    'rest_framework_simplejwt',
    'leads_section',
    'databank_section',
    'followup_section',
    'task_section',
    'project_section',
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Channels
ASGI_APPLICATION = "CRMTool.asgi.application"
WSGI_APPLICATION = 'CRMTool.wsgi.application'

ROOT_URLCONF = 'CRMTool.urls'



CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv('REDIS_URL', 'redis://default:DWhjNCDMOdqAPwcqGaellyGHFPEJndpn@interchange.proxy.rlwy.net:59182')],
        },
    },
    "notifications": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}




# Database (Railway: uses DATABASE_URL env)
DATABASES = {
    'default': dj_database_url.config( default=DATABASES_URL, conn_max_age=1800)
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Timezone and Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files for Railway (uses Whitenoise)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media/'

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email settings (update with actual credentials or use environment variables)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'suryakrishnavaliyapurakkal@gmail.com'
EMAIL_HOST_PASSWORD = 'ndal ahrg ettv tsyd'

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS = os.path.join(BASE_DIR, "google_sheets_credentials.json")
GOOGLE_SHEET_ID = "1IcBnZkLH1HO8mzK8-mIlX7dhTy79fdJBR2VBBo12ad0"

# Celery with Redis
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://default:DWhjNCDMOdqAPwcqGaellyGHFPEJndpn@interchange.proxy.rlwy.net:59182')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# CORS & CSRF
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'accept',
    'x-requested-with',
    'x-csrftoken',
    'credentials',
]

CORS_ALLOWED_ORIGINS = [
    "https://bussinesstoolcrm.up.railway.app",
    "https://crmbussinesstool.up.railway.app",
    
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/.*\.up\.railway\.app$",
]

CSRF_TRUSTED_ORIGINS = [
    "https://bussinesstoolcrm.up.railway.app",
    "https://crmbussinesstool.up.railway.app",
    
]

CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False

SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
