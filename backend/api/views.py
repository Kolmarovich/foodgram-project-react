from api.permissions import AdminOrAuthorPermission
from rest_framework import viewsets, filters
from recipes.models import Favorite, Ingredient, RecipeIngredient,  Recipe, ShoppingCart, Tag
from api.serializers import FavoriteSerializer, IngredientSerializer, RecipeIngredientSerializer, RecipeSerializer, ShoppingCartSerializer, TagSerializer, RecipeListSerializer
from users.models import User
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import exceptions, status, viewsets
from users.serializers import RecipeMinifiedSerializer
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from .filters import RecipeFilter
from django_filters.rest_framework import DjangoFilterBackend


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингоедиента."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецепта."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AdminOrAuthorPermission,)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeSerializer
        else:
            return RecipeListSerializer

    @action(detail=True, methods=('post', 'delete'))
    def favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if self.request.method == 'POST':
            if Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError('Рецепт уже в избранном.')
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            if not Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError(
                    'Рецепта нет в избранном, либо он уже удален.'
                )
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=('post', 'delete'))
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if self.request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError(
                    'Рецепт уже в списке покупок.'
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError(
                    'Рецепта нет в списке покупок, либо он уже удален.'
                )
            shopping_cart = get_object_or_404(
                ShoppingCart,
                user=user,
                recipe=recipe
            )
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
       detail=False,
       methods=('get',)
    )
    def download_shopping_cart(self, request):
        user_shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        cart_recipes = [item.recipe.id for item in user_shopping_cart]
        ingredients_list = RecipeIngredient.objects.filter(
            recipe__in=cart_recipes
        ).values(
            'ingredient'
        ).annotate(
            total_amount=Sum('amount')
        )
        response = HttpResponse(content_type="text/plain")
        response['Content-Disposition'] = (
           'attachment; filename=shopping-list.txt'
        )
        response.write('Список покупок с сайта Foodgram:\n\n')
        for ingredient_info in ingredients_list:
            ingredient = Ingredient.objects.get(pk=ingredient_info['ingredient'])
            amount = ingredient_info['total_amount']
            response.write(
               f'{ingredient.name} - {amount} {ingredient.measurement_unit},\n'
            )
        return response

