import re

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.serializers import ValidationError

from .fields import Base64ImageField, Hex2NameColor
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    ShoppingCart,
    Tag,
)

from users.serializers import UserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipesIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'name',
            'amount',
            'measurement_unit'
        ]


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """

    id = serializers.IntegerField()
    # amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'amount'
        ]


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для создания рецепта """

    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipesIngredientsSerializer(many=True, source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    # def get_ingredients(self, obj):
    #     ingredients = RecipeIngredient.objects.filter(recipe=obj)
    #     return RecipesIngredientsSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj.id  # Замечание 238 (api->view.py)
            #  Заменен obj на obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj.id  # Замечание 238 (api->view.py)
            #  Заменен obj на obj.id
        ).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о рецептах."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины покупок."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже добавлен в список покупок.',
            )
        ]

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о рецептах."""
    author = UserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        ]

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        cooking_time = data.get('cooking_time')

        if not ingredients or not tags or not cooking_time:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле не может быть пустым'}
            )

        existing_ingredient_ids = set(
            Ingredient.objects.values_list('id', flat=True)
        )

        for ingredient_data in ingredients:
            ingredient_id = ingredient_data.get('id')
            if ingredient_id not in existing_ingredient_ids:
                raise serializers.ValidationError(
                    {'ingredients': f'Ингредиент с '
                                    f'id={ingredient_id} не существует'}
                )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Теги не должны повторяться.")

        id_list = []
        for i in ingredients:
            amount = i['amount']
            if int(amount) < 1:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
            if i['id'] in id_list:
                raise serializers.ValidationError({
                    'ingredient': 'Ингредиенты должны быть уникальными!'
                })
            id_list.append(i['id'])

        return data

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = [
            RecipeIngredient(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create_tags(self, tags, recipe):
        recipe_tags = [
            RecipeTag(recipe=recipe, tag=tag)
            for tag in tags
        ]
        RecipeTag.objects.bulk_create(recipe_tags)
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        request = self.context.get('request')
        # if instance.author == request.user and 'tags' not in validated_data:
        #     raise ValidationError(
        #         "Поле 'tags' обязательно для обновления рецепта."
        #     )
        # if not request.user.is_authenticated:
        #     raise AuthenticationFailed(
        #         "Требуется аутентификация для обновления рецепта."
        #     )
        # if instance.author != request.user:
        #     raise PermissionDenied(
        #         "Вы не являетесь автором этого рецепта.")

        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
        # instance.name = validated_data.pop('name')
        # instance.text = validated_data.pop('text')
        # if validated_data.get('image'):
        #     instance.image = validated_data.pop('image')
        # instance.cooking_time = validated_data.pop('cooking_time')
        return super().update(instance, validated_data)
        instance.save()
        return instance


    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteListSerializer(serializers.ModelSerializer):
    """Cериализатор сведений об избранных рецептах."""

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """Cериализатор добавления в избранное."""

    class Meta:
        model = Favorite
        fields = [
            'user',
            'recipe'
        ]

        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=[
                    'user',
                    'recipe'
                ],
                message='Рецепт уже добавлен в список избранного.',
            )
        ]

    def to_representation(self, instance):
        return FavoriteListSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data
