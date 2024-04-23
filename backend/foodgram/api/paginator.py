from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Кастомный класс пагинации."""

    page_size = 6
    page_size_query_param = 'limit'