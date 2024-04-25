from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, AuthenticationFailed, \
    PermissionDenied
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
from .filters import RecipeFilter
from .paginator import CustomPagination
from .permissions import IsAuthenticatedForWrite
from .serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)


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
    permission_classes = (IsAuthenticatedForWrite,)
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
            author = get_object_or_404(User, pk=author_id)
            queryset = queryset.filter(author=author)
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__slug=tag)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

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
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        try:
            recipe = Recipe.objects.get(pk=pk)  #
        except Recipe.DoesNotExist:  #
            if request.method == 'POST':
                return Response({'error': 'Рецепт не существует.'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Рецепт не существует.'},
                                status=status.HTTP_404_NOT_FOUND)

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
                    ingredients[ingredient_name]['amount']\
                        += recipe_ingredient.amount

        return ingredients

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
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
        if request.method == 'POST':
            try:
                recipe = Recipe.objects.get(pk=pk)
            except Recipe.DoesNotExist:
                return Response({'error': 'Рецепт не существует.'},
                                status=status.HTTP_400_BAD_REQUEST)

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
            try:
                recipe = Recipe.objects.get(pk=pk)
            except Recipe.DoesNotExist:
                return Response({'error': 'Рецепт не существует.'},
                                status=status.HTTP_404_NOT_FOUND)
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


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
