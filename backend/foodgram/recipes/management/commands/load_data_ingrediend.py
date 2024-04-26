import json
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузить данные об ингредиентах в базу данных'

    def handle(self, *args, **options):
        try:
            file_path = 'data/ingredients.json'
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                successfully_loaded = set()
                for item in data:
                    try:
                        ingredient, created = Ingredient.objects.get_or_create(
                            **item)
                        if created:
                            successfully_loaded.add((item['name'],
                                                     item['measurement_unit']))
                            self.stdout.write(self.style.SUCCESS(
                                f'Ингредиенты "{ingredient}" '
                                f'успешно добавлены'))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(
                            f'Ошибка при импорте ингредиента:'
                            f' {e}"{ingredient}"'))
            duplicates = [item for item in data if (item['name'],
                                                    item['measurement_unit'])
                          not in successfully_loaded]
            if duplicates:
                self.stdout.write(self.style.WARNING(
                    f'Следующие ингредиенты не были '
                    f'загружены из-за дубликатов: {duplicates}'))
        except FileNotFoundError:
            raise CommandError('Файл с данными не найден')
