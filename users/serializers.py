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
        fields = [
            'id', 'user', 'user_email', 'paid_at', 'course', 'lesson', 'amount', 'method',
            'stripe_product_id', 'stripe_price_id', 'stripe_session_id',
            'stripe_checkout_url', 'stripe_status'
        ]
        read_only_fields = ['paid_at', 'stripe_product_id', 'stripe_price_id', 'stripe_session_id',
                            'stripe_checkout_url', 'stripe_status']


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


class PaymentCreateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        course_id = attrs.get('course_id')
        lesson_id = attrs.get('lesson_id')
        if bool(course_id) == bool(lesson_id):
            raise serializers.ValidationError('Нужно указать либо course_id, либо lesson_id (ровно один).')
        # Ensure object exists
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist as err:
                raise serializers.ValidationError('Указанный курс не найден.') from err
            attrs['course'] = course
        if lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
            except Lesson.DoesNotExist as err:
                raise serializers.ValidationError('Указанный урок не найден.') from err
            attrs['lesson'] = lesson
        amount = attrs.get('amount')
        if amount is None or amount <= 0:
            raise serializers.ValidationError('Сумма должна быть больше 0.')
        return attrs
