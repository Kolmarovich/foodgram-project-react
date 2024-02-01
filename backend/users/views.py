from rest_framework import permissions, status, viewsets
from users.serializers import FollowSerializer, UserSerializer
from users.models import User, Follow
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


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
        author = User.objects.get(id=pk)
        if request.method == 'POST':
            Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Follow.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Просмотр подписок."""
        user = request.user
        print(user)
        user_following = User.objects.filter(following__user=user)
        page = self.paginate_queryset(user_following)
        serializer = UserSerializer(page,
                                    context={'request': request},
                                    many=True)
        return self.get_paginated_response(serializer.data)


