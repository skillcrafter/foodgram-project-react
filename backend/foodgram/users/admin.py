from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscribe

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    """Какие поля отображаются на странице списка
      для изменения из интерфейса администратора"""
    list_display = ('id', 'username', 'email', 'first_name', 'last_name',)
    """Поиск по полям"""
    search_fields = ('email', 'username',)
    """ Автоматически добавит фильтр этого поля на стороне администратора"""
    list_filter = ('email', 'username',)
    list_display_links = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            'Персональная информация',
            {'fields': ('first_name', 'last_name', 'email')}
        ),
        (
            'Права доступа',
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (
            'Важные даты',
            {'fields': ('last_login', 'date_joined')}
        )
    )
    empty_value_display = 'Не задано'


class SubscribeAdmin(admin.ModelAdmin):
    """Подписки"""
    list_display = ('id', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
    empty_value_display = 'Не задано'


admin.site.register(Subscribe, SubscribeAdmin)
admin.site.register(User, UserAdmin)
