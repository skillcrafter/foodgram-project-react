from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Загрузить данные о тегах в базу данных'

    def handle(self, *args, **options):
        data = [
            {'name': 'Завтрак', 'color': '#2dbd4f', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#2d8fbd', 'slug': 'dinner'},
            {'name': 'Ужин', 'color': '#cf88db', 'slug': 'supper'},
        ]
        for item in data:
            tag, created = Tag.objects.get_or_create(**item)
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Тег "{tag}" успешно создан'
                ))
            else:
                self.stdout.write(
                    self.style.WARNING(f'Тег "{tag}" уже существует'))