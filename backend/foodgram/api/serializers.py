import base64
import re

from django.core.files.base import ContentFile
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, \
    NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.serializers import ValidationError

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


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name='temp.' + ext
            )
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipesIngredientsSerializer(serializers.ModelSerializer):
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
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'amount'
        ]


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if not re.match(r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', data):
            raise serializers.ValidationError('Неверный формат RGB цвета')
        return data


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = [
            'id',
            'name',
            'color',
            'slug'
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для создания рецепта """

    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
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

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipesIngredientsSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     request = self.context.get('request')
    #     if request is not None and not request.user.is_anonymous:
    #         is_in_shopping_cart = ShoppingCart.objects.filter(
    #             user=request.user, recipe_id=instance.id
    #         ).exists()
    #         representation['is_in_shopping_cart'] = is_in_shopping_cart
    #     return representation

class RecipeShortSerializer(serializers.ModelSerializer):
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
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
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
        for i in ingredients:
            ingredient = Ingredient.objects.get(id=i['id'])
            RecipeIngredient.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=i['amount']
            )

    def create_tags(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tag=tag)

    def create(self, validated_data):
        # self.check_authentication()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if instance.author == request.user and 'tags' not in validated_data:
            raise ValidationError(
                "Поле 'tags' обязательно для обновления рецепта."
            )
        if not request.user.is_authenticated:
            raise AuthenticationFailed(
                "Требуется аутентификация для обновления рецепта."
            )
        if instance.author != request.user:
            raise PermissionDenied(
                "Вы не являетесь автором этого рецепта.")

        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image'):
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data

    # def check_authentication(self):
    #     user = self.context.get('request').user
    #     if not user.is_authenticated:
    #         raise AuthenticationFailed(
    #             {"detail": "Незарегистрированные пользователи "
    #                        "не могут создавать рецепты."}
    #         )

    # def validate_tags(self, tags):
    #     print(' 2 !!!!!!!!tags= ', tags)
    #     if len(tags) != len(set(tags)):
    #         raise serializers.ValidationError("Теги не должны повторяться.")
    #     return tags


class FavoriteListSerializer(serializers.ModelSerializer):
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
