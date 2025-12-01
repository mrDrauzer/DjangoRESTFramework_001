from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny

from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # Фильтрация/поиск/сортировка
    filterset_fields = ['title']
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title']
    ordering = ['id']
    permission_classes = [AllowAny]


class LessonListCreateAPIView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Фильтрация/поиск/сортировка
    filterset_fields = ['course', 'title']
    search_fields = ['title', 'description', 'video_url']
    ordering_fields = ['id', 'title', 'course']
    ordering = ['id']
    permission_classes = [AllowAny]


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [AllowAny]
