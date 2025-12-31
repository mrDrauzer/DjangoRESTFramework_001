from rest_framework import serializers
from .models import Course, Lesson, Subscription
from PIL import Image
import os
from .validators import validate_youtube_url


MAX_IMAGE_MB = 5
ALLOWED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def _validate_image_file(file_obj):
    if not file_obj:
        return file_obj
    # Проверка размера
    size = getattr(file_obj, 'size', None)
    if size is not None and size > MAX_IMAGE_MB * 1024 * 1024:
        raise serializers.ValidationError(f"Размер изображения не должен превышать {MAX_IMAGE_MB} МБ")
    # Проверка расширения
    name = getattr(file_obj, 'name', '')
    ext = os.path.splitext(name)[1].lower()
    if ext and ext not in ALLOWED_IMAGE_EXTS:
        raise serializers.ValidationError(
            (
                f"Недопустимый формат файла: {ext}. "
                f"Разрешены: {', '.join(sorted(ALLOWED_IMAGE_EXTS))}"
            )
        )
    # Валидация содержимого через Pillow
    try:
        # Важно: сохранить позицию курсора для корректного последующего чтения
        pos = file_obj.tell()
        with Image.open(file_obj) as img:
            if img.format not in ALLOWED_IMAGE_FORMATS:
                raise serializers.ValidationError(
                    (
                        f"Недопустимый формат изображения: {img.format}. "
                        f"Разрешены: {', '.join(sorted(ALLOWED_IMAGE_FORMATS))}"
                    )
                )
        file_obj.seek(pos)
    except Exception as err:
        # Если не удалось открыть как изображение
        raise serializers.ValidationError("Файл не является валидным изображением или повреждён") from err
    return file_obj


class LessonSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
    video_url = serializers.URLField(required=False, allow_blank=True, validators=[validate_youtube_url])
    class Meta:
        model = Lesson
        fields = ['id', 'course', 'title', 'description', 'preview', 'video_url', 'owner']

    def validate_preview(self, file_obj):
        return _validate_image_file(file_obj)


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    owner = serializers.ReadOnlyField(source='owner.id')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'preview', 'description', 'owner', 'lessons_count', 'is_subscribed', 'lessons']

    def validate_preview(self, file_obj):
        return _validate_image_file(file_obj)

    def get_lessons_count(self, obj: Course) -> int:
        # Используем аннотированное значение, если оно уже добавлено во вью, иначе считаем напрямую
        count = getattr(obj, 'lessons__count', None)
        if isinstance(count, int):
            return count
        return obj.lessons.count()

    def get_is_subscribed(self, obj: Course) -> bool:
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return Subscription.objects.filter(user=user, course=obj).exists()
