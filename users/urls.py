from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, PaymentListAPIView


router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
]
