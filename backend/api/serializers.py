from django.contrib.auth import get_user_model
from django.db.models import F
from djoser.serializers import UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework import status

from recipes.models import (
    FavoriteRecipe, IngredientInRecipe, Ingredient,
    Recipe, Follow, Tag, ShopingCart
)
User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор для пользовательской модели."""
    username = serializers.CharField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        if not (request and request.user.is_authenticated):
            return None
        return (
                Follow.objects
                .filter(author_id=obj.id, user=user)
                .exists()
            )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientInRecipe."""

    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Краткий вариант сериализатора c рецептами."""
    image = Base64ImageField(
        required=False, allow_null=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = ('name', 'image', 'cooking_time',)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta(RecipeMinifiedSerializer.Meta):
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'text',
        ) + RecipeMinifiedSerializer.Meta.fields

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id', 'name', 'measurement_unit',
            amount=F('ingredient_inrecipe__amount')
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and FavoriteRecipe.objects.filter(
                recipe_id=obj.id,
                user=request.user
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (
                ShopingCart.objects.filter(
                    recipe_id=obj.id,
                    user=request.user
                ).exists()
            )
        return False


class RecipeAddSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = IngredientInRecipesSerializer(
        source='ingredientin_recipe', many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'image', 'name', 'text', 'cooking_time',
        )

    def validate_cooking_time(self, data):
        cooking_time = data

        if cooking_time is None or cooking_time < 1:
            raise serializers.ValidationError('Время приготовления должно быть'
                                              ' не меньше одной минуты')
        if cooking_time > 1440:
            raise serializers.ValidationError('Время приготовления не должно'
                                              ' превышать 1440 минут')
        return data

    def validate_tags(self, data):
        """
        Проверяет, выбраны ли хотя бы один тег и отсутствуют
        повторяющиеся теги.
        """
        tags = data

        if tags is None or len(tags) == 0:
            raise serializers.ValidationError('Выберите хотя бы 1 тег.')

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться.')

        return data

    def validate_ingredients(self, data):
        """Проверяет выбор хотя бы одного ингредиента и их количество."""
        ingredients = self.initial_data.get('ingredients')

        if len(ingredients) == 0:
            raise serializers.ValidationError(
                'Выберите хотя бы 1 ингредиент из списка.')

        ingredients_id = []
        for ingredient in ingredients:
            if ingredient.get('id') in ingredients_id:
                raise serializers.ValidationError(
                    'Ингредиенты не могут повторяться. Проверьте свой рецепт.')
            if ingredient.get('amount') in (None, 0):
                raise serializers.ValidationError(
                    'Количество ингредиента обязательно для заполнения.'
                    ' Минимальное значение 1.'
                )

            ingredients_id.append(ingredient.get('id'))

        return data

    def create(self, validated_data):
        """Создание нового рецепта."""
        author = self.context.get('request').user
        text_recipe = validated_data.get('text')

        if Recipe.objects.filter(
            author=author,
            text=text_recipe
        ).exists():
            raise serializers.ValidationError(
                'У Вас уже есть рецепт с таким же описанием. '
                'Проверьте свой рецепт.',
                code=status.HTTP_400_BAD_REQUEST,
            )

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientin_recipe')

        if 'instance' in validated_data:
            recipe = validated_data['instance']
            recipe.tags.set(tags)
        else:
            recipe = Recipe.objects.create(author=author, **validated_data)
            recipe.tags.set(tags)

        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                amount=ingredient.get('amount'),
                ingredient=Ingredient.objects.get(
                    id=ingredient.get('id')
                ),
            ) for ingredient in ingredients
        ])

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        author = self.context.get('request').user

        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)

        new_text = validated_data.get('text', instance.text)

        if new_text != instance.text:
            if (Recipe.objects.filter(author=author,
               text=new_text).exclude(id=instance.id).exists()):
                raise serializers.ValidationError(
                    'У Вас уже есть рецепт с таким же описанием. '
                    'Проверьте свой рецепт.'
                )
            instance.text = new_text

        old_ingredients = IngredientInRecipe.objects.filter(recipe=instance)
        old_ingredients.delete()

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientin_recipe')

        instance.tags.set(tags)

        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=instance,
                amount=ingredient.get('amount'),
                ingredient=Ingredient.objects.get(
                    id=ingredient.get('id')
                ),
            ) for ingredient in ingredients
        ])

        instance.save()
        return instance

    def to_representation(self, instance):
        """Переопределение Response-ответа."""
        context = {'request': self.context.get('request')}
        serializer = RecipeSerializer(
            instance=instance,
            context=context
        )
        return serializer.data


class FollowSerializer(CustomUserSerializer):
    """Сериализатор подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (
            CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count',)
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        """Проверяет подписки пользователя."""
        user = self.context.get('request').user
        author = self.instance
        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на '
                                              'самого себя.')
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(f'Вы уже подписаны на {author}.')
        return data

    def get_recipes(self, obj):
        """
        Функция выдаёт список рецептов автора,
        на которого подписан пользователь.
        В каждом списке хранится id, name, image, cooking_time.
        """
        limit = self.context.get('request')._request.GET.get('recipes_limit')
        recipes_data = Recipe.objects.filter(
            author=obj.id
        )
        if limit:
            recipes_data = recipes_data[:int(limit)]

        serializer = RecipeMinifiedSerializer(
            data=recipes_data,
            many=True
        )
        serializer.is_valid()
        return serializer.data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов у избранного автора."""
        return obj.recipe.count()
