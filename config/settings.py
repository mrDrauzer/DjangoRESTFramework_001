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

# Hosts and CSRF trusted origins
def _split_env(value: str | None) -> list[str]:
    if not value:
        return []
    # split by comma/space and strip
    parts = [p.strip() for p in value.replace('\n', ',').replace(' ', ',').split(',')]
    return [p for p in parts if p]

ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS')
ALLOWED_HOSTS = _split_env(ALLOWED_HOSTS_ENV) or ['*']

CSRF_TRUSTED_ORIGINS_ENV = os.environ.get('CSRF_TRUSTED_ORIGINS')
CSRF_TRUSTED_ORIGINS = _split_env(CSRF_TRUSTED_ORIGINS_ENV)

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
    'django_celery_beat',

    # Local apps
    'users',
    'lms',
]

# Optional: Prometheus metrics (enabled via PROMETHEUS_ENABLED=1)
PROMETHEUS_ENABLED = os.environ.get('PROMETHEUS_ENABLED', '0') in ('1', 'true', 'True')
if PROMETHEUS_ENABLED:
    INSTALLED_APPS.insert(0, 'django_prometheus')

# Optional: CORS (enabled via CORS_ENABLED=1)
CORS_ENABLED = os.environ.get('CORS_ENABLED', '0') in ('1', 'true', 'True')
if CORS_ENABLED:
    INSTALLED_APPS.append('corsheaders')

MIDDLEWARE = [
    # Prometheus before middleware (if enabled)
    *(
        ['django_prometheus.middleware.PrometheusBeforeMiddleware']
        if PROMETHEUS_ENABLED else []
    ),

    # CORS middleware should be high in the stack, before CommonMiddleware
    *(
        ['corsheaders.middleware.CorsMiddleware']
        if CORS_ENABLED else []
    ),

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Prometheus after middleware (if enabled)
    *(
        ['django_prometheus.middleware.PrometheusAfterMiddleware']
        if PROMETHEUS_ENABLED else []
    ),
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
    # Поддерживаем два набора переменных окружения и отдаём приоритет Docker-набору:
    # 1) POSTGRES_* — для docker-compose (сервис БД в одной сети)
    # 2) DB_*       — для локального нативного Postgres (если не используется Docker)
    # Это предотвращает ситуации, когда в .env остались DB_HOST=127.0.0.1,
    # и контейнеры пытаются подключиться к localhost вместо сервиса "db".
    pg_name = os.environ.get('POSTGRES_DB') or os.environ.get('DB_NAME', 'postgres')
    pg_user = os.environ.get('POSTGRES_USER') or os.environ.get('DB_USER', 'postgres')
    pg_password = os.environ.get('POSTGRES_PASSWORD') or os.environ.get('DB_PASSWORD', '')
    pg_host = os.environ.get('POSTGRES_HOST') or os.environ.get('DB_HOST', 'localhost')
    pg_port = os.environ.get('POSTGRES_PORT') or os.environ.get('DB_PORT', 5432)

    # Приведём порт к int при необходимости
    try:
        pg_port = int(pg_port)
    except (TypeError, ValueError):
        pg_port = 5432

    db_engine_path = 'django.db.backends.postgresql'
    if PROMETHEUS_ENABLED:
        # Use instrumented backend to export DB metrics
        db_engine_path = 'django_prometheus.db.backends.postgresql'

    # Connection tuning: allow persistent connections and set connect timeout
    try:
        conn_max_age_env = os.environ.get('DB_CONN_MAX_AGE', '60')
        CONN_MAX_AGE = int(conn_max_age_env) if str(conn_max_age_env).isdigit() else 60
    except Exception:
        CONN_MAX_AGE = 60

    try:
        connect_timeout_env = os.environ.get('DB_CONNECT_TIMEOUT', '5')
        CONNECT_TIMEOUT = int(connect_timeout_env) if str(connect_timeout_env).isdigit() else 5
    except Exception:
        CONNECT_TIMEOUT = 5

    DATABASES = {
        'default': {
            'ENGINE': db_engine_path,
            'NAME': pg_name,
            'USER': pg_user,
            'PASSWORD': pg_password,
            'HOST': pg_host,
            'PORT': pg_port,
            'CONN_MAX_AGE': CONN_MAX_AGE,
            'OPTIONS': {
                'connect_timeout': CONNECT_TIMEOUT,
            },
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
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')
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

# DRF throttling (optional, enabled via THROTTLE_ENABLED=1)
THROTTLE_ENABLED = os.environ.get('THROTTLE_ENABLED', '0') in ('1', 'true', 'True')
if THROTTLE_ENABLED:
    from rest_framework.throttling import AnonRateThrottle, UserRateThrottle  # type: ignore

    REST_FRAMEWORK |= {
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': os.environ.get('THROTTLE_ANON', '100/hour'),
            'user': os.environ.get('THROTTLE_USER', '1000/hour'),
        },
    }

# Stripe / внешние сервисы
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', '').strip()
STRIPE_CURRENCY = os.environ.get('STRIPE_CURRENCY', 'usd').lower()
# Базовый адрес сайта/бекенда для формирования success/cancel URL в Stripe Checkout
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000').rstrip('/')

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

# Email (по умолчанию — консольный backend для разработки)
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '0') or 0) or None
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '0') in ('1', 'true', 'True')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', '0') in ('1', 'true', 'True')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@example.com')

