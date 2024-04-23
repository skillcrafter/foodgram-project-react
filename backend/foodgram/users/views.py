from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly, AllowAny
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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        # if self.action == 'me':               ########## 21042024
        #     return IsAuthenticated(),         # удалена секция с me
        if self.action in (                     # трансформирована в это
                'subscribe',
                'subscriptions',
                'destroy',
                'me'):
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
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
        permission_classes=(IsAuthenticated,),
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

    # ОГРОМНАЯ ВЕРОЯТНОСТЬ ЧТО НЕ НУЖЕН
    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(
    #         serializer.data,
    #         status=status.HTTP_201_CREATED,
    #         headers=headers
    #     )

    # def get_me(self, request):
    #     print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    #     serializer = self.get_serializer(request.user)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    #
    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     page = self.paginate_queryset(queryset)
    #     print('&&&&&&&&&&&&&&&&&&&&&&&&&&&')
    #     if page is not None:
    #         serializer = self.get_serializer(
    #             page, many=True
    #         )
    #         return self.get_paginated_response(serializer.data)
    #     serializer = self.get_serializer(
    #         queryset,
    #         many=True,
    #         context={'request': request}
    #     )
    #     return Response(serializer.data)
    #
    # def delete(self, request, *args, **kwargs):
    #     response = super().delete(request, *args, **kwargs)
    #     if response.status_code == status.HTTP_204_NO_CONTENT:
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     return Response(response.data, status=response.status_code)

    # def subscriptions(self, request):
    #     user = request.user
    #     subscriptions = Subscribe.objects.filter(user=user)
    #     serializer = SubscribeSerializer(
    #         subscriptions,
    #         many=True,
    #         context={'request': request}
    #     )
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    # @action(
    #     detail=True,
    #     methods=['post', 'delete'],
    #     permission_classes=(IsAuthenticated,)
    # )
    # def subscribe(self, request, id):
    #     print('!!!!!!!!!!!!!!!!!!!!id:', id)
    #     if request.method == 'POST':
    #         return self.create_subscription(request, id)
    #     return self.delete_subscription(request, id)
    #
    # def create_subscription(self, request, id):
    #     get_object_or_404(User, pk=id)
    #     print('id:', id)
    #     user = request.user
    #     print('user:', user)
    #     serializer = SubscribeSerializer(
    #         data={
    #             'user': user.id,
    #             'author': id
    #         },
    #         context={'request': request}
    #     )
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    #
    # def delete_subscription(self, request, id):
    #     user = request.user
    #     author = get_object_or_404(User, pk=id)
    #     delete_count, _ = user.follower.filter(author=author).delete()
    #     if not delete_count:
    #         return Response(
    #             {'detail': 'Подписка не найдена.'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
    #     return Response(status=status.HTTP_204_NO_CONTENT)
    ###################
