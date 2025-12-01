from rest_framework import serializers
from .models import User, Payment
from lms.models import Course, Lesson


class PaymentInlineCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title']


class PaymentInlineLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'course']


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    course = PaymentInlineCourseSerializer(read_only=True)
    lesson = PaymentInlineLessonSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_email', 'paid_at', 'course', 'lesson', 'amount', 'method']
        read_only_fields = ['paid_at']


class UserPaymentSerializer(serializers.ModelSerializer):
    """Упрощённый вывод платежа для профиля пользователя."""
    class Meta:
        model = Payment
        fields = ['id', 'paid_at', 'amount', 'method', 'course', 'lesson']


class UserSerializer(serializers.ModelSerializer):
    payments = UserPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'date_joined', 'payments']
        read_only_fields = ['date_joined']
