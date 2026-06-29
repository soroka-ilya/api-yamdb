from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Разрешение только для администраторов или суперпользователей."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
        )


class IsAdminOrReadOnly(BasePermission):
    """Разрешение на чтение для всех, на изменение — только для админов."""

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or (
                request.user.is_authenticated
                and request.user.is_admin
            )
        )


class IsAuthorModeratorAdminOrReadOnly(BasePermission):
    """
    Разрешение на чтение для всех.

    Редактирование разрешено только автору объекта, модератору или админу.
    """

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (
                request.user.is_authenticated
                and (
                    obj.author == request.user
                    or request.user.is_moderator
                    or request.user.is_admin
                )
            )
        )


class IsAuthorModeratorAdmin(BasePermission):
    """Разрешение только для автора, модератора или администратора."""

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (
                request.user.is_authenticated
                and (
                    request.user == obj.author
                    or request.user.is_moderator
                    or request.user.is_admin
                )
            )
        )
