from rest_framework.permissions import BasePermission
from .utils import has_permission


class HasUserPermission(BasePermission):

    def has_permission(self, request, view):

        required_permission = getattr(view, "required_permission", None)

        # If view does not require permission
        if not required_permission:
            return True

        # Check user permission
        return has_permission(request.user, required_permission)