from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    """Custom user manager to handle user creation."""

    def create_user(self, username, email, password=None, role='customer'):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role)
        user.set_password(password)  # Hash password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        """Creates and returns a superuser."""
        user = self.create_user(username, email, password, role='admin')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractUser):
    """Custom user model with roles."""

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    ]
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    objects = CustomUserManager()  # Attach the custom manager

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def is_admin(self):
        return self.role == 'admin'

    def is_customer(self):
        return self.role == 'customer'

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
