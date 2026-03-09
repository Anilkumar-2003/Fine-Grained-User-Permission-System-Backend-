from django.urls import path
from .views import LoginView, PermissionListView, AssignPermissionView
from .views import (
    EmployeeListView,
    CreateEmployeeView,
    UpdateEmployeeView,
    DeleteEmployeeView,
    MyPermissionsView,
    EmployeeDetailsView,
    UserEmailListView,
    SummaryView
)

urlpatterns = [

    path("login/", LoginView.as_view(), name="login"),

    path("permissions/", PermissionListView.as_view()),

    path("assign-permissions/", AssignPermissionView.as_view()),

    path("accounts_employee/getAll", EmployeeListView.as_view()),

    path("employees/create/", CreateEmployeeView.as_view()),

    path("employees/<int:pk>/update/", UpdateEmployeeView.as_view()),

    path("employees/<int:pk>/delete/", DeleteEmployeeView.as_view()),
    
    path("my-permissions/", MyPermissionsView.as_view()),
    
    path("employees/me/", EmployeeDetailsView.as_view()),
    
    path("users/", UserEmailListView.as_view()),
    
    path("summary/", SummaryView.as_view()),

]