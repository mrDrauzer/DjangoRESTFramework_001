from rest_framework import viewsets, generics, status
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from django_filters import rest_framework as filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import User, Payment
from .serializers import (
    UserSerializer,
    PaymentSerializer,
    RegisterSerializer,
    PaymentCreateSerializer,
)
from .permissions import IsSelfOrReadOnly
from . import stripe_service
from .stripe_service import StripeServiceError


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


@extend_schema(
    tags=['payments', 'stripe'],
    summary='Создать платёж (Stripe Checkout)',
    description=(
        'Создаёт сущности в Stripe (Product, Price, Checkout Session) и возвращает ссылку на оплату.\n\n'
        'В теле запроса укажите либо course_id, либо lesson_id, а также сумму. '
        'Сумма передаётся в основных единицах валюты (рубли/доллары), в Stripe она будет преобразована в копейки/центы.'
    ),
    request=PaymentCreateSerializer,
    responses={201: PaymentSerializer},
)
class PaymentCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        course = data.get('course')
        lesson = data.get('lesson')
        amount = data['amount']

        # Создаём локальную запись Payment
        payment = Payment.objects.create(
            user=user,
            course=course,
            lesson=lesson,
            amount=amount,
            method=Payment.Method.STRIPE,
        )

        # Формируем имя продукта
        target_name = course.title if course else lesson.title
        metadata = {
            'payment_id': str(payment.id),
            'user_id': str(user.id),
            'type': 'course' if course else 'lesson',
            'target_id': str(course.id if course else lesson.id),
        }

        # В Stripe: Product -> Price -> Checkout Session
        try:
            product = stripe_service.create_product(name=target_name, metadata=metadata)
            price = stripe_service.create_price(product_id=product['id'], amount=amount)
            session = stripe_service.create_checkout_session(price_id=price['id'])
        except StripeServiceError as e:
            # Удалим незавершённый платёж, чтобы не копить мусор
            payment.delete()
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Сохраняем данные Stripe
        payment.stripe_product_id = product['id']
        payment.stripe_price_id = price['id']
        payment.stripe_session_id = session['id']
        payment.stripe_checkout_url = session.get('url')
        payment.stripe_status = session.get('status')
        payment.save(update_fields=[
            'stripe_product_id', 'stripe_price_id', 'stripe_session_id', 'stripe_checkout_url', 'stripe_status'
        ])

        resp = PaymentSerializer(payment).data
        headers = self.get_success_headers(resp)
        return Response(resp, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    tags=['payments', 'stripe'],
    summary='Проверить статус платежа (Stripe Session Retrieve)',
    description='Возвращает и обновляет статус платежа по его ID, используя сохранённый stripe_session_id.',
    responses={200: PaymentSerializer},
)
class PaymentStatusAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()

    def retrieve(self, request, *args, **kwargs):
        payment: Payment = self.get_object()
        # Проверяем доступ: владелец или модератор/персонал
        user = request.user
        if not (
            payment.user_id == user.id or
            user.groups.filter(name='moderators').exists() or
            user.is_staff or user.is_superuser
        ):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not payment.stripe_session_id:
            return Response(
                {'detail': 'Для данного платежа не создана Stripe сессия.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = stripe_service.retrieve_session(payment.stripe_session_id)
        except StripeServiceError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        payment.stripe_status = session.get('status')
        payment.save(update_fields=['stripe_status'])
        return Response(PaymentSerializer(payment).data)
