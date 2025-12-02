from rest_framework import serializers
from django.contrib.auth import get_user_model
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
    payments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'date_joined', 'payments']
        read_only_fields = ['date_joined']

    def get_payments(self, obj):
        # Показываем историю платежей только владельцу профиля
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.pk == obj.pk:
            return UserPaymentSerializer(obj.payments.all(), many=True).data
        return []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.pk != instance.pk:
            # Скрываем фамилию для чужого профиля согласно дополнительному заданию
            data.pop('last_name', None)
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        # create_user уже хэширует пароль, передаём его прямо сюда
        password = validated_data.pop('password')
        return get_user_model().objects.create_user(password=password, **validated_data)
