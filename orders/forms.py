from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'email', 'address']  # Fields to capture during checkout
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Add any custom validation for the email if necessary
        return email


class PaymentForm(forms.Form):
    """Form for selecting payment method during checkout."""
    PAYMENT_METHOD_CHOICES = [
        ("MPesa", "MPesa"),
        ("Credit Card", "Credit Card"),
        ("PayPal", "PayPal"),
    ]

    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, required=True)
