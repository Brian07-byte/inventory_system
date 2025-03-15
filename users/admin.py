from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        ("User Info", {"fields": ("username", "email", "password", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        ("Create User", {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role"),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
