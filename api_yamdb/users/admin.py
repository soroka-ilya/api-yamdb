from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'role',
        'is_staff',
        'is_superuser',
    )
    list_filter = (
        'role',
        'is_staff',
        'is_superuser',
        'is_active',
    )
    search_fields = (
        'username',
        'email',
    )
    ordering = ('id',)

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('bio', 'role')}),
    )
