from django.contrib import admin
from .models import Permission, UserPermissionMapping
from .models import Employee


admin.site.register(Permission)
admin.site.register(UserPermissionMapping)
admin.site.register(Employee)