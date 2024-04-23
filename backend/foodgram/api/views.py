from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, AuthenticationFailed, \
    PermissionDenied
from rest_framework.pagination import LimitOffsetPagination, \
    PageNumberPagination
from rest_framework.permissions import IsAuthenticated
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
from users.models import User
from .filters import IngredientFilter, RecipeFilter
from .paginator import CustomPagination
from .serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)


class IsAuthenticatedForSearch(permissions.BasePermission):
    """
    Пользовательский фильтр, требующий аутентификацию для запросов на поиск.
    """

    def has_permission(self, request, view):
        return (
                not request.query_params.get('name') or
                (request.user and request.user.is_authenticated)
        )


class IsAuthenticatedForWrite(permissions.BasePermission):
    """
    Пользовательский фильтр, требующий аутентификацию для записи данных.
    """

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user and request.user.is_authenticated


class IngredientsViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all().order_by('pk')
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)

    # permission_classes = [IsAuthenticatedForSearch]

    def list(self, request, *args, **kwargs):
        name_starts_with = request.query_params.get('name', '')
        queryset = self.queryset
        if name_starts_with:
            queryset = queryset.filter(name__istartswith=name_starts_with)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response(
            {'error': 'Method Not Allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {'error': 'Method Not Allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Method Not Allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


# Решение теста get_recipes_list // No Auth и не только
# Надо настроить по ТЗ
# class CustomPagination(PageNumberPagination):
#     limit = 6  # Количество объектов на странице
#     page_size_query_param = 'page_size'
#     max_page_size = 6  # Максимальное количество объектов на странице


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedForWrite]
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination # Решение теста
                                        # get_recipes_list // No Auth
                                        # и не только

    def get_queryset(self):                                         ########## 20042024 Vadim
        queryset = super().get_queryset()                           #
        author_id = self.request.query_params.get('author')         #
        tags = self.request.query_params.getlist('tags')            #
        if author_id:                                               #
            author = get_object_or_404(User, pk=author_id)          #
            queryset = queryset.filter(author=author)               #
        if tags:                                                    #
            for tag in tags:                                        #
                # print('!!!!!!!!!!!!! Tag = ', tag)                #
                queryset = queryset.filter(tags__slug=tag)          #
                # print('!!!!!!!!!!!!! queryset = ', queryset)      #
        # is_in_shopping_cart = self.request.query_params.get(
        #     'is_in_shopping_cart')
        # if is_in_shopping_cart and self.request.user.is_authenticated:
        #     queryset = queryset.filter(ShoppingCarts__user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    # НЕЛЬЗЯ переносить!
    # В Django REST Framework удаление объекта выполняется
    # через представление (view), а не через сериализатор.
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated:
            raise AuthenticationFailed(
                "Требуется аутентификация для удаления рецепта.")
        if instance.author != request.user:
            raise PermissionDenied(
                "Вы не являетесь автором этого рецепта.")
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        # recipe = self.get_object()    # здесь и в избранном повторяются
        try:                                                     ########## 20042024 Vadim
            recipe = Recipe.objects.get(pk=pk)                   #
        except Recipe.DoesNotExist:                              #
            if request.method == 'POST':
                return Response({'error': 'Рецепт не существует.'},  #
                                status=status.HTTP_400_BAD_REQUEST)  ########## 20042024 Vadim
            else:
                return Response({'error': 'Рецепт не существует.'},  #
                                status=status.HTTP_404_NOT_FOUND)  ########## 20042024 Vadim

        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={
                    'user': request.user.id,
                    'recipe': pk
                }
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            try:
                shopping_cart_item = ShoppingCart.objects.get(
                    user=request.user,
                    recipe=recipe
                )
                shopping_cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ShoppingCart.DoesNotExist:
                return Response(
                    {'error': 'Рецепт не найден в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST)

    def generate_shopping_list(self, user):
        recipes = ShoppingCart.objects.filter(
            user=user
        ).values_list('recipe', flat=True)

        # Собираем все ингредиенты из выбранных рецептов
        ingredients = {}
        for recipe in recipes:
            print(recipe)
            recipe_ingredients = RecipeIngredient.objects.filter(
                recipe=recipe
            )
            for recipe_ingredient in recipe_ingredients:
                ingredient_name = recipe_ingredient.ingredient.name
                if ingredient_name not in ingredients:
                    ingredients[ingredient_name] = {
                        'amount': recipe_ingredient.amount,
                        'measurement_unit': (recipe_ingredient.ingredient.
                                             measurement_unit)
                    }
                else:
                    ingredients[ingredient_name]['amount'
                    ] += recipe_ingredient.amount

        return ingredients

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
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
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            try:                                                     ########## 21042024 Vadim
                recipe = Recipe.objects.get(pk=pk)                   #
            except Recipe.DoesNotExist:                              #
                return Response({'error': 'Рецепт не существует.'},  #
                                status=status.HTTP_400_BAD_REQUEST)  ########## 21042024 Vadim

            serializer = FavoriteSerializer(
                data={'user': request.user.id, 'recipe': pk}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            try:                                                   ########## 21042024 Vadim
                recipe = Recipe.objects.get(pk=pk)                     #
            except Recipe.DoesNotExist:                                #
                return Response({'error': 'Рецепт не существует.'},  #
                                status=status.HTTP_404_NOT_FOUND)  ########## 21042024 Vadim
            try:
                shopping_cart_item = Favorite.objects.get(
                    user=request.user,
                    recipe=recipe
                )
                shopping_cart_item.delete()
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )
            except Favorite.DoesNotExist:
                return Response(
                    {'error': 'Рецепт не найден в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {
            "id": representation['id'],
            "name": representation['name'],
            "color": representation['color'],
            "slug": representation['slug'],
        }

    # @action(
    #     detail=True,
    #     methods=['post', 'delete'],
    #     url_path='shopping_cart',
    #     permission_classes=[IsAuthenticated]
    # )
    # def shopping_cart(self, request, pk=None):
    #     recipe = get_object_or_404(Recipe, pk=pk)
    #
    #     if request.method == 'POST':
    #         serializer = ShoppingCartSerializer(
    #             data={'user': request.user.id, 'recipe': recipe.id})
    #         if serializer.is_valid():
    #             serializer.save()
    #             return Response(serializer.data,
    #                             status=status.HTTP_201_CREATED)
    #         return Response(serializer.errors,
    #                         status=status.HTTP_400_BAD_REQUEST)
    #     elif request.method == 'DELETE':
    #         shopping_cart_exists = ShoppingCart.objects.filter(
    #             user=request.user, recipe=recipe).exists()
    #
    #         if shopping_cart_exists:
    #             ShoppingCart.objects.filter(user=request.user,
    #                                         recipe=recipe).delete()
    #             return Response(status=status.HTTP_204_NO_CONTENT)
    #         else:
    #             return Response(
    #                 {'error': 'Рецепт не найден в списке покупок.'},
    #                 status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
