from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    # Custom fields
    address = models.CharField(max_length=50, blank=True)
    # Redefine groups and user_permissions, add related_name
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # Avoid conflicts with auth.User.groups
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # Avoid conflicts with auth.User.user_permissions
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
