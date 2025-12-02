import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env for local runs
# (In Docker, variables come from docker-compose and this is harmless.)
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # library may be missing until requirements are installed
    load_dotenv = None  # type: ignore

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env before reading any environment variables
if load_dotenv:
    env_path = BASE_DIR / '.env'
    # override=False so real environment vars (e.g., from Docker) have priority
    load_dotenv(dotenv_path=str(env_path), override=False)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', '1') in ('1', 'true', 'True')

ALLOWED_HOSTS = [
    '*'
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'drf_spectacular',
    'django_filters',

    # Local apps
    'users',
    'lms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
# По умолчанию используем PostgreSQL (как указано в задании).
# Для явного использования SQLite задайте DB_ENGINE=sqlite в переменных окружения.
DB_ENGINE = os.environ.get('DB_ENGINE', 'postgres').lower()

if DB_ENGINE == 'postgres':
    # Поддерживаем два набора переменных окружения:
    # 1) DB_*      — для локального подключения (как в задании)
    # 2) POSTGRES_* — для docker-compose (уже настроено)
    pg_name = os.environ.get('DB_NAME') or os.environ.get('POSTGRES_DB', 'postgres')
    pg_user = os.environ.get('DB_USER') or os.environ.get('POSTGRES_USER', 'postgres')
    pg_password = os.environ.get('DB_PASSWORD') or os.environ.get('POSTGRES_PASSWORD', '')
    pg_host = os.environ.get('DB_HOST') or os.environ.get('POSTGRES_HOST', 'localhost')
    pg_port = os.environ.get('DB_PORT') or os.environ.get('POSTGRES_PORT', 5432)

    # Приведём порт к int при необходимости
    try:
        pg_port = int(pg_port)
    except (TypeError, ValueError):
        pg_port = 5432

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': pg_name,
            'USER': pg_user,
            'PASSWORD': pg_password,
            'HOST': pg_host,
            'PORT': pg_port,
        }
    }
else:
    # Use a dedicated subfolder for SQLite DB to avoid conflicts with any legacy db.sqlite3
    # that may exist in the project root (and potentially have inconsistent migration history).
    DB_DIR = BASE_DIR / 'db'
    os.makedirs(DB_DIR, exist_ok=True)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DB_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# DRF базовые настройки
REST_FRAMEWORK = {
    # Аутентификация: JWT (SimpleJWT) + сессии/базовая для админки/браузируемого API
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    # По умолчанию все эндпоинты закрыты; явно открываем только auth/registration
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# Куда перенаправлять после успешного входа/выхода (чтобы избежать 404 на /accounts/profile/)
LOGIN_REDIRECT_URL = '/api/'
LOGOUT_REDIRECT_URL = '/api/'
LOGIN_URL = '/api/auth/login/'

# Настройки схемы OpenAPI (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Django REST LMS API',
    'DESCRIPTION': 'Учебный API для курсов и уроков. Кастомный пользователь с авторизацией по email.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # Глобальная схема безопасности: Bearer JWT
    'SECURITY': [
        {'bearerAuth': []}
    ],
    'SECURITY_SCHEMES': {
        'bearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Вставьте access-токен из SimpleJWT: "Bearer <token>"'
        }
    },
}

# SimpleJWT — используем настройки по умолчанию библиотеки
