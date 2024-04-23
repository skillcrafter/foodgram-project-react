import json
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузить данные о ингредиентах в базу данных'

    def handle(self, *args, **options):
        try:
            file_path = 'data/ingredients.json'
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    ingredient, created = Ingredient.objects.get_or_create(
                        **item)
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'Ингредиенты "{ingredient}" успешно добавлены'))
                    # else:
                    #     self.stdout.write(self.style.WARNING(
                    #         f'Ингредиент "{ingredient}" уже существует'))

        except FileNotFoundError:
            raise CommandError('Файл с данными не найден')
        except Exception as e:
            raise CommandError(f'Ошибка при импорте данных: {e}')