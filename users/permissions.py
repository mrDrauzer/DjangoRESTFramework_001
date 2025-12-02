from rest_framework.permissions import BasePermission, SAFE_METHODS


MODERATORS_GROUP = 'moderators'


def is_moderator(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=MODERATORS_GROUP).exists()


class IsModer(BasePermission):
    """Доступ только для пользователей из группы модераторов."""

    def has_permission(self, request, view):
        return is_moderator(request.user)


class IsOwner(BasePermission):
    """Доступ только владельцу объекта (ожидается поле owner)."""

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, 'owner', None)
        return owner == request.user


class IsSelfOrReadOnly(BasePermission):
    """Пользователь может редактировать только свой профиль; читать могут все авторизованные."""

    def has_permission(self, request, view):
        # Доступ к чтению (list/retrieve) оставляем авторизованным всегда
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Разрешаем изменять только собственный профиль
        return getattr(obj, 'pk', None) == getattr(request.user, 'pk', None)
