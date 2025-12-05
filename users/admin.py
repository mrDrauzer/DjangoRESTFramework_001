from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Payment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'city', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('date_joined',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'paid_at', 'course', 'lesson', 'amount', 'method', 'stripe_status'
    )
    list_filter = ('method', 'paid_at', 'stripe_status')
    search_fields = ('user__email', 'course__title', 'lesson__title', 'stripe_session_id')
    autocomplete_fields = ('user', 'course', 'lesson')
    readonly_fields = (
        'stripe_product_id', 'stripe_price_id', 'stripe_session_id', 'stripe_checkout_url', 'stripe_status'
    )
