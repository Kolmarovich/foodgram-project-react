from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from .models import (
    Tag, Ingredient, Recipe, FavoriteRecipe,
    Follow, ShopingCart, IngredientInRecipe
)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInRecipeInline,)
    filter_horizontal = ['tags']

    def response_add(self, request, obj, post_url_continue=None):
        if not obj.ingredients.exists():
            self.message_user(
                request,
                "Необходимо добавить хотя бы один ингредиент.",
                level='ERROR')
            return HttpResponseRedirect(request.path)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if not obj.ingredients.exists():
            self.message_user(
                request,
                "Необходимо добавить хотя бы один ингредиент.",
                level='ERROR')
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

    def clean(self):
        ingredients = self.cleaned_data.get('ingredients')
        if not ingredients.exists():
            raise forms.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.')

        return super().clean()


admin.site.register(Tag)
admin.site.register(FavoriteRecipe)
admin.site.register(Follow)
admin.site.register(ShopingCart)
admin.site.register(IngredientInRecipe)
admin.site.register(Ingredient)