# Celery/Redis
REDIS_URL = os.environ.get('REDIS_URL')
if not REDIS_URL:
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
    REDIS_DB = os.environ.get('REDIS_DB', '0')
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', '0') in ('1', 'true', 'True')
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = USE_TZ
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Caching (optional, enabled via CACHE_ENABLED=1). Uses Redis if enabled.
CACHE_ENABLED = os.environ.get('CACHE_ENABLED', '0') in ('1', 'true', 'True')
CACHE_TTL = int(os.environ.get('CACHE_TTL', '300') or 300)

if CACHE_ENABLED:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': CACHE_TTL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
        }
    }
else:
    # Safe default local-memory cache for dev/tests
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-drf-lms',
        }
    }

# Celery Beat: периодическая задача деактивации неактивных пользователей
# Режим расписания можно переключать через переменную окружения CELERY_SCHEDULE_MODE
#   - "timedelta" (по умолчанию) — каждые 24 часа
#   - "crontab" — ежедневный запуск в указанное время (CRON_HOUR/CRON_MINUTE)
SCHEDULE_MODE = os.environ.get('CELERY_SCHEDULE_MODE', 'timedelta').lower()
if SCHEDULE_MODE == 'crontab':
    try:
        from celery.schedules import crontab  # type: ignore
    except Exception:
        crontab = None  # type: ignore

    cron_minute = str(os.environ.get('CRON_MINUTE', '0'))
    cron_hour = str(os.environ.get('CRON_HOUR', '3'))  # по умолчанию 03:00
    if crontab:
        beat_schedule_value = crontab(minute=cron_minute, hour=cron_hour, timezone=TIME_ZONE)
    else:
        # Fallback на timedelta, если по какой-то причине celery.schedules недоступен
        from datetime import timedelta  # type: ignore
        beat_schedule_value = timedelta(hours=24)
else:
    from datetime import timedelta  # type: ignore
    beat_schedule_value = timedelta(hours=24)  # ежедневно

# Celery Beat scheduler selection
# If CELERY_USE_DB_SCHEDULER=1, use django-celery-beat DatabaseScheduler and ignore in-code schedule.
USE_DB_SCHEDULER = os.environ.get('CELERY_USE_DB_SCHEDULER', '0') in ('1', 'true', 'True')

if USE_DB_SCHEDULER:
    CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
    CELERY_BEAT_SCHEDULE: dict = {}
else:
    CELERY_BEAT_SCHEDULE = {
        'deactivate-inactive-users-daily': {
            'task': 'users.tasks.deactivate_inactive_users',
            'schedule': beat_schedule_value,
            'options': {'expires': 60 * 60},
        },
    }

# Production security settings (enabled when DEBUG is False)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True  # legacy header, harmless
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # HSTS (can be tuned via env); by default keep conservative to avoid issues in dev
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0') or 0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', '0') in ('1', 'true', 'True')
    SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', '0') in ('1', 'true', 'True')
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', '0') in ('1', 'true', 'True')
    # Set when behind proxy that sets X-Forwarded-Proto
    if os.environ.get('SECURE_PROXY_SSL_HEADER', ''):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Logging configuration
# Set LOG_FORMAT=json to enable JSON logs (python-json-logger), otherwise plain text.
LOG_FORMAT = os.environ.get('LOG_FORMAT', 'plain').lower()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'plain': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',  # type: ignore
            'fmt': '%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)s %(process)s %(thread)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if LOG_FORMAT == 'json' else 'plain',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
}

# CORS configuration (only if enabled)
if CORS_ENABLED:
    # When CORS_ALLOW_ALL_ORIGINS=1, allow all origins (useful for dev)
    CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', '0') in ('1', 'true', 'True')
    CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS', '0') in ('1', 'true', 'True')
    CORS_ALLOWED_ORIGINS = _split_env(os.environ.get('CORS_ALLOWED_ORIGINS'))
    # Optionally allow custom headers/methods via env, else keep defaults of the package
    _custom_headers = _split_env(os.environ.get('CORS_ALLOW_HEADERS'))
    if _custom_headers:
        CORS_ALLOW_HEADERS = _custom_headers  # type: ignore
    _custom_methods = _split_env(os.environ.get('CORS_ALLOW_METHODS'))
    if _custom_methods:
        CORS_ALLOW_METHODS = _custom_methods  # type: ignore

# Optional: Sentry error tracking and performance monitoring
SENTRY_DSN = os.environ.get('SENTRY_DSN', '').strip()
if SENTRY_DSN:
    try:  # pragma: no cover - optional dependency
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.django import DjangoIntegration  # type: ignore
        from sentry_sdk.integrations.celery import CeleryIntegration  # type: ignore

        traces_sample_rate = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0') or 0)
        profiles_sample_rate = float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0') or 0)

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            send_default_pii=False,
            environment=os.environ.get('SENTRY_ENVIRONMENT', 'development' if DEBUG else 'production'),
            release=os.environ.get('SENTRY_RELEASE'),
        )
    except Exception:
        # If Sentry is not installed or fails to init, continue without it
        pass
