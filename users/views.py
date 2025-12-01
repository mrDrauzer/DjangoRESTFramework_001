from rest_framework import viewsets, generics
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from django_filters import rest_framework as filters
from rest_framework.permissions import AllowAny

from .models import User, Payment
from .serializers import UserSerializer, PaymentSerializer


class UserViewSet(ListModelMixin, RetrieveModelMixin, UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PaymentFilter(filters.FilterSet):
    course = filters.NumberFilter(field_name='course__id', lookup_expr='exact')
    lesson = filters.NumberFilter(field_name='lesson__id', lookup_expr='exact')
    method = filters.CharFilter(field_name='method', lookup_expr='exact')

    class Meta:
        model = Payment
        fields = ['course', 'lesson', 'method']


class PaymentListAPIView(generics.ListAPIView):
    queryset = Payment.objects.select_related('user', 'course', 'lesson').all()
    serializer_class = PaymentSerializer
    filterset_class = PaymentFilter
    ordering_fields = ['paid_at', 'amount', 'id']
    ordering = ['-paid_at']
    permission_classes = [AllowAny]
