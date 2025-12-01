from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import HttpResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
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
        <li><a href="/api/auth/login/">API Login</a> / <a href="/api/auth/logout/">Logout</a></li>
      </ul>
      <p>Подсказка: для авторизации используйте учётную запись суперпользователя, созданную через <code>createsuperuser</code>.</p>
    </body>
    </html>
    """
    return HttpResponse(html)

urlpatterns = [
    # Стартовая страница со ссылками
    path('', index_view, name='index'),

    path('admin/', admin.site.urls),
    # Подключаем урлы приложений под /api/
    path('api/', include('lms.urls')),
    path('api/users/', include('users.urls')),
    # Авторизация для браузируемого API (даёт ссылки Login/Logout в правом верхнем углу)
    path('api/auth/', include('rest_framework.urls')),

    # OpenAPI схема и документация
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
