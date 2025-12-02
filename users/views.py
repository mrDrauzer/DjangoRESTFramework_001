from rest_framework import viewsets, generics
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from django_filters import rest_framework as filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import User, Payment
from .serializers import UserSerializer, PaymentSerializer, RegisterSerializer
from .permissions import IsSelfOrReadOnly


class UserViewSet(ListModelMixin, RetrieveModelMixin, UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Чтение профилей доступно всем авторизованным; изменять можно только свой профиль
        self.permission_classes = [IsAuthenticated, IsSelfOrReadOnly]
        return [perm() for perm in self.permission_classes]


@extend_schema(
    tags=['auth', 'users'],
    summary='Регистрация нового пользователя',
    description='Создаёт учётную запись по email и паролю. Доступно без авторизации.',
    auth=None,
    examples=[
        OpenApiExample(
            'Пример запроса',
            value={
                'email': 'user@example.com',
                'password': 'Secret1234',
                'first_name': 'Ivan',
                'last_name': 'Petrov'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Пример ответа',
            value={
                'id': 1,
                'email': 'user@example.com',
                'first_name': 'Ivan',
                'last_name': 'Petrov'
            },
            response_only=True,
        ),
    ],
)
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class PaymentFilter(filters.FilterSet):
    course = filters.NumberFilter(field_name='course__id', lookup_expr='exact')
    lesson = filters.NumberFilter(field_name='lesson__id', lookup_expr='exact')
    method = filters.CharFilter(field_name='method', lookup_expr='exact')

    class Meta:
        model = Payment
        fields = ['course', 'lesson', 'method']


class PaymentListAPIView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    filterset_class = PaymentFilter
    ordering_fields = ['paid_at', 'amount', 'id']
    ordering = ['-paid_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related('user', 'course', 'lesson').all()
        if user.groups.filter(name='moderators').exists() or user.is_staff or user.is_superuser:
            return qs
        return qs.filter(user=user)
