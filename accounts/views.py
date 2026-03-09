from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    LoginSerializer,
    PermissionSerializer,
    AssignPermissionSerializer,
    EmployeeSerializer,
    EmployeeCreateSerializer
)

from .models import Permission, UserPermissionMapping, Employee

from rest_framework.permissions import IsAuthenticated
from .permissions import HasUserPermission

from django.core.paginator import Paginator
from django.db.models import Q

from django.contrib.auth.models import User

from django.db.models import Count

#LOGIN
class LoginView(APIView):

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            return Response({
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            })

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


# PERMISSION LIST 

class PermissionListView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]

    required_permission = "ASSIGN_PERMISSION"

    def get(self, request):

        permissions = Permission.objects.all()

        serializer = PermissionSerializer(permissions, many=True)

        return Response(serializer.data)


#ASSIGN PERMISSION
class AssignPermissionView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]
    required_permission = "ASSIGN_PERMISSION"

    def post(self, request):

        serializer = AssignPermissionSerializer(data=request.data)

        if serializer.is_valid():

            user_id = serializer.validated_data["user_id"]
            permission_ids = serializer.validated_data["permission_ids"]

            # Validate permission per ids
            valid_permissions = Permission.objects.filter(id__in=permission_ids)

            if valid_permissions.count() != len(permission_ids):
                return Response({
                    "message": "Invalid permission id provided"
                }, status=400)

            # removing the old permissions
            UserPermissionMapping.objects.filter(user_id=user_id).delete()

            # assigning the new permissions to the user
            for pid in permission_ids:
                UserPermissionMapping.objects.create(
                    user_id=user_id,
                    permission_id=pid
                )

            return Response({
                "message": "Permissions assigned successfully"
            })

        return Response({
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=400)

#EMPLOYEE LIST 

class EmployeeListView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]

    required_permission = "VIEW_EMPLOYEE"

    def get(self, request):

        page = int(request.GET.get("page", 0))
        size = int(request.GET.get("size", 10))
        sort_by = request.GET.get("sortBy", "id")
        sort_order = request.GET.get("sortOrder", "ASC")

        search = request.GET.get("search")
        department = request.GET.get("department")
        designation = request.GET.get("designation")

        employees = Employee.objects.filter(user__is_active=True)

        #Search
        if search:
            employees = employees.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search)
            )

        #Filters
        if department:
            employees = employees.filter(department__icontains=department)

        if designation:
            employees = employees.filter(designation__icontains=designation)

        #Sorting
        allowed_sort_fields = [
            "id",
            "department",
            "designation",
            "created_at",
            "user__username",
            "user__email"
        ]

        if sort_by not in allowed_sort_fields:
            sort_by = "id"

        if sort_order.upper() == "DESC":
            sort_by = f"-{sort_by}"

        employees = employees.order_by(sort_by)

        paginator = Paginator(employees, size)
        page_obj = paginator.get_page(page + 1)

        serializer = EmployeeSerializer(page_obj.object_list, many=True)

        headers = [
            {"key": "emp_id", "label": "Employee ID"},
            {"key": "username", "label": "Username"},
            {"key": "email", "label": "Email"},
            {"key": "department", "label": "Department"},
            {"key": "designation", "label": "Designation"},
            {"key": "created_at", "label": "Created At"}
        ]

        return Response({
            "headers": headers,
            "page": page,
            "size": size,
            "total_pages": paginator.num_pages,
            "total_records": paginator.count,
            "data": serializer.data
        })


# CREATE EMPLOYEE
class CreateEmployeeView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]
    required_permission = "CREATE_EMPLOYEE"

    def post(self, request):

        serializer = EmployeeCreateSerializer(data=request.data)

        try:

            if serializer.is_valid():
                serializer.save()

                return Response(
                    {"message": "Employee created successfully"},
                    status=201
                )

            return Response(
                {
                    "message": "Validation failed",
                    "errors": serializer.errors
                },
                status=400
            )

        except ValueError as e:
            return Response(
                {"message": str(e)},
                status=400
            )

        except Exception:
            return Response(
                {"message": "Unexpected server error"},
                status=500
            )
            
