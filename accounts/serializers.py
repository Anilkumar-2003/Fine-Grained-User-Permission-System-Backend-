from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Permission, UserPermissionMapping, Employee


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):

        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        user = authenticate(username=user.username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        data["user"] = user
        return data


class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = "__all__"


class AssignPermissionSerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    permission_ids = serializers.ListField(
        child=serializers.IntegerField()
    )


class EmployeeSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = Employee
        fields = [
            "emp_id",
            "username",
            "email",
            "department",
            "designation",
            "created_at"
        ]

    def update(self, instance, validated_data):

        user_data = validated_data.pop("user", None)

        if user_data:
            user = instance.user

            new_username = user_data.get("username", user.username)
            new_email = user_data.get("email", user.email)

            # Check username uniqueness
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                raise serializers.ValidationError({
                    "username": "Username already exists"
                })

            # Check email uniqueness
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                raise serializers.ValidationError({
                    "email": "Email already exists"
                })

            user.username = new_username
            user.email = new_email
            user.save()

        instance.department = validated_data.get("department", instance.department)
        instance.designation = validated_data.get("designation", instance.designation)

        instance.save()

        return instance


class EmployeeCreateSerializer(serializers.Serializer):

    username = serializers.CharField(required=False)
    email = serializers.EmailField()
    password = serializers.CharField()

    department = serializers.CharField()
    designation = serializers.CharField()

    def validate(self, data):

        email = data.get("email")

        existing_user = User.objects.filter(email=email).first()

        # Email exists and active
        if existing_user and existing_user.is_active:
            raise serializers.ValidationError({
                "email": "User with this email already exists"
            })

        return data

    def create(self, validated_data):

        email = validated_data["email"]
        password = validated_data["password"]
        department = validated_data["department"]
        designation = validated_data["designation"]

        existing_user = User.objects.filter(email=email).first()

        # Auto-generate username from email
        username = email.split("@")[0]

        # reactivate inactive user
        if existing_user and not existing_user.is_active:

            existing_user.username = username
            existing_user.set_password(password)
            existing_user.is_active = True
            existing_user.save()

            employee, created = Employee.objects.get_or_create(
                user=existing_user,
                defaults={
                    "department": department,
                    "designation": designation
                }
            )

            if not created:
                employee.department = department
                employee.designation = designation
                employee.save()

            return employee

        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        employee = Employee.objects.create(
            user=user,
            department=department,
            designation=designation
        )

        return employee
    
class UserPermissionDetailSerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    
class UserEmailSerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    email = serializers.EmailField()