from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    PaymentListAPIView,
    RegisterAPIView,
    PaymentCreateAPIView,
    PaymentStatusAPIView,
)


router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # Явные пути объявляем ДО include(router), чтобы они не перехватывались как detail у UserViewSet
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
    path('payments/create/', PaymentCreateAPIView.as_view(), name='payment-create'),
    path('payments/<int:pk>/status/', PaymentStatusAPIView.as_view(), name='payment-status'),
    path('', include(router.urls)),
]
