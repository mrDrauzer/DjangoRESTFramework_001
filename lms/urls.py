from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LessonListCreateAPIView,
    LessonRetrieveUpdateDestroyAPIView,
    CourseViewSet,
    SubscriptionToggleAPIView,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    # Управление подпиской на курс — важно объявить ДО роутера, чтобы избежать перехвата `courses/<pk>`
    path('courses/subscribe/', SubscriptionToggleAPIView.as_view(), name='course-subscribe-toggle'),
    # Роутер для CourseViewSet
    path('', include(router.urls)),
    # Эндпоинты уроков (Generic CBV)
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonRetrieveUpdateDestroyAPIView.as_view(), name='lesson-detail'),
]
