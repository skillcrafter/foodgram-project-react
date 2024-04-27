from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound


def get_object_or_400(model, *args, **kwargs):
    try:
        return get_object_or_404(model, *args, **kwargs)
    except model.DoesNotExist:
        raise NotFound(detail="Object not found", code=400)
