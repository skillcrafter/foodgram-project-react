from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny
)
from rest_framework.response import Response

from api.paginator import CustomPagination
from .models import Subscribe, User
from .serializers import (
    SubscribeSerializer,
    SubscriptionSerializer,
    UserSerializer
)
from djoser import views as djoser_views



class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для пользователей."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in (
                'subscribe',
                'subscriptions',
                'destroy',
                'me'):
            permission_classes = (IsAuthenticated,)
        else:
            permission_classes = (AllowAny,)
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        serializer_class=SubscribeSerializer
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        subscription = Subscribe.objects.filter(
            user=user,
            author=author
        )
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Вы не можете подписаться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription, created = Subscribe.objects.get_or_create(
                user=user,
                author=author
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not subscription.exists():
                return Response(
                    {'error': 'Вы не подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
