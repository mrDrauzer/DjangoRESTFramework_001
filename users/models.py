from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from lms.models import Course, Lesson


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email должен быть указан')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('Email', unique=True)
    first_name = models.CharField('Имя', max_length=150, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    phone = models.CharField('Телефон', max_length=32, blank=True)
    city = models.CharField('Город', max_length=128, blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.email


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'cash', 'Наличные'
        TRANSFER = 'transfer', 'Перевод на счёт'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments',
                             verbose_name='Пользователь')
    paid_at = models.DateTimeField('Дата оплаты', auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True,
                               related_name='payments', verbose_name='Оплаченный курс')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True,
                               related_name='payments', verbose_name='Отдельно оплаченный урок')
    amount = models.DecimalField('Сумма оплаты', max_digits=10, decimal_places=2)
    method = models.CharField('Способ оплаты', max_length=16, choices=Method.choices)

    class Meta:
        verbose_name = 'платёж'
        verbose_name_plural = 'платежи'
        ordering = ['-paid_at']

    def __str__(self):
        target = self.course or self.lesson
        return f"{self.user} → {target} : {self.amount} ({self.get_method_display()})"

    def clean(self):
        super().clean()
        # Должен быть указан ровно один из course/lesson
        has_course = self.course is not None
        has_lesson = self.lesson is not None
        if has_course and has_lesson:
            raise ValidationError('Нужно указать либо курс, либо урок, но не оба одновременно.')
        if not has_course and not has_lesson:
            raise ValidationError('Нужно указать оплаченный курс или отдельно оплаченный урок.')

    def save(self, *args, **kwargs):
        # Гарантируем валидацию бизнес-правил при любом сохранении
        self.full_clean()
        return super().save(*args, **kwargs)
