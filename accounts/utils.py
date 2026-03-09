from .models import UserPermissionMapping

def has_permission(user, permission_code):

    return UserPermissionMapping.objects.filter(
        user=user,
        permission__code=permission_code
    ).exists()
    