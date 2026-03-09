from django.db import models, transaction
from django.contrib.auth.models import User


class Permission(models.Model):

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.code


class UserPermissionMapping(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.permission.code}"

class Employee(models.Model):

    emp_id = models.CharField(
        max_length=10,   # allow future growth
        unique=True,
        blank=True,
        null=True,
        editable=False
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.emp_id:

            with transaction.atomic():

                last_employee = (
                    Employee.objects
                    .select_for_update()
                    .exclude(emp_id=None)
                    .order_by("-emp_id")
                    .first()
                )

                if last_employee:
                    new_id = int(last_employee.emp_id) + 1
                else:
                    new_id = 1

                # Pad only if less than 4 digits
                if new_id < 10000:
                    self.emp_id = str(new_id).zfill(4)
                else:
                    self.emp_id = str(new_id)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.emp_id} - {self.user.username}"