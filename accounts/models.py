from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    # 自訂欄位
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, blank=True)
    # 重新定義 groups 與 user_permissions，加 related_name
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # 避免與 auth.User.groups 衝突
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # 避免與 auth.User.user_permissions 衝突
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
