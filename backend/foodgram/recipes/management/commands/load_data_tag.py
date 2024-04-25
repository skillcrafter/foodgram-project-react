from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Загрузить данные о тегах в базу данных'

    def handle(self, *args, **options):
        data = [
            {'name': 'Завтрак', 'color': '#c8ff30', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#E26C2D', 'slug': 'dinner'},
            {'name': 'Ужин', 'color': '#c8fz41', 'slug': 'supper'},
        ]
        for item in data:
            tag, created = Tag.objects.get_or_created(**item)
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Тег "{tag}" успешно создан'
                ))
            else:
                self.stdout.write(
                    self.style.WARNING(f'Тег "{tag}" уже существует'))
