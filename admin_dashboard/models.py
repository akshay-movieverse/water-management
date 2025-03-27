from django.db import models

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SubRecunitManager(SoftDeleteManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False,unit__is_deleted=False)  # Ensure related Unit is not deleted


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True

class Unit(SoftDeleteModel):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)

    objects = SoftDeleteManager()  # Use generic manager

    def __str__(self):
        return self.name

class Subunit(SoftDeleteModel):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    objects = SubRecunitManager()  # Use generic manager
    def __str__(self):
        return self.name

class RechargeUnit(SoftDeleteModel):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="recharge_units")
    name = models.CharField(max_length=255)
    objects = SubRecunitManager()  # Use generic manager
    def __str__(self):
        return self.name
    
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.models import AbstractUser, Group, Permission

from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    

class CustomUser(AbstractUser, SoftDeleteModel):
    is_admin = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    
    email = models.EmailField(unique=True, blank=True, null=True)  # Optional Email
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Optional Phone Number
    unit = models.OneToOneField('Unit', null=True, blank=True, on_delete=models.SET_NULL)  # Assigned Unit for Manager

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",  # Unique related_name to prevent conflicts
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions_set",  # Unique related_name to prevent conflicts
        blank=True
    )

    objects = CustomUserManager()  # Use the custom manager
    
    def save(self, *args, **kwargs):
        # Ensure a user cannot be both admin and manager
        if self.is_admin and self.is_manager:
            raise ValueError("User cannot be both Admin and Manager.")
        super().save(*args, **kwargs)


class ReportGeneration(models.Model):
    manager = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    date = models.DateField()
    generated_at = models.DateTimeField(auto_now=True)  # Updates on every save

    def __str__(self):
        return f"Report by {self.manager.username} on {self.date}"

class ResetHistory(models.Model):
    ACTION_CHOICES = (
        ('subunit_reset', 'Subunit Reset'),
        ('recharge_fill', 'Recharge Fill'),
        ('subunit_reset_plus', 'Subunit Reset+'),
        ('recharge_fill_plus', 'Recharge Fill+'),
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField()
    is_undo = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.get_action_type_display()} - {self.date}"