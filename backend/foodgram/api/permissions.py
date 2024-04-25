from rest_framework import permissions


class IsAuthenticatedForWrite(permissions.BasePermission):
    """
    Пользовательский фильтр, требующий аутентификацию для записи данных.
    """

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user and request.user.is_authenticated
