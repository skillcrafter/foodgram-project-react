from django.db.models import Sum
from djoser import views as djoser_views
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import User, Subscribe
from .filters import RecipeFilter
from .paginator import CustomPagination
from .permissions import AutherOrReadOnly
from .serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserSerializer,
    SubscriptionSerializer,
    SubscribeSerializer,
)


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для пользователей."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in (
                'subscribe',
                'subscriptions',
                'destroy',
                'me'):
            permission_classes = (IsAuthenticated,)
        else:
            permission_classes = (AllowAny,)
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        serializer_class=SubscribeSerializer
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        subscription = Subscribe.objects.filter(
            user=user,
            author=author
        )
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Вы не можете подписаться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription, created = Subscribe.objects.get_or_create(
                user=user,
                author=author
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not subscription.exists():
            return Response(
                {'error': 'Вы не подписаны на этого автора!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientsViewSet(ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all().order_by('pk')

    def list(self, request, *args, **kwargs):
        name_starts_with = request.query_params.get('name', '')
        queryset = self.queryset
        if name_starts_with:
            queryset = queryset.filter(name__istartswith=name_starts_with)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    permission_classes = (AutherOrReadOnly,)
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        author_id = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if tags:
            tag_filters = {'tags__slug__in': tags}
            queryset = queryset.filter(**tag_filters)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def get_recipe_or_error_response(self, pk, method):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            if method == 'POST':
                return Response(
                    {'error': 'Рецепт не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': 'Рецепт не существует.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return recipe

    def action_request(self, request, serializer_class, model_class, pk=None):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            if request.method == 'POST':
                return Response(
                    {'error': 'Рецепт не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': 'Рецепт не существует.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        if request.method == 'POST':
            serializer = serializer_class(
                data={
                    'user': request.user.id,
                    'recipe': pk
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        try:
            instance = model_class.objects.get(
                user=request.user,
                recipe=recipe
            )
            instance.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        except model_class.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self.action_request(
            request,
            ShoppingCartSerializer,
            ShoppingCart,
            pk
        )

    def generate_shopping_list(self, user):
        recipes = ShoppingCart.objects.filter(
            user=user
        ).values_list('recipe', flat=True)

        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(
                total_amount=Sum('amount')
            )
        )

        shopping_list = {}
        for ingredient in ingredients:
            ingredient_name = ingredient['ingredient__name']
            total_amount = ingredient['total_amount']
            measurement_unit = ingredient['ingredient__measurement_unit']
            shopping_list[ingredient_name] = {
                'amount': total_amount,
                'measurement_unit': measurement_unit
            }

        return shopping_list

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',

    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list = self.generate_shopping_list(user)
        shopping_list_text = ''
        for ingredient, data in shopping_list.items():
            shopping_list_text += (f"{ingredient} "
                                   f"({data['measurement_unit']}) "
                                   f"— {data['amount']}\n")
        response = HttpResponse(
            shopping_list_text,
            content_type='text/plain'
        )
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        return self.action_request(
            request,
            FavoriteSerializer,
            Favorite,
            pk
        )


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
