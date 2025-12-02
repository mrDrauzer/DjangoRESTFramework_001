from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated

from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModer, IsOwner


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # Фильтрация/поиск/сортировка
    filterset_fields = ['title']
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title']
    ordering = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # Модератор видит все, остальные — только свои объекты
        if user and user.is_authenticated and (
            user.is_staff or user.is_superuser or user.groups.filter(name='moderators').exists()
        ):
            return qs
        return qs.filter(owner=user)

    def get_permissions(self):
        # Разграничение по action:
        # - create: разрешено только НЕ модераторам (модераторам запрещено создавать)
        # - destroy: только владельцу (модераторам запрещено удалять)
        # - update/partial_update: владелец ИЛИ модератор
        # - list/retrieve: любой аутентифицированный; ограничения обеспечиваются queryset
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, ~IsModer]
        elif self.action == 'destroy':
            self.permission_classes = [IsAuthenticated, IsOwner]
        elif self.action in ('update', 'partial_update'):
            self.permission_classes = [IsAuthenticated, IsModer | IsOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return [perm() for perm in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    # Фильтрация/поиск/сортировка
    filterset_fields = ['course', 'title']
    search_fields = ['title', 'description', 'video_url']
    ordering_fields = ['id', 'title', 'course']
    ordering = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Lesson.objects.all()
        if user and user.is_authenticated and (
            user.is_staff or user.is_superuser or user.groups.filter(name='moderators').exists()
        ):
            return qs
        return qs.filter(owner=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, ~IsModer]
        else:
            self.permission_classes = [IsAuthenticated]
        return [perm() for perm in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Lesson.objects.all()
        if user and user.is_authenticated and (
            user.is_staff or user.is_superuser or user.groups.filter(name='moderators').exists()
        ):
            return qs
        return qs.filter(owner=user)

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            self.permission_classes = [IsAuthenticated, IsModer | IsOwner]
        elif self.request.method == 'DELETE':
            self.permission_classes = [IsAuthenticated, IsOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return [perm() for perm in self.permission_classes]
