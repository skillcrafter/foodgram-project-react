from rest_framework import serializers

from api.validators import username_validator
from recipes.models import Recipe
from users.models import Subscribe, User

from foodgram.constants import MAX_NAME_LENGTH


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User"""

    username = serializers.CharField(
        max_length=MAX_NAME_LENGTH,
        validators=[username_validator]
    )
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Получение информации о подписке."""
        user = self.context.get('request').user
        return user.is_authenticated and user.subscriber.filter(
            author=obj.id
        ).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionSerializer(UserSerializer):
    """Сериализатор подписок"""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        ]
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = (
            'user',
            'author'
        )

    # def validate(self, data):
    #     user = self.context['request'].user
    #     author = data['author']
    #     if user == author:
    #         raise serializers.ValidationError("Вы не можете подписаться на "
    #                                           "самого себя")
    #     return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionSerializer(
            instance.author,
            context={'request': request}
        ).data
