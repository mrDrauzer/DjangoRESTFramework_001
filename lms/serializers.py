from rest_framework import serializers
from .models import Course, Lesson
from PIL import Image
import os


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
            f"Недопустимый формат файла: {ext}. Разрешены: {', '.join(sorted(ALLOWED_IMAGE_EXTS))}")
    # Валидация содержимого через Pillow
    try:
        # Важно: сохранить позицию курсора для корректного последующего чтения
        pos = file_obj.tell()
        with Image.open(file_obj) as img:
            if img.format not in ALLOWED_IMAGE_FORMATS:
                raise serializers.ValidationError(
                    f"Недопустимый формат изображения: {img.format}. Разрешены: {', '.join(sorted(ALLOWED_IMAGE_FORMATS))}")
        file_obj.seek(pos)
    except Exception:
        # Если не удалось открыть как изображение
        raise serializers.ValidationError("Файл не является валидным изображением или повреждён")
    return file_obj


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'course', 'title', 'description', 'preview', 'video_url']

    def validate_preview(self, file_obj):
        return _validate_image_file(file_obj)


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'preview', 'description', 'lessons']

    def validate_preview(self, file_obj):
        return _validate_image_file(file_obj)
