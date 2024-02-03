from rest_framework import serializers
from users.models import Follow, User
from recipes.models import Recipe
from djoser.serializers import UserCreateSerializer
from rest_framework.validators import UniqueTogetherValidator


class UserSerializer(UserCreateSerializer):
    """Сериалайзер пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password"
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and not request.user.is_anonymous:
            user = request.user
            return Follow.objects.filter(user=user, author=obj).exists()
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if (self.context.get('view')
           and hasattr(self.context.get('view'), 'action')):
            if self.context.get('view').action == 'create':
                representation.pop("is_subscribed", None)
        return representation


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериалайзер короткого рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'id', 'username', 'first_name',
                            'last_name', 'is_subscribed', 'recipes',
                            'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', 2
        )
        recipes_limit = int(recipes_limit)
        recipes = Recipe.objects.filter(author=obj)[:recipes_limit]
        serializer = RecipeMinifiedSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

