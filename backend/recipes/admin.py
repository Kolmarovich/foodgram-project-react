from django.contrib import admin

from .models import (Favorite, Ingredient, RecipeIngredient,
                     Recipe, ShoppingCart, Tag)

admin.site.empty_value_display = 'Не задано'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    list_filter = ('name',)
    ordering = ('name',)
    search_fields = ('name',)
    list_display_links = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug',)
    list_filter = ('name', 'slug',)
    search_fields = ('name', 'slug',)
    ordering = ('name',)
    list_display_links = ('name',)


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'author', 'name', 'image', 'text',
        'cooking_time', 'pub_date',
    )
    list_filter = ('author', 'name', 'tags')
    ordering = ('-pub_date',)
    readonly_fields = ('favorite_count', 'pub_date')
    inlines = (IngredientInline,)  # Правильное название атрибута
    search_fields = ('author__username',)  # Поле для поиска
    list_display_links = ('author',)  # Поле для ссылки в списке

    @admin.display(description='Количество добавлений в избранное')
    def favorite_count(self, recipe):
        return recipe.favorites_recipe.count()


admin.site.register(Favorite)
admin.site.register(ShoppingCart)