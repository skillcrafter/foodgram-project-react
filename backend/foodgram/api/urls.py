from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientsViewSet,
                       RecipesViewSet,
                       TagViewSet,
                       )
from users.views import UserViewSet

api_v1 = DefaultRouter()
api_v1.register(r'ingredients', IngredientsViewSet, basename='ingredients')
api_v1.register(r'tags', TagViewSet, basename='tags')
api_v1.register(r'recipes', RecipesViewSet, basename='recipes')
api_v1.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('auth/', include('djoser.urls')),   # !!! Может быть избыточной
    # надо позже проверить - удалить и посмотреть хватит ли нижней
    path('auth/', include('djoser.urls.authtoken')),
]
