from django.urls import path

from .views import (
    LessonListCreateAPIView,
    LessonRetrieveUpdateDestroyAPIView,
)


urlpatterns = [
    # Эндпоинты уроков (Generic CBV)
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonRetrieveUpdateDestroyAPIView.as_view(), name='lesson-detail'),
]
