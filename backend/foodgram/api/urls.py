from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientsViewSet,
                    RecipesViewSet,
                    TagViewSet,
                    UserViewSet,
                    )

api_v1 = DefaultRouter()
api_v1.register(r'ingredients', IngredientsViewSet, basename='ingredients')
api_v1.register(r'tags', TagViewSet, basename='tags')
api_v1.register(r'recipes', RecipesViewSet, basename='recipes')
api_v1.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
