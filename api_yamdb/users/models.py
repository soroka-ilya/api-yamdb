from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models

from core.constants import MAX_CONFIRMATION_CODE_LENGTH, MAX_ROLE_LENGTH


def validate_username_not_me(value):
    if value.lower() == 'me':
        raise ValidationError(
            'Использовать имя "me" в качестве username запрещено.'
        )


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    ROLES = (
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    )

    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[UnicodeUsernameValidator(), validate_username_not_me],
    )
    email = models.EmailField(
        'email address',
        unique=True,
    )
    bio = models.TextField(
        'Биография',
        blank=True,
    )
    role = models.CharField(
        'Роль',
        max_length=MAX_ROLE_LENGTH,
        choices=ROLES,
        default=USER,
    )
    confirmation_code = models.CharField(
        'Код подтверждения',
        max_length=MAX_CONFIRMATION_CODE_LENGTH,
        blank=True,
    )

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR or self.is_superuser

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
