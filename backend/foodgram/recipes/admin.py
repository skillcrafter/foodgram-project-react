from django.contrib import admin
from recipes.models import Recipe, Ingredient, Tag, \
    RecipeIngredient, Favorite, ShoppingCart


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug',)
    search_fields = ('name', 'slug',)
    list_display_links = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    list_filter = ('name',)
    list_display_links = ('name',)


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through  # Ingredient
    extra = 0


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    readonly_fields = ('ingredient_measurement_unit',)

    def ingredient_measurement_unit(self, instance):
        return instance.ingredient.measurement_unit

    ingredient_measurement_unit.short_description = 'Единица измерения'


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags',)
    list_display_links = ('name',)
    inlines = [
        RecipeIngredientInline, ]
    filter_vertical = ('tags',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('user',)
    list_filter = ('user',)
    list_display_links = ('user',)


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('user',)
    list_filter = ('user',)
    list_display_links = ('user',)


"""Регистрируем кастомное представление админ-зоны"""
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
