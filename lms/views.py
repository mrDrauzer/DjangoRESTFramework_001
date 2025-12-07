from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Course, Lesson, Subscription
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModer, IsOwner
from .paginators import DefaultPageNumberPagination
from .tasks import send_course_update_email


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = DefaultPageNumberPagination
    # Фильтрация/поиск/сортировка
    filterset_fields = ['title']
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title']
    ordering = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # Модератор видит всё. Для списка ограничиваем обычных пользователей своими объектами.
        is_moder = (
            user
            and user.is_authenticated
            and (
                user.is_staff
                or user.is_superuser
                or user.groups.filter(name='moderators').exists()
            )
        )
        if getattr(self, 'action', None) == 'list':
            return qs if is_moder else qs.filter(owner=user)
        # Для detail/изменений — полный queryset; ограничения обеспечат пермишены (403 вместо 404)
        return qs

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

    def perform_update(self, serializer):
        course = serializer.save()
        # Асинхронная рассылка об обновлении курса
        try:
            send_course_update_email.delay(course.id, updated_kind='course')
        except Exception:
            # В тестовой/локальной среде без Celery worker просто игнорируем ошибку вызова
            pass


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    pagination_class = DefaultPageNumberPagination
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
        # Для detail-операций возвращаем полный queryset; доступ ограничивается пермишенами
        return Lesson.objects.all()

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            self.permission_classes = [IsAuthenticated, IsModer | IsOwner]
        elif self.request.method == 'DELETE':
            self.permission_classes = [IsAuthenticated, IsOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return [perm() for perm in self.permission_classes]

    def perform_update(self, serializer):
        lesson = serializer.save()
        # Помечаем курс как обновлённый и отправляем уведомление подписчикам курса
        try:
            # Сначала отправим уведомление (чтобы троттлинг по updated_at не сработал преждевременно)
            send_course_update_email.delay(lesson.course_id, updated_kind='lesson')
            # Затем обновим updated_at у курса, чтобы было видно время изменения через урок
            Course.objects.filter(pk=lesson.course_id).update(updated_at=timezone.now())
        except Exception:
            pass


class SubscriptionToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course_id')
        course_item = get_object_or_404(Course, pk=course_id)

        subs_qs = Subscription.objects.filter(user=user, course=course_item)
        if subs_qs.exists():
            subs_qs.delete()
            message = 'подписка удалена'
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = 'подписка добавлена'

        return Response({"message": message})
