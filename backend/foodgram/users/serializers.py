from django.core.validators import RegexValidator
from rest_framework import serializers

from recipes.models import Recipe
from users.models import Subscribe, User


class UserSerializer(serializers.ModelSerializer):
    # Сериализатор для модели User

    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Invalid username format',
                code='invalid_username'
            )
        ]
    )
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        """Получение информации о подписке."""
        user = self.context.get('request').user
        return user.is_authenticated and user.subscriber.filter(
            author=obj.id
        ).exists() or False

    def to_representation(self, instance):
        # print('!!!!!!!!instance = ', instance)
        """Преобразование объекта модели в представление."""
        representation = super().to_representation(instance)
        if instance == self.context.get('request').user:
            representation['is_subscribed'] = False
        return representation

    # БЫЛО
    # def get_is_subscribed(self, obj):
    #     request = self.context.get('request')
    #     if request:
    #         user = request.user
    #         if user.is_authenticated:
    #             return user.subscriber.filter(author=obj.author).exists()
    #     return False
        # request = self.context.get('request')
        # if (request is None or
        #         request.user.is_anonymous):
        #     return False
        # return Subscribe.objects.filter(
        #     user=request.user,
        #     author=obj
        # ).exists()

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     data['is_subscribed'] = self.get_is_subscribed(instance)
    #     return data


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

    # def get_is_subscribed(self, obj):
    #     request = self.context.get('request')
    #     if (request is None or
    #             request.user.is_anonymous):
    #         return False
    #     return Subscribe.objects.filter(
    #         user=request.user,
    #         author=obj
    #     ).exists()

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


    # recipes = SerializerMethodField(method_name='get_recipe')
    # recipes_count = SerializerMethodField(
    #     method_name='get_recipes_count'
    # )
    #
    # class Meta(UserSerializer.Meta):
    #     fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')
    #     read_only_fields = ('email', 'username', 'first_name', 'last_name')
    #
    # def get_recipe(self, obj):
    #     print('!!!!! obj = ', obj)
    #     request = self.context.get('request')
    #     print('!!!!! context = ', request)
    #     limit = request.GET.get('recipes_limit')
    #     recipes = obj.recipe.all()
    #     if limit and limit.isdigit():
    #         recipes = recipes[:int(limit)]
    #     serialized_recipes = RecipeShortSerializer(
    #         recipes,
    #         many=True,
    #         context=self.context
    #     ).data
    #     return serialized_recipes
    #
    # def get_recipes_count(self, obj):
    #     return Recipe.objects.filter(author=obj).count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = (
            'user',
            'author'
        )

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionSerializer(
            instance.author,
            context={'request': request}
        ).data

    # def validate(self, attrs):
    #     user = attrs['user']
    #     author = attrs['author']
    #     if not User.objects.filter(pk=author.pk).exists():
    #         raise ValidationError({'author': 'Автор не найден.'})
    #     if user == author:
    #         raise ValidationError(
    #             {'author': 'Нельзя подписаться на себя.'}
    #         )
    #     if Subscribe.objects.filter(author=author).exists():
    #         raise ValidationError(
    #             {'author': 'Уже подписан.'}
    #         )
    #
    #     return attrs

    # def to_representation(self, instance):
    #     print('!!!!!!!!!! instance = ', instance)
    #     return SubscriptionSerializer(
    #         instance.author,
    #         context=self.context
    #     ).data

    # validators = [
    #     UniqueTogetherValidator(
    #         queryset=Subscription.objects.all(),
    #         fields=['user', 'author'],
    #     )
    # ]




