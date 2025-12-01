from django.db import models


class Course(models.Model):
    title = models.CharField('Название', max_length=255)
    preview = models.ImageField('Превью', upload_to='courses/previews/', blank=True, null=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'курс'
        verbose_name_plural = 'курсы'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name='Курс')
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    preview = models.ImageField('Превью', upload_to='lessons/previews/', blank=True, null=True)
    video_url = models.URLField('Ссылка на видео', blank=True)

    class Meta:
        verbose_name = 'урок'
        verbose_name_plural = 'уроки'

    def __str__(self):
        return f"{self.title} ({self.course})"
