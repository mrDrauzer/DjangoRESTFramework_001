import logging as _logging  # local alias to avoid polluting global namespace
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import HttpResponse
from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def index_view(_request):
    html = """
    <!doctype html>
    <html lang="ru">
    <head>
      <meta charset="utf-8" />
      <title>Django REST LMS — стартовая страница</title>
      <style>
        body { font-family: system-ui, sans-serif; margin: 2rem; }
        h1 { margin-bottom: .5rem; }
        ul { line-height: 1.8; }
        code { background: #f5f5f5; padding: 2px 4px; border-radius: 4px; }
      </style>
    </head>
    <body>
      <h1>Добро пожаловать 👋</h1>
      <p>Полезные ссылки по проекту:</p>
      <ul>
        <li><a href="/admin/">Админка</a></li>
        <li><a href="/api/">API Root (DRF Router)</a></li>
        <li><a href="/api/courses/">API: Курсы</a></li>
        <li><a href="/api/lessons/">API: Уроки</a></li>
        <li><a href="/api/users/">API: Пользователи</a></li>
        <li><a href="/api/docs/">Swagger UI</a></li>
        <li><a href="/api/redoc/">ReDoc</a></li>
        <li><a href="/api/schema/">OpenAPI schema (JSON)</a></li>
        <li><a href="/api/schema/json/">OpenAPI JSON (inline)</a></li>
        <li><a href="/api/schema/yaml/">OpenAPI YAML</a></li>
        <li><a href="/api/auth/login/">API Login</a> / <a href="/api/auth/logout/">Logout</a></li>
        <li><a href="/payments/success">Страница успешной оплаты</a> / <a href="/payments/cancel">Отмена оплаты</a></li>
      </ul>
      <p>Подсказка: для авторизации используйте учётную запись суперпользователя, созданную через <code>createsuperuser</code>.</p>
    </body>
    </html>
    """
    return HttpResponse(html)


def payments_success_view(_request):
    html = """
    <!doctype html>
    <html lang="ru">
    <head>
      <meta charset="utf-8" />
      <title>Оплата успешна</title>
      <style>body{font-family:system-ui,sans-serif;margin:2rem;} a{color:#0a62c9;}</style>
    </head>
    <body>
      <h1>Оплата прошла успешно ✅</h1>
      <p>Спасибо! Можете вернуться в приложение.</p>
      <p><a href="/">На главную</a></p>
    </body>
    </html>
    """
    return HttpResponse(html)


def payments_cancel_view(_request):
    html = """
    <!doctype html>
    <html lang="ru">
    <head>
      <meta charset="utf-8" />
      <title>Оплата отменена</title>
      <style>body{font-family:system-ui,sans-serif;margin:2rem;} a{color:#0a62c9;}</style>
    </head>
    <body>
      <h1>Оплата отменена ❌</h1>
      <p>Вы можете повторить попытку позже.</p>
      <p><a href="/">На главную</a></p>
    </body>
    </html>
    """
    return HttpResponse(html)


def healthz_view(_request):
    return HttpResponse("ok", content_type="text/plain")


def readyz_view(_request):
    # Simple readiness: check DB connection
    try:
        connection = connections['default']
        cursor = connection.cursor()
        cursor.execute('SELECT 1;')
    except OperationalError:
        return HttpResponse('db:unavailable', status=503, content_type='text/plain')
    return HttpResponse('ready', content_type='text/plain')

urlpatterns = [
    # Стартовая страница со ссылками
    path('', index_view, name='index'),

    path('admin/', admin.site.urls),
    # Подключаем урлы приложений под /api/
    path('api/', include('lms.urls')),
    path('api/users/', include('users.urls')),
    # Авторизация для браузируемого API (даёт ссылки Login/Logout в правом верхнем углу)
    path('api/auth/', include('rest_framework.urls')),

    # JWT авторизация
    path('api/auth/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/jwt/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # OpenAPI схема и документация
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Явные рендеры для удобного просмотра в браузере
    path(
        'api/schema/json/',
        SpectacularAPIView.as_view(renderer_classes=[OpenApiJsonRenderer]),
        name='schema-json',
    ),
    path(
        'api/schema/yaml/',
        SpectacularAPIView.as_view(renderer_classes=[OpenApiYamlRenderer]),
        name='schema-yaml',
    ),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Простые страницы для редиректов Stripe Checkout
    path('payments/success', payments_success_view, name='payments-success'),
    path('payments/cancel', payments_cancel_view, name='payments-cancel'),
    # Health endpoints
    path('healthz', healthz_view, name='healthz'),
    path('readyz', readyz_view, name='readyz'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Expose Prometheus metrics if enabled
try:
    if 'django_prometheus' in settings.INSTALLED_APPS:
        urlpatterns += [path('', include('django_prometheus.urls'))]
except Exception as err:  # nosec B110 - intentionally handled: optional dependency
    # If django_prometheus isn't installed, just skip adding metrics URLs but log the reason
    _logging.getLogger(__name__).debug('Prometheus URLs not added: %s', err)
