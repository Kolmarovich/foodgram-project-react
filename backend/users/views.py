from rest_framework import permissions, status, viewsets, exceptions
from users.serializers import FollowSerializer, UserSerializer
from users.models import User, Follow
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_me_data(self, request):
        """Текущий пользователь"""
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка/отписка."""
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            if user == author:
                raise exceptions.ValidationError('Укажите другого автора.')
            if Follow.objects.filter(user=user, author=author).exists():
                raise exceptions.ValidationError('Подписка уже оформлена.')
            Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Follow.objects.filter(user=user, author=author).exists():
                raise exceptions.ValidationError('Вы не пописаны на автора.')
            subscription = get_object_or_404(Follow, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Просмотр подписок."""
        user = request.user
        print(user)
        user_following = User.objects.filter(following__user=user)
        page = self.paginate_queryset(user_following)
        serializer = UserSerializer(page, context={'request': request},
                                    many=True)
        return self.get_paginated_response(serializer.data)
