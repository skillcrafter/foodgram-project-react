from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models

from foodgram.constants import (MAX_NAME_LENGTH,
                                MAX_EMAIL_LENGTH)


class User(AbstractUser):
    """Модель пользователя"""
    REQUIRED_FIELDS = ('username', 'last_name', 'first_name',)
    USERNAME_FIELD = 'email'

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
    )

    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=MAX_NAME_LENGTH,
        validators=[UnicodeUsernameValidator()],
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )

    first_name = models.CharField(verbose_name='Имя',
                                  max_length=MAX_NAME_LENGTH,
                                  )
    last_name = models.CharField(verbose_name='Фамилия',
                                 max_length=MAX_NAME_LENGTH)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    def clean(self) -> None:
        if self.username == "me":
            raise ValidationError(f'Использование имени '
                                  f'"{self.username}" недопустимо')
        return super().clean()


class Subscribe(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(User, verbose_name='Подписчик',
                             on_delete=models.CASCADE,
                             related_name="subscriber")
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE,
                               related_name="subscribing")

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписываться на самого себя.')

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
