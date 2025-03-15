from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class UserRegistrationForm(UserCreationForm):
    """Form for registering new users with email, username, and role."""
    
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2", "role"]