#UPDATE EMPLOYEE

class UpdateEmployeeView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]

    required_permission = "EDIT_EMPLOYEE"

    def put(self, request, pk):

        try:
            employee = Employee.objects.get(id=pk)
        except Employee.DoesNotExist:
            return Response({
                "message": "Employee not found"
            }, status=404)

        serializer = EmployeeSerializer(employee, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message": "Employee updated successfully",
                "data": serializer.data
            })

        return Response({
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=400)


# DELETE EMPLOYEE
class DeleteEmployeeView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]

    required_permission = "DELETE_EMPLOYEE"

    def delete(self, request, pk):

        try:
            employee = Employee.objects.get(id=pk)
        except Employee.DoesNotExist:
            return Response({
                "message": "Employee not found"
            }, status=404)

        user = employee.user
        user.is_active = False
        user.save()

        return Response({
            "message": "Employee deactivated successfully"
        })
   
class MyPermissionsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user_id = request.GET.get("user_id")

        if not user_id:
            return Response(
                {"message": "user_id is required"},
                status=400
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=404
            )

        # employee details
        employee = Employee.objects.filter(user=user).first()

        # permissions
        user_permissions = UserPermissionMapping.objects.filter(user=user)

        permissions_list = []

        for perm in user_permissions:
            permissions_list.append({
                "id": perm.permission.id,
                "code": perm.permission.code,
                "name": perm.permission.name
            })

        return Response({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "emp_id": employee.emp_id if employee else None,
            "department": employee.department if employee else None,
            "designation": employee.designation if employee else None,
            "permissions": permissions_list
        })
        
#GET EMPLOYEE DETAILS 
class EmployeeDetailsView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]

    required_permission = "EDIT_EMPLOYEE"

    def get(self, request):

        email = request.GET.get("email")

        if not email:
            return Response(
                {"message": "email is required"},
                status=400
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=404
            )

        employee = Employee.objects.filter(user=user).first()

        permissions = UserPermissionMapping.objects.filter(user=user)

        permission_list = []

        for perm in permissions:
            permission_list.append({
                "id": perm.permission.id,
                "code": perm.permission.code,
                "name": perm.permission.name
            })

        return Response({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "emp_id": employee.emp_id if employee else None,
            "department": employee.department if employee else None,
            "designation": employee.designation if employee else None,
            "permissions": permission_list
        })
            
# USER list with ID + EMAIL

class UserEmailListView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]

    required_permission = "ASSIGN_PERMISSION"

    def get(self, request):

        users = User.objects.filter(is_active=True)

        user_list = []

        for user in users:
            user_list.append({
                "user_id": user.id,
                "email": user.email
            })

        return Response(user_list)
    
#DASHBOARD SUMMARY

class SummaryView(APIView):

    permission_classes = [IsAuthenticated, HasUserPermission]

    required_permission = "ASSIGN_PERMISSION"

    def get(self, request):

        try:

            # total employees
            total_employees = Employee.objects.filter(user__is_active=True).count()

            # total permission types
            total_permissions = Permission.objects.count()

            # employees who have permissions
            employees_with_permissions = (
                UserPermissionMapping.objects
                .values("user")
                .distinct()
                .count()
            )

            # permission distribution
            permission_distribution = (
                UserPermissionMapping.objects
                .values(
                    "permission__code",
                    "permission__name"
                )
                .annotate(user_count=Count("user"))
                .order_by("permission__code")
            )

            permission_chart = []

            for p in permission_distribution:
                permission_chart.append({
                    "permission_code": p["permission__code"],
                    "permission_name": p["permission__name"],
                    "users": p["user_count"]
                })

            return Response({
                "total_employees": total_employees,
                "total_permissions": total_permissions,
                "employees_with_permissions": employees_with_permissions,
                "permission_distribution": permission_chart
            })

        except Exception:
            return Response(
                {"message": "Unable to fetch summary"},
                status=500
            )