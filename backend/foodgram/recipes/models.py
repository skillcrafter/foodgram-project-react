import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from foodgram.constants import MIN_VALUE, message

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(
        unique=True,
        max_length=128,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=128,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    # Админка Спринт 6/12: 6 спринт → Тема 3/6: Админ-зона Django → Урок 2/3
    # вывод записей так, чтобы в качестве заголовка показывалось название
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тегов"""
    name = models.CharField(
        unique=True,
        max_length=128,
        verbose_name='Тег',
    )
    color = models.CharField(unique=True, max_length=16, verbose_name='Цвет', default='#c8ff3b')
    slug = models.SlugField(
        unique=True,
        max_length=100,
        default=uuid.uuid1,
        verbose_name='Слаг', )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    # Админка Спринт 6/12: 6 спринт → Тема 3/6: Админ-зона Django → Урок 2/3
    # вывод записей так, чтобы в качестве заголовка показывалось название
    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='recipes',
        verbose_name='Автор записи',
    )
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    image = models.ImageField(
        'Фото',
        upload_to='recipes/images/'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Введите описание рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        # related_name='recipes',
        # to=Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (в минутах)",
        validators=[MinValueValidator(MIN_VALUE, message=message)],
        default=1,
    )
    tags = models.ManyToManyField(
        Tag,
        # through='RecipeTag',
        related_name='recipes',
        verbose_name='Тег',
    )

    # pub_date = models.DateTimeField(
    #     verbose_name='Дата публикации',
    #     auto_now_add=True
    # )
    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    # Админка Спринт 6/12: 6 спринт → Тема 3/6: Админ-зона Django → Урок 2/3
    # вывод записей так, чтобы в качестве заголовка показывалось название
    # def __str__(self):        # Версия Оли
    #     return f'{self.author} - {self.name}'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        default=0
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return (
            f'{self.recipe.name}: '
            f'{self.ingredient.name} - '
            f'{self.amount}/'
            f'{self.ingredient.measurement_unit}'
        )

    # Версия Вадима
    # def __str__(self):
    #     return (
    #         f'{self.recipe.name}: '
    #         f'{self.ingredient.name} - '
    #         f'{self.amount}/'
    #     )


class Favorite(models.Model):
    """Модель Избранное."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='favorites',
        verbose_name='Автор записи',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    """Модель Корзина покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='ShoppingCarts',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ShoppingCarts',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_ShoppingCart_unique'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class RecipeTag(models.Model):
    """ Модель связи тега и рецепта. """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='recipe_tag_unique'
            )
        ]