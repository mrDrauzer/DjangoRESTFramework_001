from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, PaymentListAPIView, RegisterAPIView


router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
]
