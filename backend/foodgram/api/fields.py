import base64
from django.core.files.base import ContentFile

from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Кастомный сериализатор для работы с изображением."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name='temp.' + ext
            )
        return super().to_internal_value(data)


class Hex2NameColor(serializers.Field):
    """Сериализатор для проверки формата цвета (hex) """

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if not re.match(r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', data):
            raise serializers.ValidationError('Неверный формат RGB цвета')
        return data

